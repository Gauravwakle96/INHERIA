"""An explicit source saying a reason is missing must still produce a gap."""

from conftest import login

from app import models as m
from app.ingestion import ingest_document
from app.intelligence import find_gaps, reconstruct_project


def test_status_reason_missing_does_not_count_as_decision_rationale(workspace):
    client, factory, project_id = workspace
    actor = login(client)
    document = b"""# Decision: Extend operational retention
Status: reason missing
Context: the change has no supporting explanation in this source.
Alternative: Keep the existing period.

# Decision: Retain immutable release artifacts
Status: proposed
Rationale: An immutable digest allows the same package to be traced across environments.
Alternative: A mutable latest tag.
"""
    with factory() as db:
        user = db.get(m.User, actor["id"])
        ingest_document(db, user, project_id, filename="decision-review.md", content=document)
        reconstruct_project(db, user, project_id)
        findings = find_gaps(db, user, project_id)
        missing = [finding["title"] for finding in findings if finding["kind"] == "missing_rationale"]
        assert "Rationale missing: Extend operational retention" in missing
        assert "Rationale missing: Retain immutable release artifacts" not in missing
