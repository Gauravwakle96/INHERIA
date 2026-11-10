# INHERIA verification

Final local verification: 6 November 2026. Results apply to the implemented MVP in this workspace; they do not certify an enterprise deployment.

## Public deployment verification — 11 November 2026 IST

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
