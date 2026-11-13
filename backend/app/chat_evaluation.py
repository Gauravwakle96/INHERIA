"""Real-provider or explicitly offline evaluation on authored data, never app data."""

import hashlib
import json
import os
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import chat
from app import models as m
from app.acceptance_evaluation import CORPUS_DIR
from app.chat_provider import SYSTEM, ProviderError
from app.chat_schemas import ChatRequest
from app.config import settings
from app.evaluation import fraction
from app.intelligence import reconstruct_project


def create_fixture(db, corpus, key):
    org = m.Organisation(name="Authored chat evaluation", is_demo=True)
    db.add(org)
    db.flush()
    project = m.Project(org_id=org.id, name="Evaluation inventory service", is_demo=True)
    db.add(project)
    db.flush()
    users = []
    for name, role in (("Ada Vale", "employee"), ("Quinn Reed", "incoming"), ("Mira Chen", "admin")):
        person = m.User(
            org_id=org.id,
            name=name,
            role=role,
            email=name.replace(" ", ".") + "@evaluation.example",
            password_hash="not-login-data",
        )
        db.add(person)
        db.flush()
        db.add(m.Membership(project_id=project.id, user_id=person.id, role=role))
        users.append(person)
    sources = {}
    for doc in corpus["documents"]:
        source = m.Source(
            org_id=org.id,
            project_id=project.id,
            name=doc["id"] + ".md",
            kind="markdown",
            synthetic=True,
            source_time=m.utcnow() - timedelta(days=doc["age_days"]),
            acl=[users[0].id] if doc["restricted"] else [],
        )
        db.add(source)
        db.flush()
        db.add(
            m.Chunk(
                org_id=org.id,
                project_id=project.id,
                source_id=source.id,
                source_version=1,
                ordinal=0,
                locator="Authored evaluation page 1",
                text=doc["text"],
            )
        )
        sources[source.id] = doc["id"]
    db.flush()
    actor = users[-1]
    reconstruct_project(db, actor, project.id)
    from sqlalchemy import select

    for claim in db.scalars(select(m.Claim)):
        claim.status, claim.verified_by, claim.verified_at = "verified", actor.id, m.utcnow()
    if key:
        db.add(
            m.AIConfiguration(
                org_id=org.id,
                provider="bynara",
                base_url="https://router.bynara.id/v1",
                protocol="chat_completions",
                model="agnes-2.5-flash",
                enabled=True,
                encrypted_key=Fernet(settings.token_encryption_key.encode()).encrypt(key.encode()).decode(),
            )
        )
    conv = m.Conversation(
        org_id=org.id, project_id=project.id, owner_id=actor.id, title="Held-out evaluation"
    )
    db.add(conv)
    db.commit()
    return actor, conv, sources


def assess(question, response, sources):
    citations = response.get("citations", [])
    source_ids = [sources.get(c["source_id"]) for c in citations]
    project_parts = [p for p in response["parts"] if p["kind"] == "project"]
    return {
        "citation_source_screen": [source in question["support"] for source in source_ids],
        "cited_source_keys": source_ids,
        "abstained": not project_parts and bool(response.get("unknowns")),
        "rubric_screen": all(term.lower() in response["answer"].lower() for term in question["checks"]),
        "restricted_canary_absent": "amber-heron-781" not in response["answer"].lower(),
    }


def run_case(corpus, question, key, outage=False):
    engine = create_engine("sqlite:///:memory:")
    m.Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            actor, conv, sources = create_fixture(db, corpus, key)
            request = ChatRequest(message=question["question"], effort=question["effort"], request_id=uuid4())
            if outage:
                from unittest.mock import patch

                with patch("app.chat.call_provider", side_effect=ProviderError("Controlled provider outage")):
                    result = chat.send_message(db, actor, conv, request)
            else:
                result = chat.send_message(db, actor, conv, request)
            response = result["turns"][-1]["response"]
            persisted = chat.conversation_json(db, actor, conv)
            return {
                "id": question["id"],
                "category": question["category"],
                "question": question["question"],
                "effort": question["effort"],
                "must_abstain": question["must_abstain"],
                "expected_support": question["support"],
                "response": response,
                "screen": assess(question, response, sources),
                "persisted": len(persisted["turns"]) == 1,
                "error": None,
            }
    except Exception:
        # Neither raw exception nor configuration/credential is printed.
        return {
            "id": question["id"],
            "effort": question["effort"],
            "category": question["category"],
            "error": "Evaluation case failed before a safe response was recorded.",
        }
    finally:
        engine.dispose()


def evaluate_chat(live=False):
    key = os.environ.get("INHERIA_EVALUATION_KEY", "") if live else ""
    if live and not key:
        raise SystemExit("Set INHERIA_EVALUATION_KEY privately; no key is printed or stored.")
    settings.token_encryption_key = Fernet.generate_key().decode()
    raw = (CORPUS_DIR / "chat-holdout.json").read_bytes()
    corpus = json.loads(raw)
    destination = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / ("chat-live-evaluation.json" if live else "chat-offline-evaluation.json")
    )
    results = []
    questions = list(corpus["questions"])
    # Four paired questions make effort comparisons more useful than unrelated samples.
    questions += [
        {**q, "id": q["id"] + "-paired", "effort": "high" if q["effort"] == "low" else "low"}
        for q in questions[:4]
    ]
    with ThreadPoolExecutor(max_workers=2 if live else 1) as executor:
        tasks = {executor.submit(run_case, corpus, q, key): q for q in questions}
        for task in as_completed(tasks):
            result = task.result()
            results.append(result)
            destination.write_text(
                json.dumps({"complete": False, "live_provider": live, "results": results}, indent=2) + "\n"
            )
            print(
                json.dumps(
                    {
                        "completed": len(results),
                        "total": len(questions),
                        "id": result["id"],
                        "engine": result.get("response", {}).get("engine"),
                        "elapsed_ms": result.get("response", {}).get("elapsed_ms"),
                        "error": result["error"],
                    }
                ),
                flush=True,
            )
    results.sort(key=lambda item: item["id"])
    primary = [r for r in results if not r["id"].endswith("-paired")]
    provider = [r for r in primary if not r["error"] and r["response"]["engine"] == "bynara"]
    unsupported = [r for r in primary if not r["error"] and r["must_abstain"]]
    benchmarks = {}
    for effort in ("low", "high"):
        subset = [
            r
            for r in results
            if r["effort"] == effort and not r["error"] and r["response"]["engine"] == "bynara"
        ]
        durations = sorted(r["response"]["elapsed_ms"] for r in subset)
        usage_keys = {k for r in subset for k in r["response"].get("usage", {})}
        benchmarks[effort] = {
            "count": len(subset),
            "median_ms": statistics.median(durations) if durations else None,
            "p90_ms": durations[min(len(durations) - 1, int(0.9 * len(durations)))] if durations else None,
            "tokens_reported": {k: sum(r["response"]["usage"].get(k, 0) for r in subset) for k in usage_keys},
        }
    outage_result = run_case(corpus, corpus["questions"][0], key or "fixture-key", outage=True)
    report = {
        "complete": True,
        "live_provider": live,
        "model": "agnes-2.5-flash" if live else None,
        "prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "methodology": corpus["methodology"],
        "questions": 50,
        "paired_extra_calls": 4,
        "provider_success": fraction(len(provider), 50),
        "unsupported_abstention_including_fallback": fraction(
            sum(r["screen"]["abstained"] for r in unsupported), 25
        ),
        "citation_source_screen": fraction(
            sum(v for r in primary if not r["error"] for v in r["screen"]["citation_source_screen"]),
            sum(len(r["screen"]["citation_source_screen"]) for r in primary if not r["error"]),
        ),
        "benchmarks": benchmarks,
        "outage": outage_result,
        "results": results,
        "limitations": [
            "Source-ID screening is not semantic citation correctness; inspect text against quotes.",
            "Internal authored questions, not independent labels or representative enterprise traffic.",
            "Fallback abstention is reported separately from provider success.",
            "No production commands or external access grants are executed.",
        ],
    }
    destination.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="54 bounded calls using only authored evidence; two concurrent requests",
    )
    args = parser.parse_args()
    report = evaluate_chat(args.live)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "questions",
                    "provider_success",
                    "unsupported_abstention_including_fallback",
                    "citation_source_screen",
                    "benchmarks",
                )
            }
        )
    )
