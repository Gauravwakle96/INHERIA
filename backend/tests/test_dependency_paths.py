from conftest import login
from sqlalchemy import select

from app import models as m
from app.continuity import simulation_report
from app.ingestion import ingest_document
from app.intelligence import reconstruct_project


def test_multihop_paths_include_exact_quotes_and_terminate_cycles(workspace):
    client, factory, pid = workspace
    actor = login(client)
    with factory() as db:
        user = db.get(m.User, actor["id"])
        source, _ = ingest_document(
            db,
            user,
            pid,
            filename="paths.md",
            content=b"Responsibility: Release ownership\nOwner: Alex Morgan\nSystem: release-pipeline\n\nDependency: release-pipeline -> registry\n\nDependency: registry -> network\n\nDependency: network -> registry",
        )
        reconstruct_project(db, user, pid, source_ids={source.id})
        for claim in db.scalars(select(m.Claim).where(m.Claim.project_id == pid)):
            claim.status = "verified"
        owner = db.scalar(select(m.User).where(m.User.name == "Alex Morgan"))
        report = simulation_report(db, user, pid, owner.id, "dependency_failure", "network")
        row = next(x for x in report["affected"] if x["title"] == "Release ownership")
        path = row["dependency_path"]
        assert len(path) == 2
        assert path[0]["from_component"] == "registry"
        assert path[1]["from_component"] == "release-pipeline"
        assert all(step["evidence"] and step["evidence"][0]["source_id"] == source.id for step in path)
        source.acl = [owner.id]
        db.flush()
        db.info.clear()
        denied = simulation_report(db, user, pid, owner.id, "dependency_failure", "network")
        assert not any(x["title"] == "Release ownership" for x in denied["affected"])
