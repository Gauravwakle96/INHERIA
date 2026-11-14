# Judge input and connector hardening

The finalisation checks use the actual submitted commitments: team access,
investigation/source-change intelligence and practical transfer/recovery. They
strengthen existing behaviour rather than adding another product direction.

## Fresh inputs and original results

72 new internally authored English prose documents were frozen in commit
`3496970` before execution. The first run exposed missed owner verbs, passive
dependencies, overlong component names, missing-rationale decisions and two
false candidates from ordinary personal tool use and a training example.

| Measure | Original first run | Known-case regression after general fixes |
| --- | --- | --- |
| Candidate precision | 40/42 (95.2%) | 56/56 (100%) |
| Candidate recall | 40/56 (71.4%) | 56/56 (100%) |
| Owner fields | 13/20 (65%) | 20/20 (100%) |
| Rationale fields | 8/16 (50%) | 16/16 (100%) |
| Dependency endpoints | 4/20 (20%) | 20/20 (100%) |

The [original report](judge-input-first-report.json) remains unchanged; the
[corrected report](judge-input-regression-report.json) is explicitly regression
data. Leading definite articles are removed from component identities. The
evaluator documents this normalisation and retains both raw expected/observed
values; it does not revise frozen labels or the original report.

General fixes recognise explicit managed/overseen/accountable duties, scoped
passive dependencies and additional causal wording. Instruction clauses such
as “before”, “during” and “when” no longer become part of a component name.
Training examples do not become current ownership. A proposal about future
documentation changes does not erase a separately stated current duty. A
disclaimer about the claim itself still prevents current-owner attribution.
Shared and unnamed ownership stays unresolved; missing rationale stays missing.

## Separate post-fix holdout

60 different prose documents with new names/systems were frozen in commit
`e0e5784` after fixes and before execution. No tuning was performed on this corpus.

- Candidate precision: 50/50 (100%); recall: 50/52 (96.2%).
- Owner accuracy: 19/20 (95%).
- Rationale accuracy: 11/12 (91.7%).
- Dependency endpoints: 20/20 (100%); exact quotations: 50/50 (100%).

This meets the submitted 90% candidate-precision and 85% field targets on the
bounded set. Two misses remain: a duty sentence with an unrelated denial of a
named individual, and a definite decision whose rationale contains “may”. The
conservative uncertainty guard skips these. See the
[unchanged first-run report](postfix-internal-first-report.json).

These labels were written by the implementing agent with knowledge of supported
patterns. They are not independently audited, multilingual or enterprise ground
truth. Exact quotation checks do not prove that the source itself is truthful.
New external documents still require human review.

## GitHub and duplicate requests

A real authenticated live sync of the team's own public INHERIA repository
imported 40 sources in about 11 seconds. An incremental resync imported zero new
sources in about 13 seconds. Both jobs reported completion, no partial result and
12 GitHub requests each. This is bounded recent activity and selected files,
not complete repository history. The temporary visitor-owned connection was
revoked and its encrypted token removed after verification. Existing private
accounts and provider settings were untouched. See
[live sync evidence](github-live-sync-verification.json).

Two overlapping sync requests previously could pass an unlocked pending-job
check. Enqueue now serialises on the project row and reloads current state. The
real PostgreSQL test confirms one queued job and one audit event, with a 409
response for the second request. Other source mutations retain the same lock
order and permission checks.

The Sources screen displays the saved connector warnings and import scope. A
completed job with a partial snapshot is clearly labelled partial. Authentication
and rate failures remain errors rather than successful connections. Only the
allowlisted warnings/scope are exposed; raw tokens and internal cache data stay
private.

## Responsive recovery and limits

The mobile connector test found an existing hidden table-header label positioned
outside its scroll container. Positioning the container keeps table scrolling
local and prevents document-wide overflow. The corrected screen passes bounded
390/768/1440-width and automated axe checks.

The latest Neon snapshot before these checks reported 4,486,615,813 bytes of a
5 GB allowance, leaving about 0.51 GB. Used quota cannot be reset by optimising.
Polling/quote-transfer reductions remain deployed; the live verification uses
only bounded visits. Free-hosting cold starts and quotas remain material limits.
No paid upgrade, extra database project or continuous keep-alive was introduced.

Actual unfamiliar-user sessions still need supplied observations. Automated
browser tests and authored role-switching are not five independent user sessions.
The final PDF remains deferred at the leader's request.

## Reproduction

From `backend`, evaluate a frozen corpus without credentials or application data:

```powershell
uv run python -c "from pathlib import Path; from app.acceptance_evaluation import evaluate_extraction; print(evaluate_extraction(Path('evaluation/postfix-internal-holdout.json'))['fields'])"
uv run pytest -q tests/test_judge_inputs.py tests/test_connectors.py
```

Set a loopback `INHERIA_TEST_POSTGRES_URL` ending in `_qa` for the actual duplicate
sync transaction test. The fixture creates/removes only its unique QA schema:

```powershell
uv run pytest -q tests/test_postgres_concurrency.py::test_pg_duplicate_sync_enqueues_one_job_and_reports_pending
```
