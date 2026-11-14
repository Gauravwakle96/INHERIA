# INHERIA verification

Historical and current verification results are separated below. Results apply to the implemented MVP in this workspace; they do not certify an enterprise deployment.

## Judge-input, GitHub and duplicate-sync checks — 14 November 2026

Latest full backend suite: **239 passed**, no failures/skips, including **17 real
PostgreSQL cases**. This run did not collect coverage; the previous measured
baseline remains 89%. A final uncertainty guard passed 22 targeted boundary tests.
Exact-three acceptance passed **34/34**. The complete fresh-to-closed local UI
journey passed in about 203 seconds. Build/typecheck/lint, Python/Node dependency
audits and staged secret review passed in the recorded scope.

The 72-case challenge's original misses are preserved. General fixes recognise
more explicit duties and rationale, trim dependency instruction clauses and
reject training examples. A separate 60-document first run meets submitted
targets with two disclosed misses. See [input hardening](judge-input-hardening.md).

Real authenticated live GitHub import brought 40 sources into an isolated judge
workspace; incremental resync added zero new sources. The temporary connection
and token were revoked. Duplicate enqueue now serialises on the project row;
the PostgreSQL overlap test confirms one job and one audit record.

The browser run found mobile overflow from an absolutely positioned hidden
table-header label; fixing its scroll-container positioning passed the connector
scope/warnings test at 390/768/1440 pixels with bounded axe checks. Repeated local
QA also filled the unchanged 40-visit capacity, producing an explicit capacity
error. Only visits in the task-owned local QA database were expired; production
limits/data were unchanged. The corrected paced/capacity-clean browser rerun
passed **9/9** for readiness, warnings, source access and job completion/failure.

Human-user observations are still awaited; the [task pack](usability-task-pack.md)
is preparation, not claimed testing. Free-hosting capacity is finite (latest
pre-check snapshot roughly 0.51 GB transfer remaining). PDF remains deferred.
Commands/results, file hashes and initial failures are in
[upgrade verification](judge-upgrade-verification.json).

## Judge experience and closure recovery — 14 November 2026

The Handover page now shows measured acceptance, independent assessment, current
evidence coverage and blockers before closure. Missing, changed or unavailable
readiness disables Close; direct links lead to access, sources, practical review
and required checks. Team has a manual access refresh. The public guide explains
how to exercise the exact three submitted improvements.

Six focused browser tests passed: completed-role continuation/refresh, fresh
reconstruction, pre-closure blockers and links, changed/failed readiness with
retry, request-limit cooldown without immediate query retries, and invitation/
membership revocation. The full real local UI journey passed from fresh sources
through reconstruction, evidence inspection, approval, assignment, successor
acceptance, independent assessment, prerequisite review and closure; completion
was then inspected across project pages and themes. Build, typecheck/lint and full
Node dependency audit passed. Exact-three backend acceptance passed 34/34 again.

The final focused browser run passed 8/8: closure blockers, changed/unavailable
readiness, request-limit cooldown, public exact-three guide in both themes at
390/768/1440 pixels, external membership/source refresh, source permission
preservation and successful/failed job completion refresh. Readiness errors expose one recovery control so a second
refresh button cannot bypass the displayed cooldown. Team access refresh also
updates the source inventory and membership list.

Commands, result counts and tested file hashes are recorded in
[judge experience verification](judge-experience-verification.json).

Render confirmed application commit `4fecf31e03d9b8d71e859a09e5d19c0a6e33faaf`
live on the existing Free service. [CI run 43606135040](https://github.com/Gauravwakle96/INHERIA/actions/runs/43606135040)
passed both jobs. Live browser checks confirmed the exact-three public guide,
completed handover readiness (8/8 responsibilities, 11/11 supervisor tasks,
72/72 current handover records), Team refresh and fresh-entry blockers with
recovery links. No visible request error or desktop overflow was observed. See
[live verification](judge-closure-live-verification.json); targeted failure and
accessibility tests remain the separately recorded local checks.

An initial accelerated full journey reached closure but hit the unchanged
shared-IP request limit during subsequent rapid navigation and timed out. Query
retries now avoid terminal/permission/rate errors and 429 responses expose the
provider cooldown. The test honours the 60-second server budget between heavy
review/navigation loops; the complete rerun passed in 3.4 minutes. This does not
establish unlimited throughput. Targeted readiness/error timing uses explicit
browser fixtures; the full workflow uses the local backend.

The leader confirmed that the Round 2 baseline is allowed. PDF generation remains
deferred at their request. No unfamiliar-user outcome or participant contribution
has been invented. See [final product acceptance](final-product-readiness.md).

## Free-hosting transfer optimisation — 14 November 2026

The Neon project API reported 4.08 GB public network transfer against a 5 GB free allowance, while compute was about 4.2 CU-hours of 100. Existing account data, keys, provider choices and database resources were preserved. The actual Render service health setting was changed from `/api/ready` to `/api/health`; the service remains Free.

On an isolated local PostgreSQL 17.11 copy of the completed ShopEase case study, SQL result-value bytes fell from 5,193,333 to 857,254 for overview (83.5%), 3,258,382 to 691,133 for continuation summary (78.8%), and 1,270,737 to 238,710 for claims (81.2%). These measurements exclude wire/TLS overhead and establish reductions for this fixture, not monthly billed savings or future availability.

Browser checks verified zero project requests during a 12-second idle observation, active-job completion refresh, failure refresh followed by stopped polling, and completed/fresh handover state across refresh and role switching. Active/failure timing was controlled with labelled browser status fixtures; the fresh reconstruction and completed role-view checks used the real local backend. Backend tests cover SQLite/PostgreSQL quote matching, literal `%`/`_` characters, evidence version changes, role/project isolation and a liveness check that never queries the database. See [recorded results](free-hosting-verification.json).

The local full suite passed **232 tests, zero failures/skips, 89% line coverage**, including 16 real PostgreSQL cases. Six browser checks passed after correcting an old source-permissions test to use the fresh scenario. Final source/provider recheck cache invalidation passed another 43 boundary cases. Build, typecheck, lint, Python dependency audit, production npm audit and documentation links passed.

Render confirmed application commit `7b963d9bac82a873a6b33c80b509c8de7a8df968` live. One isolated live fresh-judge check returned 17 claims with citations, completed the real investigation, preserved progress after refresh, denied another project with 404, returned health 200 and made zero project requests during 12 idle seconds. No owner credentials, provider request or existing-account mutation was used. The project API still reported the original accumulated usage; billing telemetry can lag and used quota was not reset.

## Real PostgreSQL and additional prose challenge — 14 November 2026 IST

- **15/15 real PostgreSQL 17.11 transaction cases passed** using separate concurrent
  SQLAlchemy sessions in an owned loopback QA database. The harness verifies actual
  lock waits. Tests cover duplicate acceptance/assignment/closure, claim/handover
  approval, supervisor review, prerequisite updates, changed/revoked evidence,
  recipient access loss and invitation acceptance/revocation. Alembic reached
  `b19e47a2c805` in that separate QA database. No live-account data was changed.
- A retained stale invitation object reproduced a revocation race: an accepted
  invitation could be overwritten as revoked. The route now acquires the project
  lock and reloads current ORM state before permission and status checks. The
  regression test passes. CI now supplies an ephemeral PostgreSQL 17 service;
  these cases explicitly skip when a local test URL is absent.
- A **new 72-document all-prose internal challenge** first measured candidate
  precision 94.6%, recall 88.3%, owners 84.6%, rationales 75.0% and dependencies
  83.3%. [Original results](fresh-extraction-first-report.json) remain unchanged.
  General pattern fixes and conservative uncertainty handling now give known-case
  regression precision 100%, recall 98.3%, owners 92.3%, rationales 100% and
  dependencies 94.4%. Pronoun-only attribution, an uncertain shared lead and one
  exact endpoint-label match remain unresolved. This is implementation-authored,
  post-fix regression evidence, not independent held-out accuracy.
- All five extraction acceptance tests passed, including newly uploaded prose →
  investigation → exact source citations → authorised review → generated handover.
- Final code suite: **228 passed, 90% line coverage**, including all 15 PostgreSQL
  cases, with one existing FastAPI TestClient deprecation warning. Configured Ruff
  lint/format and locked-environment Python dependency audit passed. Frontend
  files are unchanged from the preceding verified build.
- Application commit `2d48c43` deployed successfully to Render. Live new prose
  produced four pending, exact-cited candidates, excluded an unconfirmed owner,
  preserved missing rationale, recovered the passive dependency direction and
  included all four reviewed claims in the generated handover. Completed judge
  entry, refresh, 51 sources/81 claims/92 graph nodes, restricted-source denial,
  successor continuation, visitor isolation and fresh reconstruction passed.
  Sign-in checks at 390/768/1440 pixels in both themes found no horizontal
  overflow or automated axe A/AA findings in that bounded scope. Health/readiness
  returned 200; the existing owner's closed handover remained closed. See
  [live check results](postgres-extraction-live-verification.json).
- GitHub [CI run 43531873055](https://github.com/Gauravwakle96/INHERIA/actions/runs/43531873055)
  passed both jobs for `2d48c43`: backend Ruff, complete pytest with the real
  PostgreSQL 17 service and pip-audit; frontend lint, typecheck, build and npm audit.

See [method, reproduction and limits](postgres-and-extraction-hardening.md) and
[transaction case results](postgres-concurrency-verification.json). Automated
tests do not establish that five unfamiliar people independently used or verified
the product; no individual usability outcomes have been supplied for this run.

## Completed judge workspace and final reliability checks — 14 November 2026 IST

The sign-in page now offers completed and fresh visitor workspaces. The sanitised
owner-account case study contains 51 sources and 81 claims, with eight accepted
responsibilities and eleven reviewed walkthroughs. It copies authored project
history, not account credentials, AI configuration or private conversations. The
owner account is unchanged. See [implementation and limits](completion-hardening.md).

- Earlier-tree backend suite: **210 passed, 90% line coverage**, with one existing
  TestClient deprecation warning. New coverage includes typed readiness checks,
  critical-gap follow-up gates, stale-version approval, duplicate acceptance,
  dependency paths/cycles/permissions, completed-tenant isolation and actual
  process exit/restart/resume without duplicate claims.
- The exact-three acceptance runner passed **34/34** again. It records the
  baseline commit plus dirty-tree status and test-file hashes, so the result
  does not incorrectly identify an uncommitted tree as the previous commit.
- The complete fresh browser journey passed through reconstruction, exact source
  inspection, claim approval, handover approval, successor acceptance, practical
  submissions, supervisor review, required follow-ups and closure. Completed
  role/graph/continuation/refresh checks passed at 390/768/1440 pixels with zero
  automated axe A/AA findings in that bounded run.
- Initial expanded browser checks exposed test synchronisation/locator errors:
  a prerequisite loop ran before data loaded, then the accountable-person field
  needed an explicit accessible name. Both were fixed and the full journey
  reran successfully. A later fresh-mode run encountered the correctly surfaced
  local demo-capacity limit after many test copies; it was rerun against a new
  owned QA database, preserving the production capacity limit.
- Frontend lint/typecheck/production build, configured Ruff lint/format,
  full npm audit and locked Python pip-audit passed. Changed/new text credential
  patterns were reviewed across 50 files, followed by a 54-file staged scan, with zero sensitive matches. Whitespace
  review passed; the public snapshot excludes real account email/passwords,
  sessions, provider keys and connection credentials.
- A separate 24-document prose challenge first produced 10/11 candidate precision,
  10/14 recall, 2/5 owner, 1/3 rationale and 1/4 dependency-field accuracy.
  The original report remains published. Broader passive-owner, multiword-
  dependency, rationale and uncertain joint-owner handling passes its now-known
  regression cases; this does not create a fresh independent accuracy claim.
- A separate local toy HTTP/SQLite exercise actually detected a broken release,
  rolled back to healthy v1, rejected an empty backup and restored three orders
  from the correct backup with integrity checks. The executed record is
  downloadable for source ingestion and human review. It is not cloud execution,
  an INHERIA PostgreSQL disaster-recovery test or a human competence assessment.

Source lifecycle, knowledge review, membership/source ACL and handover mutations
use PostgreSQL project-row locks; SQLite tests do not prove PostgreSQL race
behaviour. UI approval checks the expected version; other edits do not universally
use optimistic version checks. Independent usability feedback is still unrecorded.
Target deployment verification is recorded separately after release below.

## Live target acceptance — 14 November 2026 IST

**VERIFIED** on https://inheria.onrender.com at application commit
`c731e84b1f5b79c9e53527151057ae4effcfc3ca`. Render reports that exact commit
live; its GitHub CI completed successfully. HTTPS health/readiness returned 200,
and source-permission, access-readiness and membership-revocation APIs are present.
The existing PostgreSQL migration is `b19e47a2c805`; the original handover remains
closed and historical interview evidence lineage remains intact.

The anonymous browser verified completed direct entry, refresh, 51 sources,
81 claims, 92 graph nodes, Savinay's filtered 50 sources, denied restricted
citations, continuation plan, visitor isolation and a fresh reconstruction action.
Both themes at 390/768/1440 pixels had zero axe A/AA findings and no horizontal
overflow; no runtime error was observed. [Judge evidence](completed-judge-live-verification.json).

Read-only authenticated browser checks verified the original Gaurav, Savinay and
Rudransh accounts still see the completed 8/8 responsibility and 11/11 reviewed
handover. Thirteen routes, exact handover links, refresh and representative
mobile/day and desktop/night layouts passed. Recorded case-study contributions
remain separate for each person. [Preserved-account evidence](preserved-account-live-verification.json).
An initial 5-second refresh assertion was too short for the live page; the bounded
40-second check subsequently passed. An initial readiness probe timed out during
release; its retry returned 200. [Target and CI evidence](completion-target-verification.json).

These are executed target checks, not guaranteed hosting uptime, independent
usability research or operational competence. Free hosting cold starts and
bounded rule extraction remain material limitations. No provider key or original
account password is included in published evidence or copied to judge tenants.

## Confirmed three-improvement acceptance — 14 November 2026 IST

The team leader confirmed that Onboarding & Access Readiness, Investigation &
Source Changes, and Practical Transfer & Recovery were submitted; chat was not.
The exact scope is recorded in [the acceptance map](three-improvements-acceptance.md).
The dedicated existing-test runner passed **34/34**: seven onboarding, ten distinct
source-change/revocation inputs, five interruption positions and twelve role
journeys. The earlier ten changed-note variants alone were not counted as ten
distinct lifecycle scenarios. No application code, provider settings, account
data or historical reports changed for this scope reconciliation. One existing
TestClient deprecation warning remains. See [machine-readable results](three-improvements-tests.json).

## Four-workstream completion checks — 14 November 2026 IST

Chat model selection follow-up: an unconfigured/disabled workspace now shows
**AI not connected** instead of a disabled GPT option. Settings loading/failure
blocks premature chat/settings actions; failure supports retry. Demo setup copy
explains that owner organisation keys are not inherited. Saving the enabled
Bynara response synchronously updates the selector to `agnes-2.5-flash`; returning
focus also refreshes organisation settings. Three dedicated Playwright cases
passed loading/failure/retry, save/refresh/request-model/disconnect and mobile
demo isolation/axe. Frontend lint/typecheck/build passed; no backend or stored
credentials changed. Actual provider availability remains a separate limitation.

- Final full backend suite: **198 passed**, **90%** overall line coverage,
  including the interview lineage migration and transitive parent change tests.
  One existing FastAPI/Starlette TestClient deprecation warning remains.
- Migration checks upgraded/downgraded an empty owned SQLite database and
  upgraded a populated prior schema, checked repeated upgrade, preserved
  restricted ACLs/other metadata and downgraded only migration-owned metadata.
  An initial wrong table name in the new migration was caught and corrected.
- **14 Playwright tests passed** for judge entry/refresh/isolation, startup failure,
  duplicate clicks, six day/night layouts, the complete handover, invitation,
  source replacement, membership removal and the source reader editor. The three
  affected source/revocation UI cases passed again after final backend changes.
- **9 chat Playwright tests passed**: private saved conversations, abstention,
  confirmed actions, settings/model contract and six day/night 390/768/1440px
  layouts with keyboard/axe checks. The first attempt used a local QA setup with
  the suite's required development personas disabled; that attempt failed and was
  stopped. The isolated setup was corrected and all nine reran successfully.
  Production shared-persona access was never enabled. Provider contracts in these
  browser tests are mocked or use labelled retrieval, not paid availability proof.
- Ruff lint/format passed for application, tests and the new migration; frontend
  lint/typecheck/production build passed. Python locked-environment pip-audit and
  npm audit found no known vulnerabilities. A broader exploratory lint of all old
  migrations found one existing import-order issue in `e4058f85541c`; that immutable
  historical migration was preserved and the configured CI scope passes.
- Changed-text credential-pattern/private-secret scan: **44 files, zero hits**
  before final documentation. Whitespace review passed; private runners, credentials
  and negative tests use ignored `.local` files and isolated QA databases.
- Fresh internal extraction holdout: **60 documents / 34 prose**, candidate
  precision/recall **50/50**, owners **20/20**, rationale **14/14**, dependency
  endpoints **14/14**, exact quotes **50/50**. It met bounded internal targets,
  not independent enterprise accuracy. The frozen first-run report is preserved.
- Live chat holdout: **50 questions + 4 paired calls** against existing Bynara
  configuration, using only authored test sources. **9/50** primary calls produced
  usable provider answers; **41/50** fell back. Unsupported abstention **25/25**
  includes fallback; provider subset **4/4**. Source attribution **19/19** includes
  14 exact retrieval excerpts and five generated parts. Broad ≥95% semantic citation
  correctness is unestablished. Both effort benchmarks and four compact-context
  development probes remain disclosed in the acceptance report.

See [four-workstream acceptance](four-workstream-acceptance.md) for evaluation
methodology and product limits. Live acceptance for the new commit is recorded
after deployment; historical live checks below apply to their named commits.

Render deployed application `c2a6a7c8d48f4fbd0d84756d786c4a4e1e9f6f9a`
as `dep-dbrn3nh7lnhs73dftdd0`; GitHub
[CI 43501188846](https://github.com/Gauravwakle96/INHERIA/actions/runs/43501188846)
passed. Public `/api/health` and `/api/ready` returned 200; new access endpoints
are present. PostgreSQL upgraded to `b19e47a2c805`, backfilled eight historical
interviews and left zero eligible interviews without parent lineage.

Read-only private-account browser checks passed all twelve workspace routes,
refresh/exact handover navigation and Gaurav/Savinay/Rudransh views: one closed
handover, **8/8** accepted responsibilities, **11/11** reviewed walkthroughs.
Desktop/night and mobile/day had no observed overflow, axe violations or runtime
errors. Two fresh isolated public browser tests passed invitation/password/member
revocation, denied sources/chat access and source permission edit/reopen/role
restrictions. Private account data/provider choices remained unchanged.
See [live verification](four-workstream-live-verification.json).

The final anonymous live browser passed direct entry, refresh, role switching,
restricted-source denial and separate visitor isolation. All six day/night
390/768/1440px sign-in layouts passed overflow/axe checks with no runtime errors.
An earlier second-visitor navigation timed out waiting 30 seconds for network
idle. Its partial/failure evidence is recorded; the rerun used DOM-loaded
navigation and explicit UI readiness and passed. No app control was weakened.

## Direct judge access — 14 November 2026 IST

After receiving the actual Round 3 opening/deadline notice, sign-in gained
**Open judge workspace** for direct access as Rudransh, while preserving the
guide link and separate role accounts. Shared demo passwords are unnecessary.
Start is guarded against duplicate clicks; failure offers retry and disabled
demo configuration is explained. The existing isolated backend is reused.

- Three targeted Playwright tests passed: anonymous direct entry, persisted
  refresh, a second visitor isolated from the first, failed startup/retry,
  duplicate-click guard and disabled-demo explanation.
- Six day/night 390/768/1440px checks passed on both sign-in and the demo guide;
  no horizontal overflow or automated WCAG A/AA violations in those states.
- The full judge UI journey passed again after these frontend changes, including
  source reconstruction, review, handover, acceptance, assessment and closure.
- Frontend lint, typecheck, production build and npm audit passed. Backend tests
  were not rerun for this frontend-only increment; prior counts are below.
- Render deployed `256b341`; GitHub CI
  [43485832515](https://github.com/Gauravwakle96/INHERIA/actions/runs/43485832515)
  succeeded and the repository was verified public. Fresh anonymous browser
  checks passed direct entry, Rudransh role, refresh, thirteen coordinator/twelve
  incoming sources, restricted direct-access denial and separate visitor isolation.
  All six day/night layouts had no overflow or axe violations; no runtime errors.
  See [live evidence](judge-entry-live-verification.json).

These finalisation changes follow the announced opening. Earlier implementation
and tests keep their original dates. See round3-submission-checklist.md for the
exact commitments, known acceptance gaps and remaining submission information.

## Workspace completion verification — 13 November 2026 IST

- Full backend suite: **169 passed**, **90%** overall line coverage; the new
  completion module has 100% line coverage. Tests cover an incomplete project,
  closure, successor visibility, restricted contribution counts, cross-tenant
  denial and source deletion. One existing TestClient deprecation warning remains.
- Backend Ruff lint/format, frontend lint/typecheck/production build passed.
  Locked-environment pip-audit and npm audit found no known vulnerabilities.
  Changed-file secret scan and diff whitespace checks passed.
- Expanded real Playwright handover journey: **1 passed**. It completes review,
  approval, ownership acceptance, evidence walkthroughs and closure, then checks
  the completion banner across twelve workspace routes, the Savinay contribution
  card, exact transition navigation, day/night desktop/mobile layout and axe.
  No runtime errors, horizontal overflow or axe violations were observed in the
  tested states. Full historical browser counts below were not rerun here.
- Initial browser rehearsals exposed shared-IP rate limiting during rapid page
  reloads and a test that accidentally collapsed an already-open details panel.
  The final journey uses normal SPA navigation and explicit panel state; existing
  rate limits were preserved. A source-deletion completion edge case was fixed
  and is covered by the full backend suite.

Live acceptance: Render deployed `ebdfba9`; GitHub Actions run
[43411270856](https://github.com/Gauravwakle96/INHERIA/actions/runs/43411270856)
succeeded. The owner's ShopEase project, incoming Savinay and coordinator Rudransh
all show one completed version with **8/8** accepted responsibilities and **11/11**
reviewed walkthroughs. All twelve owner routes, exact handover link, refresh
persistence and desktop/night 1440px and mobile/day 390px checks passed, with no
runtime errors, overflow or axe violations. Evidence remains an author-operated
case study; no actual cloud execution is asserted. The final visual review also
removed rejected interview drafts from the team page's current ownership count.
See [workspace completion](workspace-completion.md) for the data and scope rules.

## Round 3 local verification — 11 November 2026 IST

These results supersede earlier implementation counts below. The isolated QA
backend uses a separate SQLite database and local frontend; no private production
account is mutated by the new browser rehearsal.

- Full backend suite: **164 passed**. Coverage includes existing auth/connector/
  ingestion/chat/workflow tests plus isolated judge tenants, expiry, legacy persona
  bypass prevention, single-use/revoked/expired invitations, existing-account role
  preservation, independent source grants, decision authority gates, prerequisite
  privacy, rejected tasks, ten source-change recovery scenarios and five interruption
  positions. One non-failing FastAPI/Starlette TestClient deprecation warning remains.
- Ruff lint and formatting; frontend lint/typecheck/production build passed.
- Python locked-environment pip-audit and npm audit: no known vulnerabilities.
- Fresh Alembic upgrade to `a73c9d21b004`, schema comparison and current revision
  checks passed on isolated SQLite. Migration has explicit stable schema definitions.
- Full local Playwright suite: **30 passed** (5.4 minutes), covering private chat,
  invitation/join, source replacement/impact, full judge handover/validation,
  registration, evidence upload/review, role restrictions, six day/night demo and
  six workspace sizes, keyboard/axe and recoverable network failure. The complete
  judge workflow passed after shared-IP pacing. No rate-limit control was weakened.
  Production smoke results are recorded separately below.
- Existing-schema upgrade with a sentinel organisation preserved its record and
  passed Alembic comparison. This used an isolated database; no live downgrade.
- Representative judge mobile/light and desktop/dark screenshots were visually
  inspected. Axe checks are bounded automated coverage, not accessibility certification.
  No prior judge-page baseline exists, so visual regression comparison is inconclusive.
- Evaluation expanded to **60 labelled documents**, including 23 prose cases:
  candidate precision **46/47**, recall **46/46**, exact citations **47/47**,
  unsupported-answer abstention **4/4**. One false positive remains. This corpus
  was used during rule development; no held-out split or independent annotation
  audit was performed. These are controlled rule measurements, not general AI
  accuracy or operational competence.

The browser caught a stale form default for incoming ownership; dialogs now mount
forms only when opened and assignments restrict the incoming choice to the actual
transition successor. A test encoding issue and a no-wait list iteration were also
corrected. A fast combined run hit the real shared-IP rate window; subsequent runs
pace the expensive journey without disabling limits. Existing validation tests
now explicitly assess new scenario criteria. See the evaluation report for misses,
feature-status for limits and round3-delivery for commitment reconciliation.

## Historical public deployment verification — 11 November 2026 IST

## Round 3 public deployment — 11 November 2026 IST

Application commit `d328adee7b3f4ce75f900383d09f2e4f301c17f0` deployed successfully
on the existing Render Free service, deployment `dep-dbpr6jtg1s2s7395bnl0`.
[GitHub CI](https://github.com/Gauravwakle96/INHERIA/actions/runs/42929730698)
completed successfully for backend and frontend.

HTTPS `/api/health`, `/api/ready`, `/api/auth/judge-demo`, `/demo` and `/` returned
200. Production shared persona login remains disabled; the separate judge demo
configuration reports enabled with a four-hour expiry. CSP, nosniff and same-origin
referrer headers were present. PostgreSQL migration is `a73c9d21b004`; Alembic
schema comparison passed. Before/after counts remained organisations 4, users 8,
projects 4, sources 57, claims 87 and transitions 6. This is a preservation check,
not a database integrity certification.

A fresh isolated public browser verified the sign-in Explore demo link and
enabled Start interactive demo control. All six day/night combinations at
390/768/1440px showed no horizontal overflow, no axe A/AA violations and no
uncaught runtime errors. Mobile/light and desktop/dark renders were inspected.
The normal unauthenticated `/auth/me` probe returns 401; this is expected, not a
failed sign-in. These checks stayed read-only: the full mutating demo journey was
tested on the separate local QA environment, not on private production data.
See [public verification JSON](round3-public-verification.json) and screenshots
under deployment-artifacts/judge-live-*.png. The provider quota/cold-start,
accessibility and practical-competence limitations remain unchanged.

## Earlier public deployment record

**https://inheria.onrender.com** is deployed as a Render **Free** Docker web service, with a dedicated Neon PostgreSQL project in a verified **Free** organisation. Docker build and runtime were verified on Render, which resolves the earlier local Docker-daemon verification gap. Alembic upgrade and schema consistency checks passed against the actual PostgreSQL database.

The deployment configuration commit was `877ed26ca596e18570f6818c1439310fb08ece8e`. After deployment changes, **116 backend tests passed**, Python lint/formatting passed, frontend lint/typecheck/build passed, and Python/npm dependency audits reported no known vulnerabilities. The previous 13 local Playwright tests remain recorded below; they were not rerun as a deployment suite. A separate Playwright run exercised the actual public service.

HTTPS health/readiness, frontend files and SPA routes returned successful responses. Registration/login, Secure HttpOnly SameSite cookies, rejected invalid CSRF/cross-origin writes and denied cross-tenant project/source reads passed against the public service. Demo persona access was disabled and optional paid LLM processing remained disabled.

An isolated fictional QA organisation completed document upload → reconstruction/investigation → evidence review → hypothetical unavailability analysis → approved handover → incoming owner acceptance → four exercise submissions → separate supervisor review → transition closure. Five evidence-backed claims produced nine graph entities and seven relationships before closure. These are fixture observations, not product benchmarks; the assessment records a safe walkthrough and does not prove operational competence or execute infrastructure.

The public browser run checked 11 application routes, day/night persistence, graph drag/selection and both themes at 390×844, 768×1024 and 1440×900. All six settled overview combinations had zero axe WCAG A/AA violations, no horizontal overflow and no CSP violations. No uncaught browser runtime error was observed. Representative mobile/day and desktop/night screenshots were visually inspected. This is bounded automated and visual coverage, not a complete accessibility or security audit.

Live anonymous GitHub synchronisation failed with GitHub's explicit rate-limit response from Render's shared outbound IP. The integration exposed the failure without fabricated source data. Connector unit/integration coverage passed, but successful authenticated public-host synchronisation remains unverified. Use a least-privilege source token or retry after the provider reset. No credential from Render/Neon authentication was repurposed.

The local DNS resolver briefly retained a failed lookup for the new domain. Public DNS-over-HTTPS resolved it correctly, and the controlled browser subsequently loaded the normal HTTPS URL. Automated QA used that authoritative address for this host while retaining hostname and certificate verification; no system DNS configuration was changed.

See [deployment evidence](deployment-verification.json), [public browser screenshots](deployment-artifacts/) and [free hosting setup/limits](deployment.md). Render Free can sleep after 15 idle minutes; monthly hours are shared with the workspace's other services. Enterprise controls and paid AI remain outside this deployment's verified scope.

## Local application and workflow

The React preview is running at http://127.0.0.1:5173 and the FastAPI service at http://127.0.0.1:8010. Final HTTP checks returned 200 for the frontend and API schema. The API exposes 42 documented paths at `/openapi.json`; interactive documentation is available at `/docs`.

The preview's reported failed request occurred while the backend was paused. Restoring the backend and reloading the controlled browser restored sign-in and the dashboard. Keep both processes running for the Vite preview: its `/api` requests depend on the FastAPI service.

The complete tested workflow covers source upload, evidence reconstruction, investigation, authorised human review, versioned handover approval, incoming responsibility acceptance, practical exercise submission and separate supervisor assessment. A fresh organisation, project and incoming member were also created through the actual interface and API.

## Automated results

## Private chat increment — 11 November 2026

Backend: 134 tests passed (including 18 chat tests), Ruff lint/format passed, Alembic metadata check passed, locked-environment pip-audit reported no known vulnerabilities. Frontend typecheck, lint and production build passed; npm audit reported zero vulnerabilities. Chat browser tests passed for private history reload, incoming-account isolation, abstention, confirmed investigation, model configuration and clearing unsaved credentials. Both themes at widths 390/768/1440 passed horizontal overflow and axe WCAG A/AA checks; representative desktop and mobile screenshots were inspected.

Initial combined browser runs exposed test sign-in timing and exhausted shared-IP rate limits. Tests now wait for successful sign-in, reuse their own chat test session and pace requests; production access controls remain unchanged. Final full browser suite: 21 passed in 2.7 minutes; final backend rerun: 134 passed. Staged credential scan found zero supplied-key or credential-pattern findings across 29 files. Updated OpenAPI contains 51 paths; Compose syntax passed. Docker daemon runtime was not rechecked locally. Backend tests mock model outputs to cover citations, source ACL/version/role changes, deletion, malformed output, secret detection, idempotency, action gates and safe provider errors; they do not establish live AI quality.

Actual stateless Responses requests to `https://agentrouter.org/v1/responses` and `https://ps.air-outer.com/v1/responses` returned HTTP 401 using the supplied credential. Live model replies remain blocked. No credentials, raw provider errors or prompts were printed. See [chat scope and limits](chat-integration-plan.md).

## Earlier baseline results

| Check | Recorded result |
| --- | --- |
| Backend pytest suite | 104 passed |
| Python lint and formatting | Ruff check passed; Python files formatted |
| Locked Python environment dependency audit | No known vulnerabilities reported |
| Database migration consistency | Local schema compared with ORM metadata: zero differences; database at Alembic head; `alembic check` passed |
| Frontend TypeScript check | Passed |
| Frontend lint | Passed with zero warnings |
| Frontend production build | Passed |
| npm dependency audit | Zero vulnerabilities reported |
| Playwright integration/browser suite | 13 passed in the final run, 1.5 minutes |
| UI evidence record checker | Passed; rendered inspection performed separately |
| Docker Compose configuration | Syntax validation passed |
| Docker image build and container runtime | Not verified: Docker Desktop daemon unavailable |

Backend tests exercise authentication and CSRF/origin checks, tenant/project/source permission boundaries, revocation and deletion, parsing and privacy filtering, duplicate/incremental ingestion, connector failures and retries, invalid/model-failed extraction, evidence review, simulations, transfer gates and supervisor validation. Tests use controlled fixtures and mocked external services where appropriate; the suite does not establish live provider quality.

The backend run emitted one upstream Starlette/httpx deprecation warning. It did not fail a test. Dependency audits report the advisory information available when run, rather than a guarantee that all defects are known.

## Browser and accessibility evidence

Settled overview screens were tested in both day and night modes at 390×844, 768×1024 and 1440×900. Automated axe WCAG 2/2.1 A and AA checks reported zero violations on all six theme/viewport combinations. Horizontal overflow checks passed. Browser tests exercised keyboard focus, mobile navigation, reduced motion, graph interaction and recovery from a controlled network failure.

The evidence record includes real loading, empty, error, pending review, verified success and permission-limited states. Controlled delays and request aborts were released to verify recovery; no fabricated API response was used for those captures. The mobile, tablet and desktop screenshots were inspected after loading completed. Visible environment labels read **Demo workspace** and **Demo repository**. Source quotations and fictional-data provenance remain identifiable.

See [the UI evidence record](../frontend/docs/ui-evidence.json) and its [screenshots](../frontend/docs/ui-artifacts/). Screenshots include persisted demo/QA activity; their counts are observations of that state, not fixed product metrics. These representative checks are not a full assistive-technology assessment of every page and content variant.

### Design-hook follow-up

The interview-question callout's decorative 2px side border was removed. Inter was retained because the user explicitly specified it; Impeccable recorded an `overused-font=inter` exception scoped only to `src/styles.css` in the frontend's shared `.impeccable/config.json`. No whole-file or whole-rule ignores were added.

The focused detector returned an empty finding list. The frontend production build passed again. Playwright verified the actual callout's computed side border is 0px, checked for horizontal overflow, and captured settled desktop and mobile renderings. Both captures were inspected; no unresolved findings from this two-item review remain. See [desktop](../frontend/docs/ui-artifacts/investigation-callout-1440.png) and [mobile](../frontend/docs/ui-artifacts/investigation-callout-390.png). The border-only change used focused checks; the later day/night changes were followed by the full browser suite recorded above.

### Day and night themes

The shared theme switch is available before sign-in and in the workspace topbar. Browser tests verified selection, keyboard activation, refresh persistence, retention after sign-in, matching graph colors and synchronization between tabs. The saved preference is applied before painting, including the native-control color scheme and browser theme color.

The existing night shades are retained; semantic light colors cover pages, form fields, callouts, status badges, evidence dialogs and graph controls. Day/night screenshots at all three target viewports, plus light sign-in and graph screenshots, were inspected. A production build and lint pass followed the theme changes. The final Impeccable scan returned no findings for the changed UI targets.

An earlier suite run passed 12 of 13 tests. Its upload returned HTTP 201 but the test searched before the initial source inventory completed. The test now waits for that initial load and asserts the upload response; the targeted rerun and final full 13-test run passed. Playwright emitted a non-failing NO_COLOR/FORCE_COLOR environment warning.

## Connector and extraction measurements

A live public GitHub smoke test against `fastapi/fastapi` retrieved 510 documents in 15 requests. The bounded result was correctly marked partial. Private-repository operation, OAuth app flows and webhooks were not established by this public test.

The reproducible, isolated synthetic evaluation recorded candidate precision 19/19, candidate recall 19/20, exact citations 19/19 and unsupported-answer abstention 4/4. Owner and rationale fields each scored 4/5; dependency endpoints scored 2/3. See [the evaluation report](evaluation-report.md) for fixture hashes, denominators and observed failures. These measurements describe deterministic extraction on a small labelled fixture, not general AI accuracy or real employee competence.

Optional LLM extraction was tested with mocked providers, including invalid outputs and service failure. Live LLM operation and quality remain dependent on explicitly configured operator credentials and evaluation against representative authorised data.

## Reproduce the checks

From `backend`:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest -q
uv run alembic current
uv run alembic check
uv run python -m app.evaluation
uvx pip-audit --path .venv/Lib/site-packages
```

From `frontend`, with both local services running:

```powershell
npm run typecheck
npm run lint
npm run build
npm audit
npm run test:e2e
node C:\Users\gaura\.codex\plugins\cache\ecc\ecc\2.2.3\skills\frontend-design-direction\scripts\check-evidence.js docs/ui-evidence.json
```

The final checker reported: `Evidence record complete; visual correctness still requires rendered inspection.` Browser screenshots were then reviewed. Browser tests create labelled QA sources, reviews and transitions in the configured development environment; use an isolated development database when repeating them.

From the project root, with Docker available:

```powershell
docker compose config --quiet
docker compose up --build
```

Only Compose syntax was verified here. Container startup, PostgreSQL behaviour in deployment, TLS, backups, restore procedures, monitoring and environment-specific enterprise controls remain deployment work.

## Material limitations

Before publication, the staged 108 files were reviewed: 88 text files and 20 rendered screenshots. Local databases, dependencies, test traces, compiled builds, secret environment files and developer hook caches are excluded. Targeted token/private-key/JWT pattern checks found one private-key marker in the ingestion test fixtures; cryptographic parsing confirmed it is not a valid private key. No real credential was identified in this targeted review. The staged whitespace check passed after removing redundant blank lines at three file endings. This review is not a substitute for a dedicated security audit.

- SSO/MFA, reset/invitation email, OAuth apps/webhooks, source-system permission mirroring, distributed workers, vector retrieval, automated retention and advanced governance are not represented as complete.
- Human review is required for authoritative knowledge and responsibility transfer. Practical validation records a supervisor assessment; it executes no infrastructure or production commands.
- Rule-based evidence reconstruction intentionally abstains or leaves gaps when free prose is unsupported. Scores describe measurable coverage and workflow state, not guaranteed continuity.
- PyMuPDF has AGPL/commercial licensing requirements; review them before proprietary distribution.
- The reported upstream Azure Responses resource-mismatch error is separate from INHERIA's local preview failure. Codex provider/model settings were preserved; gateway routing and a permanent upstream fix were not verified. See [the diagnosis](azure-responses-error.md).

See [feature status](feature-status.md) for the complete implemented, partial and postponed capability list, and [setup instructions](../README.md) to run the application.

Live deployment f5c0ce9 reached Render live status and PostgreSQL migrated to e4058f85541c. The supplied key was saved encrypted only for the verified Gaurav organisation. Its actual Render-side connection test returned a safe unvalidated-provider-response error; local Responses/Chat Completions probes returned 401. No successful live model call is claimed. Live fallback inspection exposed partial keyword matching, so related excerpts now stay explicitly labelled and known=false. The final follow-up backend suite passed 135 tests.

Live browser QA confirmed saved private history after reload, High effort, action previews, AI settings, HTTPS readiness and updated OpenAPI. Settled desktop/night and mobile/day renders passed axe checks with zero violations and no horizontal overflow or runtime errors. Initial contrast readings during the theme transition were resolved by waiting for the palette to settle with reduced motion. Screenshots were inspected. See chat-public-verification.json.

## Bynara chat integration — 12 November 2026

Bynara Chat Completions support was added for `agnes-2.5-flash`. The existing
AgentRouter settings remain supported. Keys remain organisation-scoped and
encrypted; changing provider endpoint requires a new key. Model choices follow
the provider and unknown overrides fail before storing a turn. Evidence,
permission revalidation, action confirmation and verified-retrieval fallback
continue to use the existing services.

Actual checks for this update:

- 168 backend tests passed, including Bynara wire format, Low/High output budgets,
  encrypted settings, admin permissions, provider-switch credential boundaries,
  cited replies, failure fallback and unsupported-model rejection.
- Nine chat browser tests passed: persistence, private history, confirmed actions,
  provider/model switching, the Bynara request contract, day/night layouts at
  390/768/1440 pixels and axe accessibility checks. The Bynara browser request
  contract uses a mock; it does not establish live provider availability.
- Ruff lint/format, frontend lint/typecheck/production build, npm audit and
  locked-environment Python dependency audit passed. ESLint now excludes ignored
  local probe scripts. One existing Starlette TestClient deprecation warning
  remains in the Python suite.
- Real provider smoke requests returned usable text (45.58 seconds) and a valid
  INHERIA structured answer that abstained without evidence (47.5 seconds).
  These individual requests do not establish general AI accuracy or uptime.

Live verification on 13 November 2026:

- Render confirmed application commit `8feea4192260e505810b9b33e781b035bd894708`
  live on the existing Free service. Both GitHub CI jobs succeeded; HTTPS
  readiness, frontend assets and the deployed API schema returned 200.
- The authorised administrator's ShopEase organisation was configured through
  the live HTTPS API. Readback confirmed Bynara, Chat Completions,
  `agnes-2.5-flash`, enabled processing and a saved key; no credential appeared
  in the settings response or input.
- The real application answered a ShopEase handover question using Bynara in
  66.402 seconds, with two supporting citations and separate `project`,
  `status`, `unknown` and `guidance` parts. The stored turn was completed,
  had no provider warning and persisted across a subsequent authenticated GET.
  The temporary probe conversation was deleted after inspection.
- Live browser model/settings readback passed. Desktop/night (1440 pixels) and
  mobile/day (390 pixels) had no horizontal overflow, axe violations or
  uncaught runtime errors. These representative checks are not a full
  accessibility audit. See [Bynara live evidence](bynara-live-verification.json).

Initial local DNS failures and request/browser timeouts interrupted verification.
A process-local public-DNS resolution fallback preserved the original HTTPS host
and certificate verification without changing system DNS or weakening security.
Subsequent authenticated inspection established that the original chat request
had completed and been saved. Do not infer provider failure solely from a client
timeout; inspect the stored conversation before retrying.

No supplied key is committed, included in public evidence or installed globally
for other tenants or judge-demo visitors. Provider retention and service limits
remain external conditions; `store=false` is not a provider confidentiality
guarantee. Live checks establish individual successful calls, not general AI
accuracy, guaranteed uptime or operational competence.
