"""Frozen internal holdout evaluation, isolated from application data and credentials."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from app import models as m
from app.evaluation import classification, fraction
from app.intelligence import parse_candidates

CORPUS_DIR = Path(__file__).resolve().parents[1] / "evaluation"


def evaluate_extraction():
    raw = (CORPUS_DIR / "extraction-holdout.json").read_bytes()
    corpus = json.loads(raw)
    people = [
        m.User(id=name, name=name, email=name.replace(" ", ".") + "@evaluation.example")
        for name in ("Ada Vale", "Quinn Reed")
    ]
    gold, predicted, details = [], [], []
    field_results = {"owner": [], "rationale": [], "dependency": []}
    quotes = []
    for document in corpus["documents"]:
        actual = parse_candidates(document["text"], people)
        expected = document["expected"]
        gold.extend((document["id"], c["kind"], c["title"]) for c in expected)
        predicted.extend((document["id"], c["kind"], c["title"]) for c in actual)
        checks = []
        for candidate in expected:
            found = next(
                (c for c in actual if (c["kind"], c["title"]) == (candidate["kind"], candidate["title"])),
                None,
            )
            data = found["data"] if found else {}
            fields = candidate["fields"]
            for field in ("owner", "rationale"):
                if field not in fields:
                    continue
                observed = data.get("owner_id") if field == "owner" else data.get(field, "")
                passed = found is not None and fields[field] == observed
                field_results[field].append(passed)
                checks.append(
                    {"field": field, "expected": fields[field], "observed": observed, "passed": passed}
                )
            if "from_component" in fields:
                observed = {k: data.get(k) for k in ("from_component", "to_component")}
                passed = found is not None and observed == fields
                field_results["dependency"].append(passed)
                checks.append(
                    {"field": "dependency", "expected": fields, "observed": observed, "passed": passed}
                )
        quotes.extend(c["quote"] in document["text"] for c in actual)
        details.append({"id": document["id"], "expected": expected, "observed": actual, "fields": checks})
    scores = classification(gold, predicted)
    metrics = {key: fraction(sum(results), len(results)) for key, results in field_results.items()}
    return {
        "version": corpus["version"],
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "methodology": corpus["methodology"],
        "counts": {
            "documents": len(corpus["documents"]),
            "prose_documents": sum(d["prose"] for d in corpus["documents"]),
        },
        "candidate": scores,
        "fields": metrics,
        "exact_quotes": fraction(sum(quotes), len(quotes)),
        "targets_met": scores["precision"]["rate"] >= 0.9
        and all(metric["rate"] is not None and metric["rate"] >= 0.85 for metric in metrics.values()),
        "false_positives": list((Counter(predicted) - Counter(gold)).elements()),
        "false_negatives": list((Counter(gold) - Counter(predicted)).elements()),
        "details": details,
        "limitations": [
            "Internal authored holdout, no independent label audit.",
            "Exact citation spans do not establish source truth.",
            "English explicit patterns only; multilingual and unrestricted prose remain unvalidated.",
        ],
    }


if __name__ == "__main__":
    result = evaluate_extraction()
    destination = Path(__file__).resolve().parents[2] / "docs" / "extraction-holdout-report.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "counts",
                    "candidate",
                    "fields",
                    "targets_met",
                    "false_positives",
                    "false_negatives",
                )
            }
        )
    )
