import json

import httpx
import pytest
from conftest import login

from app.llm import extract_candidates


def model_response(candidate):
    return {
        "output": [{"content": [{"type": "output_text", "text": json.dumps({"candidates": [candidate]})}]}]
    }


def test_stateless_model_payload_and_quote_validation(monkeypatch):
    quote = "Procedure: Follow the isolated deployment rehearsal steps."
    seen = {}

    def post(self, url, **kwargs):
        seen.update(kwargs["json"])
        candidate = {
            "kind": "procedure",
            "title": "Deployment rehearsal",
            "quote": quote,
            "chunk_id": "authorised",
        }
        return httpx.Response(200, json=model_response(candidate), request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.Client, "post", post)
    result = extract_candidates(
        "https://llm.example/v1", "fake-test-only", "configured-model", [{"id": "authorised", "text": quote}]
    )
    assert result[0].quote == quote
    assert seen["store"] is False
    assert "previous_response_id" not in seen and "conversation" not in seen
    assert seen["model"] == "configured-model"


@pytest.mark.parametrize(
    "candidate",
    [
        {
            "kind": "procedure",
            "title": "password=fictional-sensitive-value-12345",
            "quote": "Procedure: Follow the isolated deployment rehearsal steps.",
            "chunk_id": "authorised",
        },
        {
            "kind": "procedure",
            "title": "Invented",
            "quote": "This evidence is fabricated and not in the source.",
            "chunk_id": "authorised",
        },
        {
            "kind": "procedure",
            "title": "Unauthorised",
            "quote": "Procedure: Follow the isolated deployment rehearsal steps.",
            "chunk_id": "restricted",
        },
        {
            "kind": "made_up_kind",
            "title": "Invalid structure",
            "quote": "Procedure: Follow the isolated deployment rehearsal steps.",
            "chunk_id": "authorised",
        },
    ],
)
def test_model_unsupported_quotes_ids_and_schema_are_rejected(monkeypatch, candidate):
    monkeypatch.setattr(
        httpx.Client,
        "post",
        lambda self, url, **kwargs: httpx.Response(
            200, json=model_response(candidate), request=httpx.Request("POST", url)
        ),
    )
    with pytest.raises(ValueError):
        extract_candidates(
            "https://llm.example/v1",
            "fake-test-only",
            "configured-model",
            [{"id": "authorised", "text": "Procedure: Follow the isolated deployment rehearsal steps."}],
        )


def test_failed_llm_keeps_investigation_and_authoritative_knowledge_safe(workspace, monkeypatch):
    from app import llm
    from app.config import settings

    client, factory, project_id = workspace
    login(client)
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_api_key", "test-only")
    monkeypatch.setattr(
        llm,
        "extract_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Service unavailable")),
    )
    response = client.post(f"/api/projects/{project_id}/investigations", json={})
    assert response.status_code == 202
    runs = client.get(f"/api/projects/{project_id}/investigations").json()
    assert runs[0]["status"] == "completed"
    assert runs[0]["report"]["findings"]
    assert all(c["status"] == "pending" for c in client.get(f"/api/projects/{project_id}/claims").json())
