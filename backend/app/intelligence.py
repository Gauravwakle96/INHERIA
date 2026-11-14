"""Evidence-first reconstruction and bounded knowledge-gap investigation.

Rules report explicit source statements, never infer ownership from commit counts.
The optional model is a candidate extractor; all candidates retain exact quotes.
"""

from __future__ import annotations

import hashlib
import re
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app import models as m
from app.security import audit, project_access, visible_sources

REVIEW_ROLES = {"admin", "manager", "lead"}
KINDS = {
    "responsibility",
    "decision",
    "procedure",
    "dependency",
    "incident",
    "task",
    "lesson",
    "architecture",
}
RESOLVED_STATUSES = {"closed", "resolved", "complete", "completed", "done"}
PREFIX = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(Responsibility|Decision|Procedure|Dependency|Incident|Task|Lesson|Architecture)\s*:\s*(.+)"
)
FIELD = re.compile(
    r"(?im)^\s*(Owner|Proposed owner|Backup|System|Component|Critical|Rationale|Alternatives?|Status|Topic|Documented|Depends on|Verified)\s*:\s*(.+)$"
)


def _rows(db: Session, cls, project_id: str):
    db.flush()
    # Conflict checks/metrics reuse the same claims many times in one request.
    # Never cache across requests or transaction boundaries.
    cache = db.info.setdefault("inheria_claim_rows", {}) if cls is m.Claim else {}
    if project_id not in cache:
        cache[project_id] = list(
            db.scalars(select(cls).where(cls.project_id == project_id).order_by(cls.created_at, cls.id))
        )
    return cache[project_id]


def _clear_evidence_cache(db, *args):
    db.info.pop("inheria_evidence_context", None)
    db.info.pop("inheria_claim_rows", None)


event.listen(Session, "after_flush", _clear_evidence_cache)
event.listen(Session, "after_commit", _clear_evidence_cache)
event.listen(Session, "after_rollback", _clear_evidence_cache)


def _evidence_context(db, user, project_id):
    # Request/transaction scoped only. Flushes and transaction boundaries invalidate it.
    db.flush()
    cache = db.info.setdefault("inheria_evidence_context", {})
    key = (user.id, project_id)
    if key in cache:
        return cache[key]
    project_access(db, user, project_id)
    sources = {
        source.id: source for source in visible_sources(db, user, project_id) if source.status == "ready"
    }
    # Check exact quotes inside the database. Returning whole source chunks on
    # every status/claim request wastes transfer, including unrelated documents.
    position = func.strpos if db.get_bind().dialect.name == "postgresql" else func.instr
    valid_quote = (
        (m.Evidence.org_id == user.org_id)
        & (m.Chunk.org_id == user.org_id)
        & (m.Chunk.project_id == project_id)
        & (m.Chunk.source_id == m.Evidence.source_id)
        & (m.Chunk.source_version == m.Evidence.source_version)
        & (m.Evidence.quote != "")
        & (position(m.Chunk.text, m.Evidence.quote) > 0)
    )
    evidence_rows = list(
        db.execute(
            select(m.Evidence, m.Chunk.locator, valid_quote)
            .outerjoin(m.Chunk, m.Chunk.id == m.Evidence.chunk_id)
            .where(m.Evidence.project_id == project_id)
            .order_by(m.Evidence.created_at, m.Evidence.id)
        )
    )
    by_claim = {}
    validated = {}
    for ref, locator, valid in evidence_rows:
        by_claim.setdefault(ref.claim_id, []).append(ref)
        validated[ref.id] = {"valid": bool(valid), "locator": locator}
    result = (sources, validated, by_claim)
    cache[key] = result
    return result


def _valid_evidence(ref, sources, validated, org_id, project_id):
    source = sources.get(ref.source_id)
    return bool(
        source
        and ref.org_id == org_id
        and ref.project_id == project_id
        and source.version == ref.source_version
        and validated.get(ref.id, {}).get("valid")
    )


def current_claims(
    db: Session, user: m.User, project_id: str, *, verified: bool = False, include_rejected: bool = False
) -> list[m.Claim]:
    """Mixed-permission evidence is hidden in full, including from administrators."""
    sources, validated, by_claim = _evidence_context(db, user, project_id)
    result = []
    for claim in _rows(db, m.Claim, project_id):
        refs = by_claim.get(claim.id, [])
        if not refs or any(not _valid_evidence(e, sources, validated, user.org_id, project_id) for e in refs):
            continue
        if verified and claim.status != "verified":
            continue
        if verified and decision_conflicted(db, claim):
            continue
        if not include_rejected and claim.status in {"rejected", "invalidated", "superseded"}:
            continue
        result.append(claim)
    return result


def decision_conflicted(db, claim):
    """Conflicting current interpretations cannot enter verified retrieval/handover."""
    if claim.kind != "decision" or not claim.data.get("topic"):
        return False
    return any(
        other.id != claim.id
        and other.status not in {"rejected", "invalidated", "superseded"}
        and other.data.get("source_status", "").lower() != "superseded"
        and other.data.get("topic") == claim.data.get("topic")
        and (other.title != claim.title or other.data.get("rationale") != claim.data.get("rationale"))
        for other in _rows(db, m.Claim, claim.project_id)
        if other.kind == "decision"
    )


def citations(db: Session, user: m.User, claim: m.Claim) -> list[dict]:
    sources, validated, by_claim = _evidence_context(db, user, claim.project_id)
    refs = by_claim.get(claim.id, [])
    if any(not _valid_evidence(e, sources, validated, user.org_id, claim.project_id) for e in refs):
        return []
    result = []
    for e in refs:
        source = sources[e.source_id]
        result.append(
            {
                "id": e.id,
                "source_id": source.id,
                "source_name": source.name,
                "source_kind": source.kind,
                "source_url": source.url,
                "source_time": source.source_time,
                "source_version": e.source_version,
                "chunk_id": e.chunk_id,
                "locator": validated[e.id]["locator"],
                "quote": e.quote,
                "synthetic": source.synthetic,
            }
        )
    return result


def serialize_claim(db: Session, user: m.User, claim: m.Claim) -> dict:
    refs = citations(db, user, claim)
    if not refs:
        raise HTTPException(404, "Knowledge evidence is unavailable or restricted.")
    return {
        "id": claim.id,
        "kind": claim.kind,
        "title": claim.title,
        "summary": claim.summary,
        "status": claim.status,
        "confidence": claim.confidence,
        "confidence_reason": claim.confidence_reason,
        "data": claim.data,
        "evidence": refs,
        "updated_at": claim.updated_at,
        "authority_conflict": decision_conflicted(db, claim)
        if claim.status not in {"superseded", "rejected", "invalidated"}
        else False,
    }


def parse_candidates(text: str, users: list[m.User]) -> list[dict]:
    matches = list(PREFIX.finditer(text))
    candidates = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        quote = text[match.start() : end].strip()[:4000]
        fields = {k.lower(): v.strip() for k, v in FIELD.findall(quote)}
        kind, title = match.group(1).lower(), match.group(2).strip()[:180]
        data: dict = {
            "extraction": "explicit_source_statement",
            "component": fields.get("system", fields.get("component", "")),
            "critical": fields.get("critical", "").lower() in {"true", "yes", "critical"},
            "source_status": fields.get("status", "unspecified"),
        }
        for source_key, target in [("owner", "owner_id"), ("backup", "backup_id")]:
            name = fields.get(source_key, fields.get("proposed owner", "") if source_key == "owner" else "")
            person = next(
                (u for u in users if name.casefold() in {u.name.casefold(), u.email.casefold()}), None
            )
            data[target] = person.id if person else None
            if name and not person and name.lower() not in {"none", "unknown", "unassigned", "n/a"}:
                data[source_key + "_unresolved"] = name
        data["documented"] = fields.get("documented", "").lower() not in {"no", "false", "undocumented"}
        if kind == "decision":
            data.update(
                rationale=fields.get("rationale", ""),
                alternative=fields.get("alternative", fields.get("alternatives", "")),
                topic=fields.get("topic", title),
                source_status=fields.get("status", "unspecified"),
            )
        if kind == "dependency":
            relation = re.split(r"\s*(?:->|→|depends on)\s*", title, maxsplit=1, flags=re.I)
            if len(relation) == 2:
                data.update(from_component=relation[0].strip(), to_component=relation[1].strip())
            elif fields.get("depends on") and data["component"]:
                data.update(from_component=data["component"], to_component=fields["depends on"])
        candidates.append({"kind": kind, "title": title, "summary": quote, "quote": quote, "data": data})
    # Conservative fallback for ordinary READMEs/issues: a quoted candidate, not a inferred fact.
    if not matches:
        for paragraph in re.split(r"\n\s*\n", text):
            paragraph = paragraph.strip()
            if len(paragraph) < 25:
                continue
            lower = paragraph.lower()
            from app.prose import dependency_span, named_duties, unasserted, unconfirmed_context

            duties = named_duties(paragraph, users)
            if paragraph.count("?") or re.search(r"(?im)^#.*(?:questions|example|outline)", paragraph):
                continue  # Interview prompts and templates are not procedure evidence.
            if re.search(
                r"\b(no (?:source|evidence|documentation)|insufficient evidence|ownership is unknown)\b",
                lower,
            ):
                continue
            if "not documented" in lower and not re.search(
                r"\b(?:decided|decision|chose|chosen|selected|adopted)\b", lower
            ):
                continue
            if unconfirmed_context(paragraph) or (unasserted(paragraph) and not duties):
                continue  # Historical duties and proposals need explicit human capture.
            kind = None

            if (
                duties or re.search(r"\b(?:is responsible for|owns|maintains|handles|looks after)\b", lower)
            ) and (
                duties
                or not re.search(
                    r"\b(?:might|may|could|unknown|no longer)\b|\bnot (?:responsible|owned|maintained|handled)\b",
                    lower,
                )
            ):
                kind = "responsibility"
            elif dependency_span(paragraph) and not re.search(r"\b(?:might|may|could|not|unknown)\b", lower):
                kind = "dependency"
            elif (
                re.search(r"\b(rollback|deploy(?:ment)?|recovery)\b", lower)
                and re.search(r"\b(step|run|pipeline|procedure|command)\b", lower)
                and not re.search(r"\b(?:no longer|not confirmed|might|may|could)\b", lower)
            ):
                kind = "procedure"
            elif re.search(
                r"\b(decided|decision|chose|chosen|selected|opted for|adopted|rejected alternative)\b", lower
            ):
                kind = "decision"
            elif re.search(r"\b(unresolved|open incident|known issue|todo|unfinished)\b", lower):
                kind = "incident" if "incident" in lower else "task"
            if kind:
                from app.prose import prose_fields

                quote = paragraph[:3000]
                candidates.append(
                    {
                        "kind": kind,
                        "title": quote.splitlines()[0][:180],
                        "summary": quote,
                        "quote": quote,
                        "data": prose_fields(quote, kind, users),
                    }
                )
    return candidates[:25]


def reconstruct_project(
    db: Session, user: m.User, project_id: str, *, source_ids: set[str] | None = None
) -> dict:
    project = project_access(db, user, project_id)
    source_list = [s for s in visible_sources(db, user, project_id) if s.status == "ready"]
    if source_ids is not None:
        source_list = [source for source in source_list if source.id in source_ids]
    user_ids = list(db.scalars(select(m.Membership.user_id).where(m.Membership.project_id == project_id)))
    users = list(db.scalars(select(m.User).where(m.User.id.in_(user_ids)))) if user_ids else []
    existing = _rows(db, m.Claim, project_id)
    keys = {c.data.get("fingerprint") for c in existing if c.status != "invalidated"}
    added = 0
    for source in source_list:
        if source.kind in {"interview", "ownership_transfer"}:
            continue  # Interview claims are created explicitly with human authorship.
        chunks = list(
            db.scalars(
                select(m.Chunk)
                .where(m.Chunk.source_id == source.id, m.Chunk.source_version == source.version)
                .order_by(m.Chunk.ordinal)
            )
        )
        for chunk in chunks:
            for item in parse_candidates(chunk.text, users):
                key = hashlib.sha256(
                    f"{source.id}:{source.version}:{chunk.id}:{item['kind']}:{item['quote']}".encode()
                ).hexdigest()
                if key in keys:
                    continue
                claim = m.Claim(
                    org_id=project.org_id,
                    project_id=project_id,
                    kind=item["kind"],
                    title=item["title"],
                    summary=item["summary"],
                    status="pending",
                    confidence="source_statement",
                    confidence_reason="An exact source excerpt supports this candidate. Human verification is required; source statements may be incorrect.",
                    data={
                        **item["data"],
                        "fingerprint": key,
                        "engine": "deterministic-v1",
                        "requested_by": user.id,
                    },
                    created_by=None,
                )
                db.add(claim)
                db.flush()
                db.add(
                    m.Evidence(
                        org_id=project.org_id,
                        project_id=project_id,
                        claim_id=claim.id,
                        chunk_id=chunk.id,
                        source_id=source.id,
                        source_version=source.version,
                        quote=item["quote"],
                    )
                )
                keys.add(key)
                added += 1
    audit(
        db,
        user,
        project_id,
        "knowledge.reconstructed",
        "project",
        project_id,
        {"added_candidates": added, "authorised_sources": len(source_list), "engine": "deterministic-v1"},
    )
    db.flush()
    return {"added_candidates": added, "searched_sources": len(source_list), "engine": "deterministic-v1"}


def find_gaps(
    db: Session, user: m.User, project_id: str, focus: str = "", employee_id: str | None = None
) -> list[dict]:
    sources = {s.id: s for s in visible_sources(db, user, project_id) if s.status == "ready"}
    claims = current_claims(db, user, project_id)
    findings = []

    def add(title, kind, severity, details, question, refs, claim_id=None):
        findings.append(
            {
                "title": title,
                "kind": kind,
                "severity": severity,
                "details": details,
                "question": question,
                "source_ids": sorted(set(refs)),
                "claim_id": claim_id,
            }
        )

    if not sources:
        add(
            "No authorised knowledge sources",
            "missing_evidence",
            "critical",
            "No ready sources are available to this investigator. Restricted sources were not searched.",
            "Which project documents and repositories can be authorised for this handover?",
            [],
        )
    responsibilities = [c for c in claims if c.kind == "responsibility"]
    if not responsibilities:
        add(
            "Responsibilities have not been confirmed",
            "unknown_ownership",
            "high",
            "Available sources do not establish who performs the critical work. Activity alone is not ownership evidence.",
            "Which recurring operations and systems do you own, and where can this be verified?",
            list(sources),
        )
    for claim in claims:
        refs = [e["source_id"] for e in citations(db, user, claim)]
        data = claim.data
        if employee_id and claim.kind == "responsibility" and data.get("owner_id") != employee_id:
            continue
        if focus and not any(
            word in (claim.title + " " + claim.summary).lower() for word in focus.lower().split()
        ):
            continue
        if claim.kind == "responsibility":
            if not data.get("owner_id"):
                add(
                    f"Owner unknown: {claim.title}",
                    "unknown_ownership",
                    "high",
                    "No identified project member is explicitly established as owner.",
                    f"Who is accountable for {claim.title}, and which source confirms that ownership?",
                    refs,
                    claim.id,
                )
            if not data.get("backup_id"):
                add(
                    f"No backup recorded: {claim.title}",
                    "single_owner",
                    "critical" if data.get("critical") else "high",
                    "This responsibility has no recorded backup. This is a knowledge coverage observation, not proof of operational failure.",
                    f"Who can cover {claim.title} and which procedure would they follow?",
                    refs,
                    claim.id,
                )
            component = data.get("component")
            procedures = [
                c
                for c in claims
                if c.kind == "procedure"
                and component
                and component.casefold() in (c.title + " " + c.summary).casefold()
            ]
            if not procedures or not data.get("documented", True):
                add(
                    f"Procedure missing: {claim.title}",
                    "missing_procedure",
                    "high",
                    "No matching operational procedure was located in the authorised evidence searched.",
                    f"Walk through {claim.title}: prerequisites, deployment or rollback steps, and when to escalate.",
                    refs,
                    claim.id,
                )
        if (
            claim.kind == "decision"
            and not data.get("rationale")
            and (
                data.get("extraction") == "explicit_source_statement"
                or not re.search(r"\b(because|rationale|reason|trade-off)\b", claim.summary, re.I)
            )
        ):
            add(
                f"Rationale missing: {claim.title}",
                "missing_rationale",
                "medium",
                "The decision is stated, but the reasoning is absent from the retrieved excerpt.",
                f"Why was {claim.title} selected, and which alternatives were rejected?",
                refs,
                claim.id,
            )
        if claim.kind == "procedure" and claim.status != "verified":
            add(
                f"Procedure unverified: {claim.title}",
                "unverified_procedure",
                "high",
                "An operational procedure exists but has not received authorised human verification.",
                f"When was {claim.title} last tested safely, by whom, and what evidence confirms it?",
                refs,
                claim.id,
            )
        if (
            claim.kind in {"task", "incident"}
            and data.get("source_status", "").lower() not in RESOLVED_STATUSES
        ):
            add(
                f"Unresolved work: {claim.title}",
                "unfinished_work",
                "high",
                "The source records work or an incident without evidence of closure.",
                f"What remains for {claim.title}, who owns the next action, and where is progress recorded?",
                refs,
                claim.id,
            )
        for source_id in refs:
            source = sources[source_id]
            if source.source_time and source.source_time < m.utcnow() - timedelta(days=180):
                add(
                    f"Outdated evidence: {claim.title}",
                    "stale_source",
                    "medium",
                    "Supporting evidence is older than the configured 180-day review interval; age does not prove inaccuracy.",
                    f"Is {claim.title} still current? Provide a recent safe validation or updated source.",
                    [source_id],
                    claim.id,
                )
                break
    decisions = [c for c in claims if c.kind == "decision"]
    for index, left in enumerate(decisions):
        for right in decisions[index + 1 :]:
            same_topic = left.data.get("topic") and left.data.get("topic") == right.data.get("topic")
            superseded = any(c.data.get("source_status", "").lower() == "superseded" for c in [left, right])
            differs = left.data.get("rationale") != right.data.get("rationale") or left.title != right.title
            if same_topic and differs and not superseded:
                refs = [e["source_id"] for c in [left, right] for e in citations(db, user, c)]
                add(
                    f"Decision conflict requires review: {left.data.get('topic') or left.title}",
                    "contradiction",
                    "high",
                    f"Two decision excerpts may disagree: “{left.title}” and “{right.title}”. A reviewer must determine chronology and authority.",
                    "Which decision is currently authoritative, what changed, and which evidence resolves the conflict?",
                    refs,
                    left.id,
                )
    unique = {f"{f['kind']}:{f['claim_id']}:{f['title']}": f for f in findings}
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(unique.values(), key=lambda f: (rank[f["severity"]], f["title"]))[:200]


def run_investigation(investigation_id: str, focus: str = "", employee_id: str | None = None):
    from app.database import SessionLocal

    with SessionLocal() as db:
        investigation = db.get(m.Investigation, investigation_id)
        if not investigation:
            return
        user = db.get(m.User, investigation.created_by)
        try:
            project_access(db, user, investigation.project_id, write=True)
            investigation.status = "running"
            progress = dict((investigation.report or {}).get("checkpoint", {}))
            completed = dict(progress.get("sources", {}))
            focus = (investigation.report or {}).get("focus", focus)
            employee_id = (investigation.report or {}).get("employee_id", employee_id)
            db.commit()
            added = progress.get("added_candidates", 0)
            for source in visible_sources(db, user, investigation.project_id):
                db.refresh(source)
                if source.status != "ready" or completed.get(source.id) == source.version:
                    continue
                project_access(db, user, investigation.project_id, write=True)
                stats = reconstruct_project(db, user, investigation.project_id, source_ids={source.id})
                completed[source.id] = source.version
                added += stats["added_candidates"]
                investigation.report = {
                    **investigation.report,
                    "checkpoint": {"sources": completed, "added_candidates": added},
                    "focus": focus,
                    "employee_id": employee_id,
                }
                # Candidates and checkpoint are committed together; retries are idempotent.
                db.commit()
            stats = {"added_candidates": added, "engine": "deterministic-v1"}
            from app.config import settings

            llm_status = "disabled"
            if settings.llm_enabled:
                from app.llm import extract_candidates

                sources = [
                    s for s in visible_sources(db, user, investigation.project_id) if s.status == "ready"
                ]
                source_map = {s.id: s for s in sources}
                chunks = list(
                    db.scalars(
                        select(m.Chunk)
                        .where(m.Chunk.source_id.in_(source_map))
                        .order_by(m.Chunk.created_at.desc())
                    )
                )
                selected, budget = [], 0
                for chunk in chunks:
                    if chunk.source_version != source_map[chunk.source_id].version:
                        continue
                    if len(selected) >= 15 or budget + len(chunk.text) > 30000:
                        continue
                    selected.append(chunk)
                    budget += len(chunk.text)
                try:
                    candidates = (
                        extract_candidates(
                            settings.llm_base_url,
                            settings.llm_api_key,
                            settings.llm_model,
                            [{"id": c.id, "text": c.text} for c in selected],
                        )
                        if selected
                        else []
                    )
                    chunk_map = {c.id: c for c in selected}
                    known_quotes = {
                        (e.chunk_id, e.quote) for e in _rows(db, m.Evidence, investigation.project_id)
                    }
                    for item in candidates:
                        if (item.chunk_id, item.quote) in known_quotes:
                            continue
                        chunk = chunk_map[item.chunk_id]
                        source = source_map[chunk.source_id]
                        claim = m.Claim(
                            org_id=investigation.org_id,
                            project_id=investigation.project_id,
                            kind=item.kind,
                            title=item.title,
                            summary=item.quote,
                            status="pending",
                            confidence="model_candidate",
                            confidence_reason="Exact source quote validated; interpretation still requires human review.",
                            data={
                                "engine": "llm-structured-v1",
                                "owner_id": None,
                                "backup_id": None,
                                "component": "",
                                "critical": False,
                                "model": settings.llm_model,
                            },
                            created_by=None,
                        )
                        db.add(claim)
                        db.flush()
                        db.add(
                            m.Evidence(
                                org_id=investigation.org_id,
                                project_id=investigation.project_id,
                                claim_id=claim.id,
                                chunk_id=chunk.id,
                                source_id=source.id,
                                source_version=source.version,
                                quote=item.quote,
                            )
                        )
                    llm_status = "completed"
                    audit(
                        db,
                        user,
                        investigation.project_id,
                        "ai.extraction_completed",
                        "investigation",
                        investigation.id,
                        {
                            "chunks": len(selected),
                            "input_characters": budget,
                            "candidate_count": len(candidates),
                            "model": settings.llm_model,
                            "prompt_version": "extract-v1",
                        },
                    )
                except Exception:
                    llm_status = "failed_rule_fallback"
                    audit(
                        db,
                        user,
                        investigation.project_id,
                        "ai.extraction_failed",
                        "investigation",
                        investigation.id,
                        {"fallback": "deterministic-v1", "prompt_version": "extract-v1"},
                    )
            findings = find_gaps(db, user, investigation.project_id, focus, employee_id)
            visible_ids = {
                s.id for s in visible_sources(db, user, investigation.project_id) if s.status == "ready"
            }
            existing = _rows(db, m.Gap, investigation.project_id)
            keys = {(g.title, g.kind, g.claim_id) for g in existing}
            for finding in findings:
                key = (finding["title"], finding["kind"], finding["claim_id"])
                if key not in keys:
                    db.add(
                        m.Gap(
                            org_id=investigation.org_id,
                            project_id=investigation.project_id,
                            investigation_id=investigation.id,
                            **finding,
                            status="open",
                        )
                    )
                    keys.add(key)
            unknowns = [
                "An absence in the searched sources is not proof that the knowledge does not exist elsewhere.",
                "Activity or authorship does not establish employee competence or formal responsibility.",
            ]
            investigation.report = {
                "summary": f"Investigated {len(visible_ids)} authorised sources; {len(findings)} evidence gaps require review.",
                "findings": findings,
                "questions": [
                    {"question": f["question"], "reason": f["details"], "source_ids": f["source_ids"]}
                    for f in findings[:20]
                ],
                "searched_sources": len(visible_ids),
                "unknowns": unknowns,
                "engine": "deterministic-v1",
                "limitations": [
                    "Rule-based evidence investigation; no arbitrary risk or AI accuracy scores.",
                    "Authoritative knowledge was not modified. Human approval is required.",
                ],
                **stats,
                "llm_status": llm_status,
                "checkpoint": {"sources": completed, "added_candidates": added},
                "focus": focus,
                "employee_id": employee_id,
            }
            investigation.status = "completed"
            audit(
                db,
                user,
                investigation.project_id,
                "investigation.completed",
                "investigation",
                investigation.id,
                {"findings": len(findings), "searched_sources": len(visible_ids)},
            )
            db.commit()
        except Exception:
            db.rollback()
            investigation = db.get(m.Investigation, investigation_id)
            if investigation:
                investigation.status = "failed"
                investigation.report = {
                    **(investigation.report or {}),
                    "summary": "Investigation failed. Check source access and retry.",
                    "findings": [],
                    "questions": [],
                    "unknowns": ["No authoritative knowledge was changed."],
                    "engine": "deterministic-v1",
                    "limitations": [],
                }
                db.commit()


def visible_findings(db: Session, user: m.User, project_id: str, findings: list[dict]) -> list[dict]:
    ids = {s.id for s in visible_sources(db, user, project_id) if s.status == "ready"}
    claims = {c.id for c in current_claims(db, user, project_id)}
    return [
        f
        for f in findings
        if set(f.get("source_ids", [])).issubset(ids) and (not f.get("claim_id") or f["claim_id"] in claims)
    ]


def build_graph(db: Session, user: m.User, project_id: str) -> dict:
    project = project_access(db, user, project_id)
    claims = current_claims(db, user, project_id)
    nodes = {project.id: {"id": project.id, "label": project.name, "kind": "project", "status": "current"}}
    edges = []
    for claim in claims:
        nodes[claim.id] = {"id": claim.id, "label": claim.title, "kind": claim.kind, "status": claim.status}
        refs = citations(db, user, claim)
        edges.append(
            {
                "id": f"project-{claim.id}",
                "source": project.id,
                "target": claim.id,
                "label": "documented in project",
                "status": claim.status,
                "evidence": refs,
            }
        )
        for field, label in [("owner_id", "recorded owner"), ("backup_id", "recorded backup")]:
            person = db.get(m.User, claim.data.get(field)) if claim.data.get(field) else None
            if person and person.org_id == user.org_id:
                nodes[person.id] = {
                    "id": person.id,
                    "label": person.name,
                    "kind": "person",
                    "status": claim.status,
                }
                edges.append(
                    {
                        "id": f"{field}-{claim.id}",
                        "source": person.id,
                        "target": claim.id,
                        "label": label,
                        "status": claim.status,
                        "evidence": refs,
                    }
                )
        if claim.kind == "dependency" and claim.data.get("from_component") and claim.data.get("to_component"):
            ids = []
            for component in [claim.data["from_component"], claim.data["to_component"]]:
                node_id = "system-" + hashlib.sha256(component.casefold().encode()).hexdigest()[:20]
                nodes[node_id] = {"id": node_id, "label": component, "kind": "system", "status": claim.status}
                ids.append(node_id)
            edges.append(
                {
                    "id": f"dep-{claim.id}",
                    "source": ids[0],
                    "target": ids[1],
                    "label": "depends on",
                    "status": claim.status,
                    "evidence": refs,
                }
            )
    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "limitations": [
            "Edges quote authorised sources. Pending relationships require human confirmation; absent edges were not invented."
        ],
    }


def successor_answer(db: Session, user: m.User, project_id: str, question: str) -> dict:
    claims = current_claims(db, user, project_id, verified=True)
    stop = {
        "what",
        "which",
        "where",
        "when",
        "does",
        "this",
        "that",
        "with",
        "from",
        "have",
        "about",
        "should",
        "would",
        "there",
        "they",
        "their",
        "how",
        "the",
        "and",
        "are",
        "can",
        "why",
        "was",
        "were",
    }
    terms = {w for w in re.findall(r"[a-z0-9_-]{3,}", question.lower()) if w not in stop}
    ranked = []
    requested_financial = bool(re.search(r"\b(financial|cost|revenue|budget|money)\b", question, re.I))
    requested_duration = bool(
        re.search(r"\b(duration|downtime|how long|how many hours|how many minutes)\b", question, re.I)
    )
    intent = (
        "decision"
        if question.lower().startswith("why ")
        else "owner"
        if question.lower().startswith("who ")
        else None
    )
    components = {term for term in terms if "-" in term or "_" in term}
    for claim in claims:
        if requested_financial and not re.search(
            r"\b(financial|cost|revenue|budget|money)\b", claim.summary, re.I
        ):
            continue
        if requested_duration and not re.search(
            r"\b(duration|downtime|hours|minutes)\b", claim.summary, re.I
        ):
            continue
        if intent == "decision" and claim.kind not in {"decision", "architecture"}:
            continue
        if intent == "owner" and not claim.data.get("owner_id"):
            continue
        words = set(re.findall(r"[a-z0-9_-]{3,}", (claim.title + " " + claim.summary).lower()))
        if not components.issubset(words):
            continue
        overlap = len(terms & words)
        if overlap and overlap / max(1, len(terms)) >= 0.5:
            ranked.append((overlap, claim))
    ranked.sort(key=lambda row: (-row[0], row[1].id))
    selected = [c for _, c in ranked[:3]]
    if not selected:
        return {
            "answer": "Insufficient Evidence. No verified, authorised source directly answers this question. Ask an authorised project lead or create an investigation task.",
            "known": False,
            "citations": [],
            "unknowns": ["The answer could not be established from accessible verified knowledge."],
            "engine": "evidence-retrieval-v1",
        }
    refs = [e for c in selected for e in citations(db, user, c)]
    return {
        "answer": "\n\n".join(f"{c.title}\n{c.summary}" for c in selected),
        "known": True,
        "citations": refs,
        "unknowns": [
            "These are matching verified excerpts, not a guarantee that all aspects of the question are answered."
        ],
        "engine": "evidence-retrieval-v1",
    }
