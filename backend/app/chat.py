"""Private conversations grounded in current authorised evidence and workflow state."""

import re
import time
from datetime import timedelta
from types import SimpleNamespace

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app import models as m
from app.chat_provider import BUDGETS, ProviderError, call_provider
from app.config import settings
from app.ingestion import privacy_filter
from app.intelligence import citations, current_claims, successor_answer, visible_findings
from app.security import audit, project_access, visible_sources
from app.transfer import claim_signature


def safe_input(text):
    cleaned, detected, _ = privacy_filter(text)
    if set(detected) - {"pii_redacted"}:
        raise HTTPException(422, "Remove secrets or credentials from the message before sending.")
    return cleaned


def configuration(db, user):
    return db.scalar(select(m.AIConfiguration).where(m.AIConfiguration.org_id == user.org_id))


def config_json(record):
    return {
        "provider": "agentrouter",
        "base_url": record.base_url if record else "https://agentrouter.org/v1",
        "model": record.model if record else "",
        "protocol": record.protocol if record else "responses",
        "enabled": bool(record and record.enabled),
        "has_key": bool(record and record.encrypted_key),
    }


def decrypt_key(record):
    try:
        if not settings.token_encryption_key or not record or not record.encrypted_key:
            raise ProviderError("AI settings require a server encryption key and a provider key.")
        return Fernet(settings.token_encryption_key.encode()).decrypt(record.encrypted_key.encode()).decode()
    except (ValueError, InvalidToken):
        raise ProviderError(
            "Saved provider key could not be decrypted. Ask your administrator to update AI settings."
        ) from None


def provider_snapshot(record, model=None):
    if not record:
        return None
    return SimpleNamespace(
        base_url=record.base_url,
        protocol=record.protocol,
        model=model or record.model,
        encrypted_key=record.encrypted_key,
        enabled=record.enabled,
    )


def conversation(db, user, project_id, conversation_id):
    project_access(db, user, project_id)
    record = db.get(m.Conversation, conversation_id)
    if (
        not record
        or record.org_id != user.org_id
        or record.project_id != project_id
        or record.owner_id != user.id
    ):
        raise HTTPException(404, "Conversation unavailable.")
    return record


def evidence_map(db, user, project_id):
    claims = current_claims(db, user, project_id, verified=True)
    return {c.id: c for c in claims}, {r["id"]: r for c in claims for r in citations(db, user, c)}


def access_signature(db, user, project_id):
    member = db.scalar(
        select(m.Membership).where(m.Membership.project_id == project_id, m.Membership.user_id == user.id)
    )
    return [user.role, member.role if member else None]


def history_valid(provenance, claims, sources, roles=None):
    return (
        (not provenance.get("roles") or provenance["roles"] == roles)
        and all(
            cid in claims and claim_signature(claims[cid]) == sig
            for cid, sig in provenance.get("claims", {}).items()
        )
        and all(
            sid in sources and sources[sid].status == "ready" and sources[sid].version == version
            for sid, version in provenance.get("sources", {}).items()
        )
    )


def turns(db, record):
    return list(
        db.scalars(
            select(m.ChatTurn)
            .where(m.ChatTurn.conversation_id == record.id)
            .order_by(m.ChatTurn.created_at, m.ChatTurn.id)
        )
    )


def conversation_json(db, user, record):
    claims, refs = evidence_map(db, user, record.project_id)
    sources = {s.id: s for s in visible_sources(db, user, record.project_id)}
    roles = access_signature(db, user, record.project_id)
    results = []
    for turn in turns(db, record):
        valid = history_valid(turn.provenance, claims, sources, roles)
        response = (
            turn.response
            if valid
            else {
                "answer": "Earlier evidence changed or is no longer accessible. Ask again using current sources.",
                "parts": [],
                "citations": [],
                "actions": [],
                "known": False,
                "engine": "evidence_invalidated",
                "unknowns": [],
                "warning": "This turn was withheld because its evidence is unavailable.",
            }
        )
        if valid:
            response = {
                **response,
                "citations": [
                    jsonable_encoder(refs[rid]) for rid in response.get("citation_ids", []) if rid in refs
                ],
                "actions": [
                    action_json(a)
                    for a in db.scalars(select(m.ChatAction).where(m.ChatAction.turn_id == turn.id))
                ],
            }
        results.append(
            {
                "id": turn.id,
                "question": turn.question if valid else "Earlier question withheld",
                "effort": turn.effort,
                "status": turn.status,
                "response": response,
                "created_at": turn.created_at,
            }
        )
    # Titles are neutral; they never repeat potentially restricted source text.
    return {"id": record.id, "title": record.title, "updated_at": record.updated_at, "turns": results}


def action_json(action):
    return {
        "id": action.id,
        "kind": action.kind,
        "title": action.title,
        "status": action.status,
        "expires_at": action.expires_at,
        "result": action.result,
    }


def action_options(db, user, project_id):
    try:
        project_access(db, user, project_id, write=True)
    except HTTPException:
        return []
    result = [
        {
            "id": "investigate",
            "kind": "investigate",
            "target_id": "",
            "title": "Investigate this project’s authorised sources",
        }
    ]
    for c in db.scalars(
        select(m.Connection)
        .where(m.Connection.project_id == project_id, m.Connection.status != "revoked")
        .limit(15)
    ):
        if c.provider == "github":
            result.append(
                {
                    "id": "sync:" + c.id,
                    "kind": "sync",
                    "target_id": c.id,
                    "title": "Synchronise selected repository: " + c.repository,
                }
            )
    findings = list(db.scalars(select(m.Gap).where(m.Gap.project_id == project_id, m.Gap.status == "open")))
    for gap in findings[:50]:
        if visible_findings(db, user, project_id, [{"source_ids": gap.source_ids, "claim_id": gap.claim_id}]):
            result.append(
                {
                    "id": "start_capture:" + gap.id,
                    "kind": "start_capture",
                    "target_id": gap.id,
                    "title": "Start knowledge capture: " + gap.title,
                }
            )
    for t in db.scalars(
        select(m.Transition)
        .where(m.Transition.project_id == project_id, m.Transition.status != "closed")
        .limit(15)
    ):
        if t.status in {"planned", "draft", "generated", "needs_review"}:
            result.append(
                {
                    "id": "generate_handover:" + t.id,
                    "kind": "generate_handover",
                    "target_id": t.id,
                    "title": "Generate handover: " + t.title,
                }
            )
        if t.status in {"approved", "in_progress"}:
            result.append(
                {
                    "id": "generate_exercises:" + t.id,
                    "kind": "generate_exercises",
                    "target_id": t.id,
                    "title": "Generate practical exercises: " + t.title,
                }
            )
    members = list(
        db.scalars(
            select(m.User)
            .join(m.Membership, m.Membership.user_id == m.User.id)
            .where(m.Membership.project_id == project_id, m.User.active.is_(True))
        ).all()
    )
    for person in members[:20]:
        result.append(
            {
                "id": "simulate:" + person.id,
                "kind": "simulate",
                "target_id": person.id,
                "title": "Simulate unavailability: " + person.name,
            }
        )
    return result[:80]


def status_context(db, user, project_id):
    claims = current_claims(db, user, project_id)
    sources = [s for s in visible_sources(db, user, project_id) if s.status == "ready"]
    status = [
        {
            "id": "status:knowledge",
            "text": f"Accessible current claims: {len(claims)}. Pending review: {sum(c.status == 'pending' for c in claims)}. Verified: {sum(c.status == 'verified' for c in claims)}. Ready sources: {len(sources)}. This measures available evidence, not completeness.",
        },
        {
            "id": "status:ownership",
            "text": f"Recorded responsibility candidates without backup: {sum(c.kind == 'responsibility' and not c.data.get('backup_id') for c in claims)}. Pending ownership is uncertain; absence does not prove no backup exists.",
        },
    ]
    stale = sum(s.source_time < m.utcnow() - timedelta(days=180) for s in sources)
    status.append(
        {
            "id": "status:freshness",
            "text": f"{stale} accessible ready sources are older than the 180-day review interval. Source age is a review signal, not proof that a procedure is wrong.",
        }
    )
    if user.role in {"admin", "manager", "lead", "security"}:
        jobs = list(
            db.scalars(
                select(m.Job)
                .where(m.Job.project_id == project_id)
                .order_by(m.Job.created_at.desc())
                .limit(10)
            )
        )
        status.append(
            {
                "id": "status:integrations",
                "text": f"Recent project jobs: {sum(j.status == 'failed' for j in jobs)} failed, {sum(j.status in {'queued', 'running'} for j in jobs)} queued/running. Failures require checking Connected sources and retrying after the provider or connection issue is resolved.",
            }
        )
    return status


def prepare_context(db, user, project_id, message, effort):
    budget = BUDGETS[effort]
    claims, refs = evidence_map(db, user, project_id)
    words = set(re.findall(r"[\w-]{3,}", message.lower()))
    ranked = sorted(
        claims.values(),
        key=lambda c: len(words & set(re.findall(r"[\w-]{3,}", (c.title + " " + c.summary).lower()))),
        reverse=True,
    )
    evidence = []
    provenance = {
        "claims": {},
        # Status aggregates also depend on sources outside the citation budget.
        "sources": {s.id: s.version for s in visible_sources(db, user, project_id) if s.status == "ready"},
        "roles": access_signature(db, user, project_id),
    }
    chars = 0
    for claim in ranked:
        for ref in citations(db, user, claim):
            entry = {
                "id": ref["id"],
                "claim": claim.title,
                "kind": claim.kind,
                "quote": ref["quote"],
                "source": ref["source_name"],
                "locator": ref["locator"],
                "version": ref["source_version"],
            }
            size = len(str(entry))
            if len(evidence) >= budget["evidence"] or chars + size > budget["chars"]:
                continue
            for field in ("claim", "quote", "source", "locator"):
                entry[field] = safe_input(entry[field])
            evidence.append(entry)
            chars += size
            provenance["claims"][claim.id] = claim_signature(claim)
            provenance["sources"][ref["source_id"]] = ref["source_version"]
    options = action_options(db, user, project_id)
    # Action titles may reference a gap not selected in the model evidence budget.
    # Retain that dependency so revoked sources cannot survive through a preview.
    option_gaps = {o["target_id"] for o in options if o["kind"] == "start_capture"}
    for gap in db.scalars(select(m.Gap).where(m.Gap.id.in_(option_gaps))):
        for source_id in gap.source_ids:
            source = db.get(m.Source, source_id)
            if source:
                provenance["sources"][source_id] = source.version
    return (
        {"evidence": evidence, "status": status_context(db, user, project_id), "available_actions": options},
        provenance,
        refs,
        options,
    )


def inferred_actions(message, options):
    text = message.lower()
    requested = bool(
        re.search(
            r"\b(run|start|retry|sync|synchroni[sz]e|generate|create|simulate|investigate)\b|\b(karo|kro|chala|banao|bna)\b",
            text,
        )
    )
    if not requested:
        return []
    kind = (
        "investigate"
        if "investigat" in text
        else "sync"
        if "sync" in text or "retry" in text
        else "start_capture"
        if "capture" in text
        else "generate_exercises"
        if "exercise" in text
        else "generate_handover"
        if "handover" in text
        else "simulate"
        if "simulat" in text
        else None
    )
    matches = [o for o in options if o["kind"] == kind]
    return [matches[0]["id"]] if len(matches) == 1 else []


def create_previews(db, user, turn, ids, options):
    available = {o["id"]: o for o in options}
    for option_id in dict.fromkeys(ids):
        if option_id not in available:
            raise ProviderError("Model proposed an unavailable action. No action was executed.")
        o = available[option_id]
        db.add(
            m.ChatAction(
                org_id=user.org_id,
                project_id=turn.project_id,
                turn_id=turn.id,
                owner_id=user.id,
                kind=o["kind"],
                target_id=o["target_id"],
                title=o["title"],
                expires_at=m.utcnow() + timedelta(minutes=20),
            )
        )


def send_message(db, user, record, payload):
    # PostgreSQL row lock covers the read/running-record insertion, then releases
    # before the provider request. Two tabs cannot start simultaneous turns.
    db.scalar(select(m.Conversation).where(m.Conversation.id == record.id).with_for_update())
    previous = turns(db, record)
    request_id = str(payload.request_id)
    duplicate = next((t for t in previous if t.request_id == request_id), None)
    if duplicate:
        if duplicate.status == "running":
            raise HTTPException(409, "This message is still being processed.")
        return conversation_json(db, user, record)
    if any(t.status == "running" for t in previous):
        raise HTTPException(409, "Wait for the current reply before sending another message.")
    if len(previous) >= 100:
        raise HTTPException(409, "This conversation reached its limit. Start a new conversation.")
    message = safe_input(payload.message)
    context, provenance, refs, options = prepare_context(db, user, record.project_id, message, payload.effort)
    claims, _ = evidence_map(db, user, record.project_id)
    sources = {s.id: s for s in visible_sources(db, user, record.project_id)}
    history = []
    for old in previous[-BUDGETS[payload.effort]["history"] :]:
        if old.status != "completed" or not history_valid(
            old.provenance, claims, sources, provenance["roles"]
        ):
            continue
        history.extend(
            [
                {"role": "user", "content": old.question},
                {"role": "assistant", "content": old.response.get("answer", "")},
            ]
        )
        provenance["claims"].update(old.provenance.get("claims", {}))
        provenance["sources"].update(old.provenance.get("sources", {}))
    turn = m.ChatTurn(
        org_id=user.org_id,
        project_id=record.project_id,
        conversation_id=record.id,
        request_id=request_id,
        question=message,
        effort=payload.effort,
        provenance=provenance,
    )
    db.add(turn)
    record.updated_at = m.utcnow()
    db.commit()
    started = time.monotonic()
    warning = None
    config = provider_snapshot(configuration(db, user), payload.model)
    # Snapshot provider configuration and release the database connection while
    # waiting for the external service. Revalidate authority after it returns.
    db.commit()
    action_ids = []
    parts = []
    citation_ids = []
    usage = {}
    engine = "verified_retrieval"
    if config and config.enabled:
        try:
            draft, usage = call_provider(
                config, decrypt_key(config), message, payload.effort, context, history
            )
            allowed = {r["id"] for r in context["evidence"]}
            status_ids = {r["id"] for r in context["status"]}
            for part in draft.parts:
                allowed_refs = (
                    allowed if part.kind == "project" else status_ids if part.kind == "status" else set()
                )
                if (part.kind in {"project", "status"} and not part.references) or not set(
                    part.references
                ).issubset(allowed_refs):
                    raise ProviderError(
                        "Answer contained an unsupported evidence reference; verified retrieval was used."
                    )
                text = safe_input(part.text)
                parts.append({"kind": part.kind, "text": text, "references": part.references})
                if part.kind == "project":
                    citation_ids.extend(part.references)
            action_ids = draft.action_ids
            # Action intent is required independently of model output.
            if action_ids and not re.search(
                r"\b(run|start|retry|sync|generate|create|simulate|investigate|karo|kro|banao|bna)\b",
                message,
                re.I,
            ):
                raise ProviderError("Unrequested model action discarded; no action was executed.")
            if any(a not in {o["id"] for o in options} for a in action_ids):
                raise ProviderError("Unavailable model action discarded.")
            engine = "agentrouter"
        except (ProviderError, HTTPException) as exc:
            warning = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
            parts = []
            citation_ids = []
            action_ids = []
    else:
        warning = "AI provider is not enabled. Showing current verified excerpts and available actions."
    if engine != "agentrouter":
        answer = successor_answer(db, user, record.project_id, message)
        parts = [
            {
                "kind": "excerpt" if answer["known"] else "unknown",
                "text": (
                    "Related verified excerpts (keyword matches; they may not answer every part of your question):\n\n"
                    + answer["answer"]
                    if answer["known"]
                    else answer["answer"]
                ),
                "references": [r["id"] for r in answer["citations"]],
            }
        ]
        citation_ids = [r["id"] for r in answer["citations"]]
        for ref in answer["citations"]:
            provenance["sources"][ref["source_id"]] = ref["source_version"]
        for claim in claims.values():
            if any(ref["id"] in citation_ids for ref in citations(db, user, claim)):
                provenance["claims"][claim.id] = claim_signature(claim)
        action_ids = inferred_actions(message, options)
    # Recheck after the external call: access, source or approval may have changed.
    db.expire_all()
    project_access(db, user, record.project_id)
    if not user.active:
        raise HTTPException(403, "This account is no longer authorised.")
    claims, _ = evidence_map(db, user, record.project_id)
    sources = {s.id: s for s in visible_sources(db, user, record.project_id)}
    if not history_valid(provenance, claims, sources, access_signature(db, user, record.project_id)):
        turn.question = "Earlier question withheld because evidence changed"
        parts = [
            {
                "kind": "unknown",
                "text": "Evidence changed while answering. Please ask again using the current sources.",
                "references": [],
            }
        ]
        citation_ids = []
        action_ids = []
        engine = "evidence_invalidated"
    create_previews(db, user, turn, action_ids, options)
    turn.response = {
        "parts": parts,
        "answer": "\n\n".join(p["text"] for p in parts),
        "citation_ids": list(dict.fromkeys(citation_ids)),
        "unknowns": [p["text"] for p in parts if p["kind"] == "unknown"],
        "known": any(p["kind"] == "project" for p in parts),
        "engine": engine,
        "warning": warning,
        "usage": usage,
        "model": config.model if config and engine == "agentrouter" else None,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }
    turn.status = "completed"
    turn.provenance = provenance
    audit(
        db,
        user,
        record.project_id,
        "chat.answered",
        "conversation",
        record.id,
        {"engine": engine, "effort": payload.effort, "cited": len(citation_ids), "fallback": bool(warning)},
    )
    db.commit()
    return conversation_json(db, user, record)
