"""Chat endpoints reuse existing domain handlers; confirmation never grants authority."""

from typing import Annotated

from cryptography.fernet import Fernet
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app import chat, schemas
from app import chat_schemas as s
from app import models as m
from app.chat_provider import ProviderError, call_provider, provider_name
from app.config import settings
from app.database import get_db
from app.security import audit, current_user, project_access, require_role, visible_sources

router = APIRouter(prefix="/api", tags=["Digital Successor chat"])
Db = Annotated[Session, Depends(get_db)]
User = Annotated[m.User, Depends(current_user)]


@router.get("/projects/{project_id}/ai-settings")
def ai_settings(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    return chat.config_json(chat.configuration(db, user))


@router.put("/projects/{project_id}/ai-settings")
def save_settings(project_id: str, payload: s.AISettingsUpdate, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    record = chat.configuration(db, user)
    if record and record.encrypted_key and record.base_url != payload.base_url and not payload.api_key:
        raise HTTPException(422, "Enter a new provider key when changing the endpoint.")
    if not record:
        record = m.AIConfiguration(org_id=user.org_id)
        db.add(record)
    if payload.api_key:
        try:
            record.encrypted_key = (
                Fernet(settings.token_encryption_key.encode()).encrypt(payload.api_key.encode()).decode()
            )
        except (ValueError, TypeError):
            raise HTTPException(
                503, "Server token encryption is not configured. Ask the deployment administrator."
            ) from None
    if payload.enabled and not record.encrypted_key:
        raise HTTPException(422, "Enter a provider key before enabling AI.")
    record.base_url, record.model, record.protocol, record.enabled = (
        payload.base_url,
        payload.model,
        payload.protocol,
        payload.enabled,
    )
    record.provider = provider_name(record.base_url)
    audit(
        db,
        user,
        project_id,
        "ai.settings_updated",
        "organisation",
        user.org_id,
        {"enabled": record.enabled, "protocol": record.protocol},
    )
    db.commit()
    return chat.config_json(record)


@router.delete("/projects/{project_id}/ai-settings")
def disconnect_ai(project_id: str, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    record = chat.configuration(db, user)
    if record:
        db.delete(record)
    audit(db, user, project_id, "ai.disconnected", "organisation", user.org_id, {})
    db.commit()
    return {"ok": True}


@router.post("/projects/{project_id}/ai-settings/test")
def test_ai(project_id: str, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    config = chat.provider_snapshot(chat.configuration(db, user))
    if not config or not config.model:
        raise HTTPException(422, "Save provider settings first.")
    db.commit()
    try:
        draft, usage = call_provider(
            config,
            chat.decrypt_key(config),
            "Connection test. Return an unknown part saying Connection successful.",
            "low",
            {"evidence": [], "status": [], "available_actions": []},
            [],
        )
        if any(p.references for p in draft.parts):
            raise ProviderError("Connection response contained unsupported references.")
    except ProviderError as exc:
        raise HTTPException(502, str(exc)) from None
    db.expire_all()
    db.info.pop("inheria_evidence_context", None)
    db.info.pop("inheria_claim_rows", None)
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    audit(db, user, project_id, "ai.connection_tested", "organisation", user.org_id, {"success": True})
    db.commit()
    return {"ok": True, "model": config.model, "usage": usage}


@router.get("/projects/{project_id}/chat/conversations")
def conversations(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    return [
        {"id": r.id, "title": r.title, "updated_at": r.updated_at}
        for r in db.scalars(
            select(m.Conversation)
            .where(
                m.Conversation.project_id == project_id,
                m.Conversation.org_id == user.org_id,
                m.Conversation.owner_id == user.id,
            )
            .order_by(m.Conversation.updated_at.desc())
            .limit(50)
        )
    ]


@router.post("/projects/{project_id}/chat/conversations", status_code=201)
def new_conversation(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    count = len(
        list(
            db.scalars(
                select(m.Conversation.id).where(
                    m.Conversation.project_id == project_id, m.Conversation.owner_id == user.id
                )
            )
        )
    )
    if count >= 50:
        raise HTTPException(409, "Conversation limit reached. Delete an old conversation to continue.")
    record = m.Conversation(
        org_id=user.org_id, project_id=project_id, owner_id=user.id, title="Conversation " + str(count + 1)
    )
    db.add(record)
    db.commit()
    return chat.conversation_json(db, user, record)


@router.get("/projects/{project_id}/chat/conversations/{conversation_id}")
def get_conversation(project_id: str, conversation_id: str, db: Db, user: User):
    return chat.conversation_json(db, user, chat.conversation(db, user, project_id, conversation_id))


@router.delete("/projects/{project_id}/chat/conversations/{conversation_id}")
def remove_conversation(project_id: str, conversation_id: str, db: Db, user: User):
    record = chat.conversation(db, user, project_id, conversation_id)
    turn_ids = select(m.ChatTurn.id).where(m.ChatTurn.conversation_id == record.id)
    db.execute(delete(m.ChatAction).where(m.ChatAction.turn_id.in_(turn_ids)))
    db.execute(delete(m.ChatTurn).where(m.ChatTurn.conversation_id == record.id))
    db.delete(record)
    audit(db, user, project_id, "chat.deleted", "conversation", record.id, {})
    db.commit()
    return {"ok": True}


@router.post("/projects/{project_id}/chat/conversations/{conversation_id}/messages")
def send(project_id: str, conversation_id: str, payload: s.ChatRequest, db: Db, user: User):
    record = chat.conversation(db, user, project_id, conversation_id)
    existing = db.scalar(
        select(m.ChatTurn.id).where(
            m.ChatTurn.conversation_id == record.id, m.ChatTurn.request_id == str(payload.request_id)
        )
    )
    try:
        return chat.send_message(db, user, record, payload)
    except Exception:
        db.rollback()
        if existing:
            raise
        # A committed running record must not permanently block retry after failure.
        db.execute(
            update(m.ChatTurn)
            .where(
                m.ChatTurn.conversation_id == record.id,
                m.ChatTurn.request_id == str(payload.request_id),
                m.ChatTurn.status == "running",
            )
            .values(
                status="failed",
                response={
                    "answer": "Reply interrupted. Send the message again.",
                    "warning": "Reply interrupted.",
                    "engine": "failed",
                    "known": False,
                    "parts": [],
                    "actions": [],
                    "unknowns": [],
                },
            )
        )
        db.commit()
        raise


@router.get("/projects/{project_id}/chat/actions")
def available_actions(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    return chat.action_options(db, user, project_id)


@router.post("/projects/{project_id}/chat/conversations/{conversation_id}/actions", status_code=201)
def preview_action(project_id: str, conversation_id: str, payload: s.ActionRequest, db: Db, user: User):
    record = chat.conversation(db, user, project_id, conversation_id)
    if len(chat.turns(db, record)) >= 100:
        raise HTTPException(409, "Conversation limit reached. Start a new conversation.")
    options = chat.action_options(db, user, project_id)
    option = next(
        (o for o in options if o["kind"] == payload.kind and o["target_id"] == payload.target_id), None
    )
    if not option:
        raise HTTPException(403, "This action is unavailable for your role or project state.")
    provenance = {
        "roles": chat.access_signature(db, user, project_id),
        "sources": {
            src.id: src.version for src in visible_sources(db, user, project_id) if src.status == "ready"
        },
        "claims": {},
    }
    turn = m.ChatTurn(
        org_id=user.org_id,
        project_id=project_id,
        conversation_id=record.id,
        request_id=m.new_id(),
        question="Preview requested action",
        effort="low",
        status="completed",
        provenance=provenance,
        response={
            "answer": "Review this action before confirming. No changes have been made.",
            "parts": [],
            "known": False,
            "engine": "action_preview",
            "unknowns": [],
        },
    )
    db.add(turn)
    db.flush()
    chat.create_previews(db, user, turn, [option["id"]], options)
    record.updated_at = m.utcnow()
    db.commit()
    return chat.conversation_json(db, user, record)


@router.post("/projects/{project_id}/chat/actions/{action_id}/confirm")
def confirm_action(
    project_id: str, action_id: str, payload: s.Confirmation, tasks: BackgroundTasks, db: Db, user: User
):
    project_access(db, user, project_id, write=True)
    action = db.get(m.ChatAction, action_id)
    if (
        not action
        or action.project_id != project_id
        or action.org_id != user.org_id
        or action.owner_id != user.id
    ):
        raise HTTPException(404, "Action unavailable.")
    if action.status == "completed":
        return chat.action_json(action)
    if action.status != "pending" or action.expires_at < m.utcnow():
        raise HTTPException(
            409, "Action preview expired or is already being confirmed. Request a new preview."
        )
    turn = db.get(m.ChatTurn, action.turn_id)
    claims, _ = chat.evidence_map(db, user, project_id)
    sources = {s.id: s for s in visible_sources(db, user, project_id)}
    if not chat.history_valid(turn.provenance, claims, sources, chat.access_signature(db, user, project_id)):
        raise HTTPException(409, "Evidence changed. Request a fresh action preview.")
    # Atomic transition serialises confirmations. Domain mutation uses the same transaction.
    claimed = db.execute(
        update(m.ChatAction)
        .where(m.ChatAction.id == action.id, m.ChatAction.status == "pending")
        .values(status="executing")
    )
    if claimed.rowcount != 1:
        raise HTTPException(409, "Action is already being confirmed.")
    from app.routers import sources as source_routes
    from app.routers import workspace

    try:
        if action.kind == "investigate":
            result = workspace.investigate(project_id, schemas.InvestigationCreate(), tasks, db, user)
            url = "/investigation"
        elif action.kind == "sync":
            result = source_routes.sync_connection(project_id, action.target_id, tasks, db, user)
            url = "/sources"
        elif action.kind == "start_capture":
            result = workspace.update_gap(
                project_id,
                action.target_id,
                schemas.GapUpdate(
                    status="in_progress", note="Knowledge capture started from a confirmed chat preview."
                ),
                db,
                user,
            )
            url = "/investigation"
        elif action.kind == "generate_handover":
            result = workspace.generate(project_id, action.target_id, db, user)
            url = "/handover"
        elif action.kind == "generate_exercises":
            result = workspace.exercises(project_id, action.target_id, db, user)
            url = "/validation"
        elif action.kind == "simulate":
            result = workspace.simulate(
                project_id, schemas.SimulationCreate(employee_id=action.target_id), db, user
            )
            url = "/risk"
        else:
            raise HTTPException(422, "Unsupported action.")
    except HTTPException:
        db.rollback()
        raise
    # Domain handlers commit the executing state with their mutation; replay cannot duplicate it.
    action.status = "completed"
    action.result = {"resource_id": result.get("id"), "status": result.get("status", "created"), "path": url}
    audit(db, user, project_id, "chat.action_confirmed", "chat_action", action.id, {"kind": action.kind})
    db.commit()
    return chat.action_json(action)
