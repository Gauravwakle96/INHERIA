"""Load the reviewed, credential-free account case study into a new visitor tenant."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, inspect, select

from app import models as m

SNAPSHOT = Path(__file__).parent / "data" / "completed-shopease.json"
TABLES = [
    ("sources", m.Source),
    ("chunks", m.Chunk),
    ("claims", m.Claim),
    ("evidence", m.Evidence),
    ("gaps", m.Gap),
    ("transitions", m.Transition),
    ("transfers", m.Transfer),
    ("exercises", m.Exercise),
    ("audits", m.Audit),
]


def load_completed_demo(db, org, people, project):
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    ids = {snapshot["projects"][0]["id"]: project.id}
    ids.update({p["id"]: people[p["name"]].id for p in snapshot["people"]})
    for key, _ in TABLES:
        ids.update({row["id"]: m.new_id() for row in snapshot[key]})

    def remap(value):
        if isinstance(value, str):
            return ids.get(value, value)
        if isinstance(value, list):
            return [remap(item) for item in value]
        if isinstance(value, dict):
            return {ids.get(key, key): remap(item) for key, item in value.items()}
        return value

    for key, model in TABLES:
        columns = {prop.key: prop.columns[0] for prop in inspect(model).column_attrs}
        for original in snapshot[key]:
            row = remap(original)
            if "metadata" in row:
                row["source_metadata"] = row.pop("metadata")
            row["org_id"], row["project_id"] = org.id, project.id
            values = {key: value for key, value in row.items() if key in columns}
            for field, column in columns.items():
                if isinstance(column.type, DateTime) and isinstance(values.get(field), str):
                    values[field] = datetime.fromisoformat(values[field]).replace(tzinfo=None)
            db.add(model(**values))
        db.flush()
    # Reports retain the original evidence/version, while identifiers are visitor-local.
    # These are historical recorded actions, not approvals made by a visiting judge.
    project.name = "ShopEase · Completed DevOps handover"
    project.description = snapshot["projects"][0]["description"]
    # A replayed investigation must recognise existing evidence in the new tenant.
    for claim in db.scalars(select(m.Claim).where(m.Claim.project_id == project.id)):
        if not claim.data.get("fingerprint"):
            continue
        ref = db.scalar(select(m.Evidence).where(m.Evidence.claim_id == claim.id))
        if ref:
            fingerprint = hashlib.sha256(
                f"{ref.source_id}:{ref.source_version}:{ref.chunk_id}:{claim.kind}:{ref.quote}".encode()
            ).hexdigest()
            claim.data = {**claim.data, "fingerprint": fingerprint}
    db.flush()
    return snapshot["manifest"]
