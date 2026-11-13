# INHERIA verification

Historical and current verification results are separated below. Results apply to the implemented MVP in this workspace; they do not certify an enterprise deployment.

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
