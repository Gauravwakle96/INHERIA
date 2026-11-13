"""Conservative English prose patterns; every extracted field is an exact source span."""

import re


def dependency_span(paragraph):
    return re.search(
        r"(?:^|[.!?]\s+|,\s*)([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,5})\s+"
        r"(?:depends on|requires|is dependent on)\s+"
        r"([A-Za-z0-9_-]+(?:\s+(?!for\b|with\b|to\b|because\b|and\b)[A-Za-z0-9_-]+){0,5})",
        paragraph,
        re.I,
    )


def named_duties(paragraph, users):
    matches = []
    for user in users:
        name = re.escape(user.name)
        direct = re.search(
            name + r"\s+(?:is responsible for|owns|maintains|handles|looks after)\s+([^.!?\n]+)",
            paragraph,
            re.I,
        )
        passive = re.search(
            r"([^.!?\n]+?)\s+(?:is|are)\s+(?:owned|maintained|handled) by\s+" + name, paragraph, re.I
        )
        titled = re.search(
            r"(?:^|[.!?]\s+)([^.!?\n]+?)\s+(?:coordinator|owner|maintainer) is\s+" + name, paragraph, re.I
        )
        match = direct or passive or titled
        if match:
            matches.append((user, match))
    # Joint duties remain a candidate with no falsely selected individual owner.
    joint = [u for u in users if re.search(re.escape(u.name), paragraph, re.I)]
    if len(joint) > 1 and re.search(
        r"\b(?:jointly own|joint owners|share responsibility)\b", paragraph, re.I
    ):
        return [(u, None) for u in joint]
    return matches


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
    duties = named_duties(paragraph, users)
    if len(duties) > 1:
        data["candidate_owner_ids"] = [user.id for user, _ in duties]
        data["ownership_uncertainty"] = (
            "Multiple people are stated; responsibility split requires human confirmation."
        )
    elif duties:
        user, match = duties[0]
        if match:
            data["owner_id"] = user.id
            data["component"] = match.group(1).strip()
            data["field_evidence"]["owner_id"] = match.group(0)
            data["field_evidence"]["component"] = match.group(1)
    if kind == "decision":
        reason = re.search(
            r"\b(?:because|since|in order to|due to|selected to|chosen to)\s+([^.!?\n]+)", paragraph, re.I
        )
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
        dependency = dependency_span(paragraph)
        if dependency:
            data.update(from_component=dependency.group(1), to_component=dependency.group(2))
            data["field_evidence"]["dependency"] = dependency.group(0).strip()
    return data
