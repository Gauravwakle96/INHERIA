import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from conftest import login
from cryptography.fernet import Fernet
from sqlalchemy import select

from app import chat, chat_provider
from app import models as m
from app.config import settings


def setup(workspace, monkeypatch, enabled=False):
    client, factory, pid = workspace
    actor = login(client)
    base = f"/api/projects/{pid}"
    key = Fernet.generate_key()
    monkeypatch.setattr(settings, "token_encryption_key", key.decode())
    r = client.put(
        base + "/ai-settings",
        json={"model": "gpt-6.1-sol", "api_key": "test-provider-credential", "enabled": enabled},
    )
    assert r.status_code == 200, r.text
    conv = client.post(base + "/chat/conversations").json()
    return client, factory, pid, actor, base, conv, key


def send(client, base, conv, text="How is billing-api deployed?", effort="low", request_id=None):
    return client.post(
        base + "/chat/conversations/" + conv["id"] + "/messages",
        json={"message": text, "effort": effort, "request_id": request_id or str(uuid4())},
    )


def verify_all(client, base):
    claims = client.get(base + "/claims").json()
    for c in claims:
        assert (
            client.post(
                base + "/claims/" + c["id"] + "/review",
                json={"action": "approve", "note": "Controlled fixture citation reviewed."},
            ).status_code
            == 200
        )
    return claims


def test_settings_encrypt_key_and_admin_only(workspace, monkeypatch):
    client, factory, _, _, base, _, key = setup(workspace, monkeypatch)
    response = client.get(base + "/ai-settings")
    assert response.json()["has_key"] and "credential" not in response.text
    with factory() as db:
        record = db.scalar(select(m.AIConfiguration))
        assert record.encrypted_key != "test-provider-credential"
        assert Fernet(key).decrypt(record.encrypted_key.encode()).decode() == "test-provider-credential"
    login(client, "Alex Morgan")
    assert client.put(base + "/ai-settings", json={"model": "gpt-6-astra"}).status_code == 403
    login(client)
    assert client.delete(base + "/ai-settings").status_code == 200
    assert not client.get(base + "/ai-settings").json()["has_key"]


def test_provider_endpoint_and_key_validation_dont_echo_secrets(workspace, monkeypatch):
    client, _, _, _, base, _, _ = setup(workspace, monkeypatch)
    response = client.put(
        base + "/ai-settings",
        json={
            "model": "gpt-6.1-sol",
            "base_url": "http://127.0.0.1/admin",
            "api_key": "invalid\nsecret-value",
        },
    )
    assert response.status_code == 422 and "secret-value" not in response.text
    monkeypatch.setattr(settings, "token_encryption_key", "")
    assert (
        client.put(
            base + "/ai-settings", json={"model": "gpt-6.1-sol", "api_key": "test-provider-credential"}
        ).status_code
        == 503
    )


def test_private_history_persists_and_is_not_shared(workspace, monkeypatch):
    client, _, _, _, base, conv, _ = setup(workspace, monkeypatch)
    result = send(client, base, conv, "What is annual company revenue?")
    assert result.status_code == 200, result.text
    turn = result.json()["turns"][0]
    assert turn["response"]["engine"] == "verified_retrieval" and not turn["response"]["known"]
    assert len(client.get(base + "/chat/conversations/" + conv["id"]).json()["turns"]) == 1
    login(client, "Alex Morgan")
    assert client.get(base + "/chat/conversations").json() == []
    assert client.get(base + "/chat/conversations/" + conv["id"]).status_code == 404
    assert send(client, base, conv).status_code == 404
    assert client.delete(base + "/chat/conversations/" + conv["id"]).status_code == 404


def test_chat_message_idempotency_and_secret_rejection(workspace, monkeypatch):
    client, _, _, _, base, conv, _ = setup(workspace, monkeypatch)
    rid = str(uuid4())
    assert send(client, base, conv, request_id=rid).status_code == 200
    assert len(send(client, base, conv, request_id=rid).json()["turns"]) == 1
    # This value is a labelled test pattern, not a usable provider key.
    secret_pattern = "sk-" + "fixture" * 10
    assert send(client, base, conv, "Please use this key " + secret_pattern).status_code == 422
    assert secret_pattern not in client.get(base + "/chat/conversations/" + conv["id"]).text


def test_valid_model_answer_uses_verified_citations_and_effort(workspace, monkeypatch):
    client, _, _, _, base, conv, _ = setup(workspace, monkeypatch, True)
    verify_all(client, base)
    calls = []

    def provider(config, key, message, effort, context, history):
        calls.append((config.model, effort, context, history))
        ref = context["evidence"][0]
        return chat_provider.Draft(
            parts=[chat_provider.Part(kind="project", text=ref["quote"], references=[ref["id"]])]
        ), {"total_tokens": 40}

    monkeypatch.setattr(chat, "call_provider", provider)
    response = client.post(
        base + "/chat/conversations/" + conv["id"] + "/messages",
        json={
            "message": "Explain deployment",
            "effort": "high",
            "model": "gpt-5.6-sol",
            "request_id": str(uuid4()),
        },
    )
    assert response.status_code == 200, response.text
    answer = response.json()["turns"][-1]["response"]
    assert answer["engine"] == "agentrouter" and answer["citations"] and answer["usage"]["total_tokens"] == 40
    assert calls[0][0:2] == ("gpt-5.6-sol", "high")
    assert [c["id"] for c in answer["citations"]] == [calls[0][2]["evidence"][0]["id"]]


@pytest.mark.parametrize("mode", ["bad_citation", "unrequested_action", "service_failure", "secret_output"])
def test_invalid_provider_output_falls_back_and_never_executes(workspace, monkeypatch, mode):
    client, _, _, _, base, conv, _ = setup(workspace, monkeypatch, True)

    def provider(*args):
        if mode == "service_failure":
            raise chat_provider.ProviderError("Provider quota unavailable.")
        if mode == "bad_citation":
            return chat_provider.Draft(
                parts=[chat_provider.Part(kind="project", text="Invented fact", references=["restricted-id"])]
            ), {}
        if mode == "secret_output":
            return chat_provider.Draft(
                parts=[chat_provider.Part(kind="guidance", text="sk-" + "fixture" * 10)]
            ), {}
        return chat_provider.Draft(
            parts=[chat_provider.Part(kind="unknown", text="No evidence")], action_ids=["investigate"]
        ), {}

    monkeypatch.setattr(chat, "call_provider", provider)
    result = send(client, base, conv, "What is annual company revenue?")
    assert result.status_code == 200, result.text
    reply = result.json()["turns"][-1]["response"]
    assert reply["engine"] == "verified_retrieval" and reply["warning"]
    assert reply["actions"] == [] and "Invented fact" not in result.text
    assert client.get(base + "/investigations").json() == []


def test_model_context_excludes_pending_and_restricted_sources(workspace, monkeypatch):
    client, factory, pid, actor, base, conv, _ = setup(workspace, monkeypatch, True)
    verify_all(client, base)
    with factory() as db:
        claim = db.scalar(select(m.Claim).where(m.Claim.project_id == pid))
        ref = db.scalar(select(m.Evidence).where(m.Evidence.claim_id == claim.id))
        source = db.get(m.Source, ref.source_id)
        source.acl = ["another-user"]
        restricted_text = source.name
        db.commit()

    def provider(config, key, message, effort, context, history):
        assert restricted_text not in json.dumps(context)
        return chat_provider.Draft(
            parts=[chat_provider.Part(kind="unknown", text="Insufficient Evidence")]
        ), {}

    monkeypatch.setattr(chat, "call_provider", provider)
    assert send(client, base, conv).status_code == 200


def test_stale_history_and_followup_are_withheld_and_deleted(workspace, monkeypatch):
    client, factory, pid, _, base, conv, _ = setup(workspace, monkeypatch, True)
    verify_all(client, base)
    observed = []

    def provider(config, key, message, effort, context, history):
        observed.append(history)
        ref = context["evidence"][0]
        return chat_provider.Draft(
            parts=[chat_provider.Part(kind="project", text="Cited project answer", references=[ref["id"]])]
        ), {}

    monkeypatch.setattr(chat, "call_provider", provider)
    assert send(client, base, conv).status_code == 200
    assert send(client, base, conv, "Explain that again").status_code == 200
    assert len(observed[1]) == 2
    with factory() as db:
        turn = db.scalar(select(m.ChatTurn).where(m.ChatTurn.conversation_id == conv["id"]))
        sid = next(iter(turn.provenance["sources"]))
        source = db.get(m.Source, sid)
        source.status = "revoked"
        db.commit()
    hidden = client.get(base + "/chat/conversations/" + conv["id"]).json()
    assert all(t["response"]["engine"] == "evidence_invalidated" for t in hidden["turns"])
    assert send(client, base, conv, "Ask using current evidence").status_code == 200
    assert observed[-1] == []
    assert client.delete(base + "/sources/" + sid).status_code == 200
    with factory() as db:
        old_turns = list(
            db.scalars(
                select(m.ChatTurn)
                .where(m.ChatTurn.conversation_id == conv["id"])
                .order_by(m.ChatTurn.created_at)
            )
        )
        assert all("Cited project answer" not in json.dumps(t.response) for t in old_turns[:2])


def test_action_preview_requires_confirmation_and_is_idempotent(workspace, monkeypatch):
    client, _, _, _, base, conv, _ = setup(workspace, monkeypatch)
    response = send(client, base, conv, "Investigate this project")
    assert response.status_code == 200, response.text
    action = response.json()["turns"][-1]["response"]["actions"][0]
    assert client.get(base + "/investigations").json() == []
    path = base + "/chat/actions/" + action["id"] + "/confirm"
    assert client.post(path, json={"confirm": False}).status_code == 422
    assert client.post(path, json={"confirm": True}).status_code == 200
    assert client.post(path, json={"confirm": True}).status_code == 200
    assert len(client.get(base + "/investigations").json()) == 1


def test_action_ownership_role_and_expiry_boundaries(workspace, monkeypatch):
    client, factory, _, _, base, conv, _ = setup(workspace, monkeypatch)
    response = client.post(
        base + "/chat/conversations/" + conv["id"] + "/actions", json={"kind": "investigate"}
    )
    action = response.json()["turns"][-1]["response"]["actions"][0]
    path = base + "/chat/actions/" + action["id"] + "/confirm"
    login(client, "Priya Shah")
    assert client.post(path, json={"confirm": True}).status_code == 404
    login(client, "Alex Morgan")
    assert client.get(base + "/chat/actions").json() == []
    assert client.post(path, json={"confirm": True}).status_code == 403
    login(client)
    with factory() as db:
        db.get(m.ChatAction, action["id"]).expires_at = m.utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.post(path, json={"confirm": True}).status_code == 409


def test_delete_conversation_removes_turns_and_previews(workspace, monkeypatch):
    client, factory, _, _, base, conv, _ = setup(workspace, monkeypatch)
    send(client, base, conv, "Investigate this project")
    assert client.delete(base + "/chat/conversations/" + conv["id"]).status_code == 200
    with factory() as db:
        assert db.scalar(select(m.ChatTurn)) is None and db.scalar(select(m.ChatAction)) is None


def test_role_change_hides_restricted_status_and_followup_history(workspace, monkeypatch):
    client, factory, pid, actor, base, conv, _ = setup(workspace, monkeypatch, True)
    seen_history = []

    def provider(config, key, message, effort, context, history):
        seen_history.append(history)
        if any(s["id"] == "status:integrations" for s in context["status"]):
            return chat_provider.Draft(
                parts=[
                    chat_provider.Part(
                        kind="status", text="Recent jobs require review.", references=["status:integrations"]
                    )
                ]
            ), {}
        return chat_provider.Draft(
            parts=[chat_provider.Part(kind="unknown", text="Insufficient Evidence")]
        ), {}

    monkeypatch.setattr(chat, "call_provider", provider)
    assert send(client, base, conv, "Which integrations failed?").status_code == 200
    with factory() as db:
        db.get(m.User, actor["id"]).role = "employee"
        member = db.scalar(
            select(m.Membership).where(m.Membership.project_id == pid, m.Membership.user_id == actor["id"])
        )
        member.role = "employee"
        db.commit()
    result = client.get(base + "/chat/conversations/" + conv["id"]).json()
    assert result["turns"][0]["response"]["engine"] == "evidence_invalidated"
    assert "Recent jobs require review" not in json.dumps(result)
    assert send(client, base, conv, "Explain again").status_code == 200
    assert seen_history[-1] == []


@pytest.mark.parametrize("protocol", ["responses", "chat_completions"])
def test_malformed_provider_shape_fails_safely(monkeypatch, protocol):
    real = httpx.Client
    monkeypatch.setattr(
        chat_provider.httpx,
        "Client",
        lambda **kw: real(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[])), **kw),
    )
    config = SimpleNamespace(base_url="https://agentrouter.org/v1", model="gpt-6.1-sol", protocol=protocol)
    with pytest.raises(chat_provider.ProviderError, match="validated"):
        chat_provider.call_provider(config, "fixture-value", "Hello", "low", {}, [])


def test_provider_wire_protocol_effort_and_safe_errors(monkeypatch):
    calls = []

    def handle(request):
        body = json.loads(request.content)
        calls.append(body)
        assert "previous_response_id" not in body and "conversation" not in body and not body["store"]
        draft = {
            "parts": [{"kind": "unknown", "text": "Insufficient Evidence", "references": []}],
            "action_ids": [],
        }
        return httpx.Response(
            200,
            json={
                "output": [{"content": [{"type": "output_text", "text": json.dumps(draft)}]}],
                "usage": {"total_tokens": 20, "secret": "do not return"},
            },
        )

    real = httpx.Client
    monkeypatch.setattr(
        chat_provider.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handle), **kw)
    )
    config = SimpleNamespace(base_url="https://agentrouter.org/v1", model="gpt-6.1-sol", protocol="responses")
    for effort in ["low", "high"]:
        _, usage = chat_provider.call_provider(config, "fixture-value", "Explain project", effort, {}, [])
        assert usage == {"total_tokens": 20}
    assert calls[0]["reasoning"]["effort"] == "low" and calls[1]["reasoning"]["effort"] == "high"
    assert calls[1]["max_output_tokens"] > calls[0]["max_output_tokens"]

    def denied(request):
        return httpx.Response(401, text="secret echoed by malicious provider")

    monkeypatch.setattr(
        chat_provider.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(denied), **kw)
    )
    with pytest.raises(chat_provider.ProviderError, match="401") as exc:
        chat_provider.call_provider(config, "fixture-value", "Hello", "low", {}, [])
    assert "malicious" not in str(exc.value)
