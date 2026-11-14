"""Conservative English prose patterns; every extracted field is an exact source span."""

import re


def unconfirmed_context(paragraph):
    # A disclaimer about this claim invalidates it; an unrelated proposed update
    # must not erase an explicit current duty in an earlier sentence.
    if re.search(
        r"\b(?:training example|example (?:only|assignment)|not a current assignment)\b", paragraph, re.I
    ):
        return True
    return bool(
        re.search(
            r"\b(?:no longer|formerly|former team|superseded|hypothetical|"
            r"might|may|could|possibly|not confirmed|has not been decided|not official|"
            r"this (?:claim|statement|decision|duty|assignment) (?:is |has )?(?:no longer|not|superseded|proposed)|"
            r"not been confirmed|rumour|rumor)\b",
            paragraph,
            re.I,
        )
    )


def dependency_span(paragraph):
    if re.search(r"\b(?:developer|employee|customer|engineer)\s+(?:uses|calls)\b", paragraph, re.I):
        return None
    end_words = r"for|with|to|because|and|before|after|during|when|while|which"
    direct = re.search(
        r"(?:^|[.!?]\s+|,\s*)([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,5})\s+"
        r"(?:depends on|depends upon|requires|is dependent on|uses|relies on|relies upon|calls|connects to)\s+"
        rf"([A-Za-z0-9_-]+(?:\s+(?!(?:{end_words})\b)[A-Za-z0-9_-]+){{0,5}})",
        paragraph,
        re.I,
    )
    if direct:
        return direct
    return re.search(
        r"(?:^|[.!?]\s+)([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,5})\s+"
        rf"is (?:required|used) by\s+([A-Za-z0-9_-]+(?:\s+(?!(?:{end_words})\b)[A-Za-z0-9_-]+){{0,5}})",
        paragraph,
        re.I,
    )


def unasserted(sentence):
    """Reject explicit proposals, denials and unconfirmed statements, not all 'not'."""
    return bool(
        re.search(
            r"\b(?:no longer|does not|did not|not responsible|formerly|former team|superseded|"
            r"proposed|hypothetical|might|may|could|possibly|not confirmed|not been confirmed|"
            r"has not been decided|not official|rumour|rumor)\b|"
            r"\bnot (?:owned|maintained|handled|assigned)\b|"
            r"\bno (?:ownership|causal decision)\b",
            sentence,
            re.I,
        )
    )


def named_duties(paragraph, users):
    if unconfirmed_context(paragraph):
        return []
    sentences = [sentence for sentence in re.split(r"(?<=[.!?])\s+", paragraph) if not unasserted(sentence)]
    paragraph = " ".join(sentences)
    matches = []
    for user in users:
        name = r"(?<!\w)" + re.escape(user.name) + r"(?!\w)"
        direct = re.search(
            name
            + r"\s+(?:is responsible for|is accountable for|owns|maintains|handles|manages|oversees|looks after|provides ownership for)\s+([^.!?\n]+)",
            paragraph,
            re.I,
        )
        passive = re.search(
            r"([^.!?\n]+?)\s+(?:is|are)\s+(?:owned|maintained|handled|managed) by\s+" + name, paragraph, re.I
        )
        titled = re.search(
            r"(?:^|[.!?]\s+)([^.!?\n]+?)\s+(?:coordinator|owner|maintainer) is\s+" + name, paragraph, re.I
        )
        assigned = re.search(r"([^.!?\n]+?)\s+(?:is|are) assigned to\s+" + name, paragraph, re.I)
        belongs = re.search(r"\bresponsibility for\s+([^.!?\n]+?)\s+belongs to\s+" + name, paragraph, re.I)
        current = re.search(
            r"\b(?:the )?(?:current )?owner of\s+([^.!?\n]+?)\s+is\s+" + name, paragraph, re.I
        )
        match = direct or passive or titled or assigned or belongs or current
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
            r"\b(?:because|since|so that|in order to|due to|selected to|chosen to|chose [^.!?\n]+? to|adopted [^.!?\n]+? to|the reason was|the rationale was|motivated by)\s+([^.!?\n]+)",
            paragraph,
            re.I,
        )
        if not reason:
            reason = re.search(r"(?:^|[.!?]\s+)([^.!?\n]+?) drove the decision\b", paragraph, re.I)
        if not reason:
            reason = re.search(
                r"\b(?:selected|chose|adopted)\s+[^.!?\n]+?\s+as\s+([^.!?\n]+)", paragraph, re.I
            )
        decision = re.search(
            r"\b(?:decided to|chose|selected)\s+([^.!?\n]+?)(?=\s+(?:because|since|in order to)\b|[.!?\n]|$)",
            paragraph,
            re.I,
        )
        if reason and not re.search(
            r"\b(?:not recorded|not documented|unknown|unconfirmed|missing|not available)\b",
            reason.group(1),
            re.I,
        ):
            data["rationale"] = reason.group(1).strip()
            data["field_evidence"]["rationale"] = reason.group(0)
        elif reason:
            data["rationale_uncertainty"] = "Source explicitly states that decision rationale is unavailable."
        if decision:
            data["topic"] = decision.group(1).strip()
            data["field_evidence"]["topic"] = decision.group(0)
        alternative = re.search(r"\b(?:rejected|instead of)\s+([^.!?\n]+)", paragraph, re.I)
        if alternative:
            data["alternative"] = alternative.group(1).strip()
            data["field_evidence"]["alternative"] = alternative.group(0)
        if not data.get("rationale"):
            data.setdefault(
                "rationale_uncertainty", "No explicit decision rationale was found in this cited passage."
            )
    if kind == "dependency":
        dependency = dependency_span(paragraph)
        if dependency:
            origin, target = dependency.group(1), dependency.group(2)
            if re.search(r"\bis (?:required|used) by\b", dependency.group(0), re.I):
                origin, target = target, origin
            origin, target = (re.sub(r"^the\s+", "", value, flags=re.I) for value in (origin, target))
            data.update(from_component=origin, to_component=target)
            data["field_evidence"]["dependency"] = dependency.group(0).strip()
    return data
