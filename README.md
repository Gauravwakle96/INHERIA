# INHERIA

**People leave. Knowledge lives on.**

A functional technical knowledge-continuity application built around **Connect → Reconstruct → Verify → Review → Handover → Validate**. React/TypeScript frontend, FastAPI modular backend, SQLAlchemy models and Alembic migrations. PostgreSQL is the deployment database; SQLite supports local development.

**Live application:** https://inheria.onrender.com — create an account to start your own workspace. Render Free may take about a minute to wake after inactivity.

## Run locally

Free hosting instructions: [Render Free + Neon Free](docs/deployment.md).

Requirements: Python 3.13, uv, Node 24 and npm. Dependencies are locked.

Clone the repository, then run the commands from its checkout:

```powershell
git clone https://github.com/Gauravwakle96/INHERIA.git
cd INHERIA
```

```powershell
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8010
```

In a second terminal, start from the repository root:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8010/docs**. Interactive API calls require the HttpOnly session cookie and the `X-CSRF-Token` returned by sign-in or `/api/auth/me`.

Use the **Day / Night** button on the sign-in page or workspace topbar to switch palettes. Night is the default; the selected theme is saved in this browser, restored before the first render and synchronised across its tabs. Forms, dialogs, status badges and the knowledge graph follow the selection. Theme colors use the standard CSS `light-dark()` function; use a current browser.

System32 is the current authorised workspace and can cause Windows sandbox process-start failures. For future sessions, use a normal project directory. Copying the finished project outside this workspace requires filesystem approval; do not weaken sandbox settings.

## Try the complete scenario

## Digital Successor chat

Open **Digital successor** for private saved conversations, Low/High effort, evidence citations and confirmed project actions. An administrator can use **AI settings** to save an encrypted AgentRouter key, select `gpt-6.1-sol`, `gpt-6-astra` or `gpt-5.6-sol`, enable external processing and test the connection. Configure `INHERIA_TOKEN_ENCRYPTION_KEY` on the server first. No credential is returned to the browser or stored in frontend code.

The supplied key returned HTTP 401 on both official endpoints during verification. Live model replies remain unverified; failed requests show a warning and fall back to current verified excerpts. Low/High changes model context/output budgets; lexical fallback uses the existing retrieval method. See [chat setup and limits](docs/chat-integration-plan.md).

## Demonstration workflow

The local default enables the clearly labelled **NEXORA TECHNOLOGIES Demo workspace**. It contains five fictional employees, three repository fixtures, 75 commits, 12 pull requests, 25 issues and ten documents. These are fictional demonstration data, not real GitHub contributors or activity.

1. Sign in as **Maya Chen**. Inspect sources or upload a permitted PDF/DOCX/Markdown/TXT/JSON document. Public GitHub repository connections are also functional.
2. Run an investigation. Inspect evidence gaps, targeted interview questions, candidate responsibilities, decisions and source citations.
3. Sign in as **Alex Morgan** to record a targeted knowledge-capture answer. Employee explanations stay distinct from independent source evidence and require another authorised reviewer.
4. Return as Maya or **Priya Shah**. Approve or reject evidence candidates. Corrected explanations return to pending and require another reviewer. Confirm responsibility owners and backups explicitly.
5. Create a transition from Alex to **Jordan Lee**. Generate the verified handover, approve it, assign its responsibilities, and generate practical exercises.
6. Sign in as Jordan. Accept or reject assigned ownership, locate the cited documents, submit a safe test-environment walkthrough, and describe escalation conditions.
7. Sign in as Priya. Review each predefined exercise criterion and the submitted citations. Close the handover only when every responsibility is accepted and every exercise is supervisor-validated. Closure records the new owner with human-transfer provenance.

Practical tasks require human assessment. INHERIA does not run infrastructure commands, operate production systems or equate a quiz score with competence.

## Use your own organisation

Register an organisation, create a project, and use **Team → Add member** as an administrator to create authorised departing/incoming accounts. Account creation returns no passwords and sends no email. Share temporary credentials through your organisation's authorised process. Password reset, email invitations and enterprise SSO are not implemented.

Connect a public GitHub repository such as `fastapi/fastapi`, `django/django` or `prometheus/prometheus`. A connected repository is not a complete archive: bounded snapshots are honestly marked **partial**. Private GitHub PATs require a server-side Fernet encryption key. See [connector and dataset notes](docs/connectors-and-datasets.md).

## Configuration

See [backend/.env.example](backend/.env.example) for local settings. Environment values use the `INHERIA_` prefix. Copy to `backend/.env`; secret files are ignored. No Codex credentials or provider settings are read by the application.

| Setting | Purpose |
| --- | --- |
| `INHERIA_DATABASE_URL` | SQLite local URL or PostgreSQL + psycopg deployment URL |
| `INHERIA_ENVIRONMENT` | `development` or `production`; production requires PostgreSQL, HTTPS origins and disabled demo mode |
| `INHERIA_DEMO_MODE` | Enables only synthetic persona sign-ins; must be false in production |
| `INHERIA_ALLOWED_ORIGINS` | JSON array of exact permitted origins for state-changing requests |
| `INHERIA_TOKEN_ENCRYPTION_KEY` | Fernet key for private GitHub PATs; public access needs none |
| `INHERIA_LLM_ENABLED` | Explicit operator opt-in to external processing of authorised, privacy-filtered evidence |
| `INHERIA_LLM_BASE_URL` | HTTPS OpenAI-compatible Responses base URL; no embedded secrets or query credentials |
| `INHERIA_LLM_API_KEY` | Server-only provider key; never use a browser environment variable |
| `INHERIA_LLM_MODEL` | Explicit model selection; no automatic replacement of the operator's model |

Without LLM configuration, source-statement extraction and bounded evidence investigation use clearly labelled deterministic rules. The Digital Successor retrieves matching **verified** excerpts and abstains when evidence is insufficient. Optional LLM extraction validates structured outputs, exact quotations, authorised chunk IDs and usage budgets. Failure falls back to the rule engine. Live LLM quality has not been claimed from mocked tests.

## Checks

From `backend`:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest -q
uv run python -m app.evaluation
uvx pip-audit --path .venv/Lib/site-packages
```

From `frontend`:

```powershell
npm run lint
npm run typecheck
npm run build
npm audit
npm run test:e2e
```

See [verification results](docs/verification.md), [controlled evaluation](docs/evaluation-report.md), [architecture](docs/architecture.md), [API contract](API_CONTRACT.md) and [feature status](docs/feature-status.md). Automated evaluation uses an isolated labelled synthetic fixture. Its results are not general model accuracy or employee handover ground truth.

## Deployment

The [Dockerfile](Dockerfile) builds the frontend and API. [compose.yaml](compose.yaml) supplies PostgreSQL. Copy the root `.env.example` to `.env`, configure PostgreSQL credentials and the exact HTTPS application origin, then run `docker compose up --build`. Terminate TLS in an authorised reverse proxy and configure backups, disk encryption and monitoring. Production forbids demo persona access.

PyMuPDF is **AGPL/commercial**. Review AGPL obligations or obtain an Artifex commercial licence before proprietary distribution. The application is not represented as production-ready merely because local checks pass; deployment controls and enterprise requirements require environment-specific validation.
