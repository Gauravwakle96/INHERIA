# Final handover experience and completed judge workspace

The owner's authored ShopEase account has been copied into a credential-free
case-study snapshot. The sign-in page's **Open judge workspace** starts a separate
visitor tenant containing 51 sources, 81 knowledge records, the completed
Gaurav → Savinay handover, eight accepted responsibilities and eleven reviewed
walkthroughs. Existing source versions, quotations, ownership history and team
contributions are preserved. Visitors can inspect the populated graph immediately.

**Try a fresh handover** starts the original 13-source scenario with no approvals
or acceptance. Both modes expire and isolate visitor edits. No live account
lookup, password, session, API key, AI configuration, private conversation or
connected credential is used by the public demo. The public snapshot contains
reviewed authored case-study material, not actual Wipro/client records. Previous
approvals are recorded author-operated history, not decisions made by the visitor
or proof of independent human assessment. Unrelated draft transitions are omitted.

## Current continuation journey

Every project has a server-calculated next-step panel and an exact action link.
The stage follows sources, review, generation, approval, assignment, acceptance,
practical tasks, required checks and closure. **My continuation plan** gathers
current authorised responsibilities, procedures, open work and unanswered
questions. It does not treat an empty list as proof that no work exists.

The summary endpoint omits full source excerpts to keep polling bounded. Full
evidence is loaded in the continuation view. Source permissions still filter
all paths; restricted critical-gap titles are withheld with their source evidence.

## Readiness checks and recovery

Checks now have deployment, rollback, recovery, restore-test, knowledge-access,
backup-owner and follow-up categories. Current, verified, readable evidence is
required and conservative category patterns reject unrelated citations. A
restore-test record additionally identifies the isolated environment, run ID,
artifact and successful result. These are validation constraints, not semantic
proof or authenticity verification: a qualified supervisor must inspect relevance.

Current accessible unresolved critical gaps become required follow-up checks on
newly generated handovers. Each needs evidence for that gap, an active project
owner, due date and review note. This permits explicitly owned unresolved work;
the gap stays open and is never described as successfully recovered. Existing
closed handovers remain historical records and are not retroactively rewritten.

Duplicate acceptance and unchanged submitted/passed explanations return existing
records. A revision can be resubmitted for new review. UI approval carries the
reviewed version and stale tabs receive a conflict. Source lifecycle, source ACL,
membership and handover mutations use project-row locks on PostgreSQL. Expected
version is currently enforced for UI approval, not every edit. Actual concurrency
testing against PostgreSQL remains distinct from SQLite fixture testing.

Dependency simulations return a cited multi-step explanation path. Only current
verified, authorised relationships propagate impact; cycles terminate and absent
relationships remain unknown. These reports are hypothetical operational impact,
separate from source → claim → handover evidence invalidation.

## Executed evidence

- Completed/fresh judge browser tests check role switching, populated graph,
  ownership totals, refresh, isolation and 390/768/1440 layouts with axe.
- `test_restart_process.py` actually exits a worker after a committed checkpoint,
  starts a new API process, authenticates and resumes with no duplicate claims.
- `evaluation/run_local_operational_exercise.py` actually starts a local toy
  HTTP service, detects a broken release, rolls back, rejects an empty backup and
  verifies the correct SQLite restore. [Executed record](local-operational-exercise.json).
  This is neither cloud execution nor an INHERIA PostgreSQL disaster-recovery test.
  The downloadable record is available on the demo page for upload/review.
- The additional frozen 24-document prose challenge exposed real misses.
  [Original challenge result](diverse-prose-challenge-report.json) is preserved.
  After passive-owner, multiword-dependency, rationale and joint-owner fixes,
  [regression results](diverse-prose-regression-report.json) pass on these known
  cases. They are internal, implementation-informed regression evidence, not a
  fresh independent accuracy estimate. Joint owners remain explicitly uncertain.

Reproduction: `uv run pytest tests/test_completed_demo.py
tests/test_completion_hardening.py tests/test_dependency_paths.py
tests/test_restart_process.py` from `backend`; use the documented local services
for `npx playwright test tests/completed-demo.spec.ts tests/judge-demo.spec.ts`
from `frontend`. Run the local operational script only in a development checkout;
it creates temporary files and local toy processes, never production operations.

## Remaining external evidence

Independent usability sessions, independently labelled extraction evaluation,
actual cloud recovery and qualified human operational assessment are not claimed.
Final PDF/public sharing and accurate participant contribution details remain
submission tasks. The three submitted commitments remain onboarding/access,
investigation/change and practical validation/recovery; chatbot work is additional.
