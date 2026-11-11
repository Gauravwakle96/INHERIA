"""Conservative English prose patterns; every extracted field is an exact source span."""

import re


def prose_fields(paragraph, kind, users):
    data = {
        "extraction": "supported_prose_pattern",
        "owner_id": None,
        "backup_id": None,
        "component": "",
        "critical": False,
        "field_evidence": {},
    }
    # A named person's explicit duty statement is candidate evidence, not confirmation.
    for user in users:
        pattern = re.escape(user.name) + r"\s+(?:is responsible for|owns|maintains)\s+([^.!?\n]+)"
        match = re.search(pattern, paragraph, re.I)
        if match and not re.search(r"\b(?:might|may|could|possibly|not|no longer)\b", match.group(0), re.I):
            data["owner_id"] = user.id
            data["component"] = match.group(1).strip()
            data["field_evidence"]["owner_id"] = match.group(0)
            data["field_evidence"]["component"] = match.group(1)
            break
    if kind == "decision":
        reason = re.search(r"\b(?:because|since|in order to)\s+([^.!?\n]+)", paragraph, re.I)
        decision = re.search(
            r"\b(?:decided to|chose|selected)\s+([^.!?\n]+?)(?=\s+(?:because|since|in order to)\b|[.!?\n]|$)",
            paragraph,
            re.I,
        )
        if reason:
            data["rationale"] = reason.group(1).strip()
            data["field_evidence"]["rationale"] = reason.group(0)
        if decision:
            data["topic"] = decision.group(1).strip()
            data["field_evidence"]["topic"] = decision.group(0)
        alternative = re.search(r"\b(?:rejected|instead of)\s+([^.!?\n]+)", paragraph, re.I)
        if alternative:
            data["alternative"] = alternative.group(1).strip()
            data["field_evidence"]["alternative"] = alternative.group(0)
    if kind == "dependency":
        dependency = re.search(
            r"(?:^|[.!?]\s+)([A-Za-z0-9_-]+)\s+(?:depends on|requires)\s+([A-Za-z0-9_-]+)", paragraph, re.I
        )
        if dependency:
            data.update(from_component=dependency.group(1), to_component=dependency.group(2))
            data["field_evidence"]["dependency"] = dependency.group(0).strip()
    return data
