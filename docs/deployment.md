# Free deployment: Render and Neon

Use one Render **Free** Docker web service and one Neon **Free** PostgreSQL project. The frontend and API share one HTTPS origin; no separate frontend deployment is needed. Paid LLM APIs are disabled by default.

Verified deployment: **https://inheria.onrender.com**. Service plan and database organisation plan were both confirmed free. See [public verification](deployment-verification.json).

## Deployment configuration

`render.yaml` describes the free service. Import this repository into Render or use its official CLI with an explicit `--plan free`. Choose Singapore for both services where available. Create the database in a verified Neon Free organisation; do not add Render PostgreSQL, whose free tier expires after 30 days.

Set server-side environment variables in Render:

| Variable | Value or purpose |
| --- | --- |
| `INHERIA_ENVIRONMENT` | `production` |
| `INHERIA_DEMO_MODE` | `false`; disables passwordless demo identities |
| `INHERIA_LLM_ENABLED` | `false`; deterministic evidence processing stays available |
| `INHERIA_DATABASE_URL` | Neon connection URL with `sslmode=require`; stored as a secret |
| `INHERIA_TOKEN_ENCRYPTION_KEY` | Fernet key for encrypted private GitHub tokens; generate once and keep stable |
| `INHERIA_ALLOWED_ORIGINS` | Optional JSON list of exact HTTPS origins for a custom domain |
| `PORT` | Injected by Render; local container default is `8010` |

When `INHERIA_ALLOWED_ORIGINS` is omitted, production uses Render's `RENDER_EXTERNAL_URL` as the exact trusted origin. Explicit overrides take precedence. Database URLs using `postgres://` or `postgresql://` are normalised to the installed SQLAlchemy psycopg v3 driver without dropping TLS parameters. Do not put database URLs, keys or provider tokens in frontend variables or committed files.

Generate the encryption key locally with `uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and save it directly in the hosting secret settings. Never rotate the key without a plan for already encrypted tokens.

The Docker image builds the frontend and copies its assets into `/app/frontend/dist`. FastAPI serves that directory and handles SPA deep links. Startup runs `alembic upgrade head`, then starts one Uvicorn worker on the platform port. The process runs as an unprivileged user. Render's health-check path is `/api/health`, which reports process state without querying PostgreSQL. `/api/ready` remains a genuine database check and returns a generic 503 if it cannot connect; use it for explicit readiness verification rather than continuous uptime probes. For services created outside Blueprint, change the actual Render service setting as well as `render.yaml`.

## Security and browser behaviour

Production requires PostgreSQL, HTTPS origins and disabled demo login. Session cookies are Secure, HttpOnly and SameSite=Strict; write requests retain origin and CSRF checks. The theme bootstrap is an external same-origin script. Script and style element policies remain restricted to `'self'`; `style-src-attr 'unsafe-inline'` permits React Flow's dynamic layout and React style attributes. This exception permits CSS attributes, not inline scripts or style elements. Source text is rendered through React escaping rather than injected HTML.

Register an account and create a project after deployment. No shared demonstration account is enabled on the public service. Public GitHub sources can be connected without a private token; private-source authentication requires the configured server encryption key.

During live QA, GitHub rejected anonymous synchronisation from Render's shared outbound IP because its rate limit was exhausted. INHERIA reported the failure and did not mark the integration connected successfully. Retry after GitHub's reset or configure your own least-privilege GitHub token in the repository connection form. Render/Neon login credentials are not reused as GitHub source credentials. Authenticated live source synchronisation was not verified in this deployment.

Later verification on 14 November established an authenticated live import of
the team's own public repository: 40 sources, followed by an incremental resync
with zero new imports. The temporary connection/token was revoked afterward.
This supersedes the earlier unverified authenticated path, while anonymous
shared-IP rate limits and bounded-history limits remain. See
[live sync evidence](github-live-sync-verification.json).

## Free-tier limitations

## Organisation chat configuration

The chat migration runs on normal Docker startup. `INHERIA_TOKEN_ENCRYPTION_KEY` encrypts organisation provider keys as well as GitHub tokens; keep it stable. No shared global chat key is installed. Administrators configure their own organisation through Digital successor → AI settings, explicitly enable processing and test a real request. Bynara uses `https://router.bynara.id/v1`, `agnes-2.5-flash` and Chat Completions. AgentRouter remains available for existing configurations. Provider fees and usage conditions remain separate from free hosting. One organisation's key is never shared with judge-demo visitors or other tenants. Slow calls show a waiting state; the server has a 110-second timeout and preserves conversations on provider failure.

## Hosting limits

Render Free currently sleeps after 15 idle minutes and may take about a minute to wake. Its 750 monthly instance hours are shared across services in the workspace. This workspace also contains other services, so total usage determines availability. Neon Free currently includes 100 CU-hours, 1 GB PostgreSQL storage and **5 GB public network transfer per project/month**; check [current limits](https://neon.com/docs/introduction/plans) before relying on them. Optional organisation AI keys incur their provider's separate fees; free hosting does not include unlimited AI requests.

### Database transfer budget

The 14 November 2026 control-plane snapshot reported 4,084,147,107 transferred bytes (approximately 4.08 GB of 5 GB) and 15,136 compute seconds (4.20 CU-hours of 100). The period ends at `2026-12-01T00:00:00Z`. These project API totals are indicative; Neon's dashboard billing meters remain authoritative. The warning concerned network transfer rather than compute. Optimisations cannot erase already used quota or guarantee unlimited judge traffic.

A later snapshot before the judge-input checks reported 4,486,615,813 bytes
(about 89.7% of 5 GB), leaving about 0.51 GB, and 16,031 compute seconds. This is
not a judge-capacity guarantee; traffic and delayed billing updates can change
remaining allowance. Keep live verification bounded and retain the runnable
installation path in the README.

- Completed/idle pages do not continuously poll claims, overview, gaps, connections or handover summaries. Running sync/investigation work uses a small active-status endpoint every five foreground seconds. Completion/failure refreshes dependent data once. Stale queries also refresh when the user returns to the window, navigates back or reloads; updates from another account are not continuously pushed to an idle tab.
- Exact evidence quote membership is checked inside PostgreSQL (`strpos`; SQLite uses `instr`). The application receives citation quotes, locations and validation results rather than every full source chunk on each claim/status request. Opening a source still retrieves its full authorised content.
- Claim rows used repeatedly by conflict checks and metrics are reused only within one SQLAlchemy session/transaction. Flush, commit, rollback and lock/reload boundaries invalidate this data. Permissions and source-version validation still run; there is no cross-user response cache.
- The actual Render liveness probe uses `/api/health`. Database readiness remains separately testable.

See [transfer verification](free-hosting-verification.json) for local PostgreSQL measurements and browser checks. Measure data transfer in the Neon console after real traffic; result-value bytes measured locally exclude wire/TLS overhead and are not a billing forecast. Avoid frequent live test loops or readiness-based keep-alive services. If the remaining free quota is insufficient, the supported options are to wait for renewal, reduce traffic or deliberately choose a suitable hosting plan; this deployment does not silently upgrade or create extra projects to bypass limits.

Render's filesystem is ephemeral. The application stores parsed sources and workflow data in PostgreSQL; do not depend on local container files for persistence. Jobs are bounded in-process tasks: a restart interrupts them and marks them failed for retry. Distributed workers, automatic backups/retention policies, SSO/MFA and enterprise source permission mirroring remain future work. Provider limits and billing rules can change.

## Verification and recovery

After a successful build, verify HTTPS `/api/ready`, `/api/health`, `/`, `/theme-init.js`, frontend assets and a SPA deep link. Check actual registration, authenticated API access, rejected cross-origin writes, both themes and graph rendering under the production CSP. Verify migrations against PostgreSQL rather than relying only on SQLite tests.

If deployment fails, inspect Render build/runtime logs without exposing secrets. Fix and push a commit, then redeploy. Redeploy a previous successful commit for an application rollback; do not downgrade a live database without reviewing migration and data impact. Disconnect/revoke private source tokens before removing their integration.

See [verification](verification.md) for recorded results and [feature status](feature-status.md) for material limitations.


## Isolated judge demo configuration

Keep `INHERIA_DEMO_MODE=false` in production. This disables the shared development
persona login. `INHERIA_JUDGE_DEMO_ENABLED=true` separately enables `/demo` and
per-visitor isolated workspaces. Defaults: `INHERIA_JUDGE_DEMO_HOURS=4` and
`INHERIA_JUDGE_DEMO_MAX_VISITS=40`. Visitors must retain both session and visitor
cookies to switch their three demo roles. Expired sessions are denied immediately;
expired demo tenants are removed on the next demo start, not by a scheduled job.
Capacity/rate failures are explicit. Do not upload confidential production sources
into a public demonstration environment. Invitations are manually shared one-time
links; email delivery, SSO and password recovery are not provided.

Migration `a73c9d21b004` adds demo visits, invitations and access requests without
replacing user/source/workflow tables. The Docker startup runs Alembic before
serving. Existing tokens/provider choices and project data must be preserved.
Document replacement and active-transition reopening are reversible versioned
workflow actions; closed ownership is revised through a follow-up transition.
