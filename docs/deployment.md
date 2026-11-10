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

The Docker image builds the frontend and copies its assets into `/app/frontend/dist`. FastAPI serves that directory and handles SPA deep links. Startup runs `alembic upgrade head`, then starts one Uvicorn worker on the platform port. The process runs as an unprivileged user. `/api/health` reports process state; `/api/ready` checks the database and returns a generic 503 if it cannot connect.

## Security and browser behaviour

Production requires PostgreSQL, HTTPS origins and disabled demo login. Session cookies are Secure, HttpOnly and SameSite=Strict; write requests retain origin and CSRF checks. The theme bootstrap is an external same-origin script. Script and style element policies remain restricted to `'self'`; `style-src-attr 'unsafe-inline'` permits React Flow's dynamic layout and React style attributes. This exception permits CSS attributes, not inline scripts or style elements. Source text is rendered through React escaping rather than injected HTML.

Register an account and create a project after deployment. No shared demonstration account is enabled on the public service. Public GitHub sources can be connected without a private token; private-source authentication requires the configured server encryption key.

During live QA, GitHub rejected anonymous synchronisation from Render's shared outbound IP because its rate limit was exhausted. INHERIA reported the failure and did not mark the integration connected successfully. Retry after GitHub's reset or configure your own least-privilege GitHub token in the repository connection form. Render/Neon login credentials are not reused as GitHub source credentials. Authenticated live source synchronisation was not verified in this deployment.

## Free-tier limitations

Render Free currently sleeps after 15 idle minutes and may take about a minute to wake. Its 750 monthly instance hours are shared across services in the workspace. This workspace also contains other services, so total usage determines availability. Neon Free currently includes 100 CU-hours per project and 1 GB storage; check current provider limits before relying on them. No paid upgrade or paid LLM is configured.

Render's filesystem is ephemeral. The application stores parsed sources and workflow data in PostgreSQL; do not depend on local container files for persistence. Jobs are bounded in-process tasks: a restart interrupts them and marks them failed for retry. Distributed workers, automatic backups/retention policies, SSO/MFA and enterprise source permission mirroring remain future work. Provider limits and billing rules can change.

## Verification and recovery

After a successful build, verify HTTPS `/api/ready`, `/api/health`, `/`, `/theme-init.js`, frontend assets and a SPA deep link. Check actual registration, authenticated API access, rejected cross-origin writes, both themes and graph rendering under the production CSP. Verify migrations against PostgreSQL rather than relying only on SQLite tests.

If deployment fails, inspect Render build/runtime logs without exposing secrets. Fix and push a commit, then redeploy. Redeploy a previous successful commit for an application rollback; do not downgrade a live database without reviewing migration and data impact. Disconnect/revoke private source tokens before removing their integration.

See [verification](verification.md) for recorded results and [feature status](feature-status.md) for material limitations.
