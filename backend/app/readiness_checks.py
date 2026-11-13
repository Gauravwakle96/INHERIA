"""Typed evidence requirements. Human judgement remains explicit and necessary."""

import re

from fastapi import HTTPException

CATEGORIES = {
    "general": "General evidence review",
    "deployment": "Deployment procedure readiness",
    "rollback": "Rollback restrictions and checks",
    "recovery": "Recovery procedure readiness",
    "restore_test": "Recorded isolated restore test",
    "access": "INHERIA knowledge access",
    "backup_owner": "Backup ownership confirmation",
    "follow_up": "Owned and dated follow-up",
}
PATTERNS = {
    "deployment": [r"deploy|release|pipeline", r"approval|approv|health|precondition|check"],
    "rollback": [r"rollback", r"schema|migration|compatib|restriction|precondition|check"],
    "recovery": [r"recover|restore|backup", r"integrity|retention|restore|target|procedure"],
    "restore_test": [
        r"restore|recovery",
        r"staging|test environment|isolated",
        r"observation|test result|observed result",
        r"run id\s*:",
        r"artifact\s*:",
        r"result\s*:",
    ],
    "backup_owner": [r"backup|cover", r"owner|responsib|accept|confirm"],
    "follow_up": [r"owner|assigned|responsib|backup|follow.up|task"],
}


def validate_check(item, evidence, *, access_ready):
    category = item.get("category", "general")
    if category == "access" and not access_ready:
        raise HTTPException(422, "The incoming person must have all current handover knowledge access.")
    if category == "follow_up" and (not item.get("owner_id") or not item.get("due_date")):
        raise HTTPException(422, "A follow-up requires an accountable project member and due date.")
    patterns = PATTERNS.get(category, [])
    if patterns and not any(all(re.search(p, ref["quote"], re.I) for p in patterns) for ref in evidence):
        raise HTTPException(
            422,
            "Select evidence relevant to "
            + CATEGORIES[category]
            + ". Unrelated citations cannot confirm this check.",
        )
    if category == "restore_test" and any(
        re.search(
            r"no (?:actual |real )?(?:test|execution)|not (?:executed|performed)|outline only",
            e["quote"],
            re.I,
        )
        for e in evidence
    ):
        raise HTTPException(422, "An outline or unexecuted procedure is not a restore-test record.")
    if category == "restore_test" and not any(
        re.search(r"(?im)^result\s*:\s*(?:passed|success|successful)\b", e["quote"]) for e in evidence
    ):
        raise HTTPException(
            422, "A failed or incomplete restore record cannot confirm successful restore readiness."
        )


def check_matches(item, evidence, access_ready):
    try:
        validate_check(item, evidence, access_ready=access_ready)
        return True
    except HTTPException:
        return False
