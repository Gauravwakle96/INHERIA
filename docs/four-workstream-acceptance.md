# Four workstreams: measured acceptance, 14 November 2026

This records completed implementation and measured limitations. It does not
replace the three commitments actually submitted in Round 2. The saved PDF lists
the conversational successor, investigation/change intelligence and practical
transfer. Secure onboarding is additional unless the team confirms its submitted
replacement. Preserve the event-window baseline and historical submission.

| Workstream | Implemented acceptance | Remaining limit |
| --- | --- | --- |
| Conversational Digital Successor | Private history, encrypted org provider settings, Low/High budgets, verified source references, confirmation-gated actions, saved fallback; 50 fresh authored questions plus four paired effort calls assessed live. | Bynara returned valid app replies for 9/50 primary questions; 41/50 used fallback. General ≥95% semantic citation correctness is not established. External upstream availability is a material limitation. |
| Secure onboarding and access readiness | Single-use expiring invites, recipient passwords, independent access requests, current-source permission editor, admin project revocation, revoked old ACL grants/invites/requests, parent-source permission checks on derived copies, audit and explicit recipient handover access view. | No invitation email/SSO/MFA or automatic AWS access. Membership revocation keeps other projects and historical records; it is not organisation-wide offboarding. |
| Investigation and change intelligence | Explicit prose duty patterns, historical/negated abstention, decision reasons, dependencies, change impact/revalidation and atomic resume; fresh separate 60-document holdout with 34 prose documents. | English supported patterns only. Internal authored labels are implementation-informed; no independent enterprise accuracy study or general semantic extraction guarantee. |
| Practical transfer and recovery | Deployment, rollback and recovery rubrics; knowledge walkthrough versus cited staging observations; review history; rejection/reopen/reapproval; current evidence, acceptance and critical prerequisite closure gates; 12 distinct positive/negative API journeys. | Observation records require honest authorised authors and qualified supervisor review. App checks scope/currency and records assessment; it cannot verify that an external restore actually happened. No production commands executed. |

## Extraction evaluation

Development fixtures remain in `app.evaluation`; a fresh authored holdout was
frozen before its first run at `backend/evaluation/extraction-holdout.json`.
First-run results: 50/50 candidate precision and recall, owner 20/20, decision
rationale 14/14, dependency endpoints 14/14, exact source quotes 50/50. No
false positives or misses in this bounded set. Target 85% fields / 90% precision
was met on this internal set. It is now regression data; later tuning requires
a fresh evaluation set. It is not independent ground truth or general AI accuracy.

[Extraction report](extraction-holdout-report.json) contains labels, predictions,
denominators, hashes and limits. The old development report is preserved.

## Conversational assessment

[Live results](chat-live-evaluation.json) preserve every primary/paired response,
citations, effort, provider/model, prompt/corpus hashes, token counts and latency.
Only authored evidence was sent; no live project content or production database
was used for evaluation. A protected, existing organisation credential supplied
the authorised calls without changing provider settings or publishing the key.

Primary categories: supported 20, missing 10, stale 5, conflicting 5, restricted
10. There were 9/50 valid provider responses (3 supported, 2 stale, 4 restricted)
and 41 fallback responses. Diagnostics identified HTTP 200 envelopes containing
an `upstream_error` rather than an answer. The app now labels that safely.

Unsupported-question abstention was 25/25 including fallback, and 4/4 among the
successful provider subset. Conflicting/missing categories had no usable provider
reply, so do not claim those model behaviours comprehensively validated.
Source attribution passed 19/19 cited primary responses: 14 exact fallback
excerpts and five generated project parts. AI-assisted comparison found those
five parts supported by their quotes. That small subset does not establish the
promised ≥95% model-wide semantic citation target; independent review remains.

The canary literal appears in q46's **user question** and was repeated in its
abstention. This fails literal-absence screening but reveals no hidden source
content. Permission assessment must distinguish echoed input from source leakage.
Restricted evidence was excluded from retrieval/model input; boundary tests verify
direct access denial and source/membership revalidation separately.

Successful replies, including paired extras:

| Effort | Replies | Median | P90 | Provider-reported tokens total |
| --- | ---: | ---: | ---: | ---: |
| Low | 7 | 45.317 s | 56.521 s | 19,987 |
| High | 5 | 40.245 s | 45.224 s | 14,965 |

These are small, different successful subsets; High is not proven faster/cheaper.
Three of four paired extras succeeded, and corresponding initial calls often
failed, so a controlled paired latency comparison is inconclusive. Effort changes
context/output budgets; Bynara reasoning effort is not claimed. Outage testing
preserves conversation and provides labelled excerpts.

Four later [compact-context development probes](chat-compact-followup.json)
returned only one usable answer. They are not held-out results and did not justify
changing deployed evidence selection or declaring the upstream failures solved.

## Regression and browser acceptance

The final backend suite passed **198 tests with 90% coverage**, including migration,
parent-lineage and transitive source-change tests. One existing TestClient
deprecation warning remains. Python/Node dependency audits, configured lint,
typecheck/build and whitespace review passed on executed checks. See verification
for the preserved historical-migration import-order issue found outside CI scope.

Twelve separately parameterised transfer flows cover incoming acceptance, wrong
owner, missing citations, supervisor submission denial, self-assessment denial,
rejection, incomplete rubric, correction/reassessment, critical prerequisite
closure, reopen/reapproval, cited staging observation and observation revocation.
Existing tests cover ten source-change/recovery inputs, five interrupted-source
positions, deletion, actual source revocation and upstream permission failures.

Browser tests passed the complete judge journey, invitation/password/revocation
and source editor reopen/readers. Browser testing caught and fixed stale initial
ACL selection; permission forms now remount from current server readers.
Representative mobile/day and desktop/night axe checks accompany these journeys.
This is not a complete screen-reader audit or independent usability study.

The final browser runs passed 14 judge/onboarding/source tests and nine chat
tests. Three affected source-change/revocation cases passed again after the last
backend change. The first chat attempt lacked its local development personas;
after fixing the isolated QA setup all nine passed. No production persona access
was enabled and paid provider reliability is reported separately above.

Parent-lineage checks cover restriction, revocation, deletion and cycles. A
transitive interview-evidence regression verifies downstream impact, claim
invalidation and task revalidation. Source edits and access approvals share the
PostgreSQL project lock with membership revocation to prevent stale grants.
Migration `b19e47a2c805` backfills same-project historical interview parents;
populated and empty upgrade/downgrade checks run only on owned test databases.

## Reproduce

From `backend`: `uv run python -m app.acceptance_evaluation`,
`uv run python -m app.chat_evaluation` (explicitly offline), and `uv run pytest -q`.
For a paid live rerun set `INHERIA_EVALUATION_KEY` privately, then
`uv run python -m app.chat_evaluation --live`: 54 bounded Bynara calls, two
concurrent requests, plus a mocked outage check. It overwrites the output report;
archive previous results before rerunning and report subsequent tuning honestly.
Frontend: run the existing app, then `npx playwright test` for the relevant specs.
