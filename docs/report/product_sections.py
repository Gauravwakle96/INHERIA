"""Concise product documentation: current behaviour, roadmap and future scope."""


def build(
    p,
    tbl,
    box,
    evidence,
    link,
    journey,
    architecture,
    lifecycle,
    repo,
    base,
    guides_base,
    live,
):
    pages = []

    def page(title, subtitle, items):
        pages.append((title, subtitle, items))

    def jump(label, number):
        return f'<link href="#page-{number}" color="#087F80"><u>{label}</u></link>'

    page(
        "INHERIA · Product documentation",
        "TECHNICAL REFERENCE · OPERATING GUIDE · DEVELOPMENT ROADMAP",
        [
            p(
                "<b>People leave. Knowledge lives on.</b><br/>INHERIA turns authorised project sources into evidence-linked knowledge, controlled responsibility transfer and a reviewed continuation plan.",
                "lead",
            ),
            box(
                "Current product scope",
                "A deployed web application for technical teams, departing owners, incoming employees and authorised reviewers. The core journey works without a paid model. Human review, current evidence and source permissions govern knowledge and transfer state.",
            ),
            tbl(
                ["Documentation", "Page", "Purpose"],
                [
                    [
                        jump("Product workflow", 2),
                        "2",
                        "Users, supported inputs, human decisions and continuation.",
                    ],
                    [
                        jump("Architecture and data/API", 3),
                        "3–4",
                        "Components, infrastructure, persisted records and contracts.",
                    ],
                    [
                        jump("Security and evidence lifecycle", 5),
                        "5–6",
                        "Access boundaries, source lineage, jobs and invalidation.",
                    ],
                    [
                        jump("Installation and operations", 7),
                        "7–8",
                        "Local setup, production settings, failures and recovery.",
                    ],
                    [
                        jump("Quality and limitations", 9),
                        "9",
                        "Executed tests, bounded evaluation and known limits.",
                    ],
                    [
                        jump("Roadmap and release gates", 10),
                        "10–11",
                        "Ordered milestones, resources, dependencies and acceptance.",
                    ],
                    [
                        jump("Future scope", 12),
                        "12",
                        "Practical extensions after the current quality gates.",
                    ],
                    [
                        jump("Reference index", 13),
                        "13",
                        "Source documentation, evidence and maintenance rules.",
                    ],
                ],
                [0.35, 0.10, 0.55],
            ),
            p(
                link("Live application", live)
                + " · "
                + link("Public source repository", repo),
                "body",
            ),
            p(
                "Documentation distinguishes implemented behaviour, recorded verification and planned work. Evidence files remain linked to the verified source revision. Current roadmap and operating guides have separate links. This document describes the product; it makes no claim of unlimited capacity, autonomous production execution or certified employee competence.",
                "small",
            ),
        ],
    )

    page(
        "Product workflow and user responsibilities",
        "AUTHORISED INPUTS · REVIEWED KNOWLEDGE · CONTROLLED TRANSFER",
        [
            journey(),
            tbl(
                ["Stage", "Implemented behaviour", "Responsible decision"],
                [
                    [
                        "Connect",
                        "Upload PDF/DOCX/MD/TXT/JSON; connect public GitHub or authorised PAT access. Preserve source version, locator, timestamp and ACL.",
                        "User supplies authorised material; connection does not authorise unrestricted disclosure.",
                    ],
                    [
                        "Reconstruct",
                        "Bounded investigation extracts explicit duties, decisions/reasons, dependencies, procedures and unresolved work.",
                        "Candidates remain pending; incomplete or uncertain information is surfaced.",
                    ],
                    [
                        "Verify / review",
                        "Inspect exact quotes; approve, reject, correct or resolve conflicting authority.",
                        "Authorised reviewer; employee testimony cannot self-approve.",
                    ],
                    [
                        "Handover",
                        "Generate a current role/permission-filtered report; approve version and propose successor/backup ownership.",
                        "Coordinator reviews; assignment is separate from acceptance and access.",
                    ],
                    [
                        "Accept / validate",
                        "Successor accepts/rejects duty and submits cited scenario work; supervisor assesses criteria.",
                        "Participant cannot self-assess; manager cannot accept for the successor.",
                    ],
                    [
                        "Continue",
                        "Closure requires current evidence, acceptance, reviewed work and mandatory prerequisites.",
                        "Coordinator closes; successor receives duties, procedures, risks and next actions.",
                    ],
                ],
                [0.18, 0.47, 0.35],
            ),
            box(
                "Completion and unresolved work",
                "A completed knowledge transfer can retain open operational issues with accountable follow-up. Missing critical prerequisites block closure. Source changes can remove current readiness; historical ownership remains inspectable. Real technical execution and external cloud access are separate organisational procedures.",
            ),
            evidence("API_CONTRACT.md", "docs/feature-status.md"),
        ],
    )

    page(
        "Architecture and infrastructure",
        "COMPONENTS · DATA FLOW · DESIGN DECISIONS",
        [
            architecture(),
            tbl(
                ["Layer", "Implementation and reason"],
                [
                    [
                        "Frontend",
                        "React 19, TypeScript, Vite 7, React Query, React Router and React Flow. One responsive workspace and same-origin REST in production.",
                    ],
                    [
                        "Backend",
                        "Python/FastAPI/Pydantic modular monolith. Domain rules remain separate from UI, parsers and provider adapters.",
                    ],
                    [
                        "Database",
                        "SQLAlchemy 2 with PostgreSQL/psycopg in production; SQLite local default. Alembic migrations, UUIDs, foreign keys and duplicate constraints.",
                    ],
                    [
                        "Source processing",
                        "httpx GitHub REST, PyMuPDF and python-docx. Bounded parsing, privacy filtering, incremental sync and evidence locators.",
                    ],
                    [
                        "Deployment",
                        "Docker builds frontend/API; one Render Free HTTPS service plus Neon Free PostgreSQL. Frontend assets served by FastAPI.",
                    ],
                    [
                        "Optional model layer",
                        "Responses/Chat Completions adapters with opt-in credentials, structural validation and accessible citations. Lexical retrieval and rules support the core flow.",
                    ],
                ],
                [0.22, 0.78],
            ),
            p(
                "Consequential trade-off: in-process workers, lexical retrieval and relational graph records keep the bounded deployment simpler. There is no distributed queue, embeddings/vector store or separate graph database in this release. Scale and recovery work are explicit roadmap milestones.",
                "small",
            ),
            evidence(
                "docs/architecture.md",
                "backend/pyproject.toml",
                "frontend/package.json",
            ),
        ],
    )

    page(
        "Data model and API contracts",
        "PERSISTED STATE · EVIDENCE RECORDS · HTTP BOUNDARIES",
        [
            tbl(
                ["Domain", "Records and invariants"],
                [
                    [
                        "Identity / access",
                        "Organisations, users, memberships, sessions, invitations and access requests. Current tenant/project/source permissions precede content reads or writes.",
                    ],
                    [
                        "Source / knowledge",
                        "Connections, sources, versioned chunks, claims and evidence. Every citation identifies source, source version, chunk, locator and exact quote.",
                    ],
                    [
                        "Investigation / risk",
                        "Investigations, gaps, jobs and hypothetical simulations. Source checkpoints and fingerprints constrain repeat processing.",
                    ],
                    [
                        "Transfer / history",
                        "Transitions, transfers, exercises and audit events. Versioned approval, incoming acceptance and separate supervisor assessment.",
                    ],
                    [
                        "Optional conversation",
                        "Encrypted organisation settings, owner-only conversations/turns and expiring action previews. Credentials never returned to frontend.",
                    ],
                ],
                [0.27, 0.73],
            ),
            p("REST interface", "h2"),
            tbl(
                ["Boundary", "Representative route / contract"],
                [
                    [
                        "Authentication",
                        "POST /api/auth/register or /login; GET /api/auth/me returns user and CSRF token. Opaque session cookie authenticates subsequent requests.",
                    ],
                    [
                        "Project sources",
                        "Under /api/projects/{id}: /sources/upload, /connections/github, /connections/{id}/sync, /sources/{id}/access.",
                    ],
                    [
                        "Knowledge",
                        "/claims and /claims/{id}/review; /investigations and resume; /evidence/{source_id}, /graph and /gaps.",
                    ],
                    [
                        "Transfer",
                        "/transitions/{id}/generate, /approve, /assign, /readiness and /close; /transfers/{id}/respond; /exercises/{id}/submit and /review.",
                    ],
                    [
                        "Errors / state",
                        "ISO dates, UUID IDs, validated JSON payloads. 409 for conflicting state/active duplicate, 429 with cooldown; safe error text and request identifier where provided.",
                    ],
                ],
                [0.27, 0.73],
            ),
            box(
                "Review and metric meanings",
                "Claim states include pending, verified, rejected, invalidated and superseded. Confidence labels describe evidence strength, not predicted correctness. Acceptance = accepted/required duties; validation = passing reviewed/required tasks; coverage = current accessible/required records. Missing denominators return unavailable values.",
            ),
            p(
                "Interactive OpenAPI: local /docs. The complete request/response contract and route-specific guards are documented in API_CONTRACT.md; the table above is a navigation summary.",
                "small",
            ),
            evidence("API_CONTRACT.md", "backend/app/models.py", "docs/openapi.json"),
        ],
    )

    page(
        "Permissions, privacy and responsible design",
        "SECURITY CONTROLS · HUMAN AUTHORITY · ACCESSIBLE USE",
        [
            tbl(
                ["Boundary", "Implemented control", "Limit or operator duty"],
                [
                    [
                        "Identity",
                        "Argon2 passwords; hashed random sessions/invites; Secure/HttpOnly/SameSite cookies.",
                        "No verified email, reset email, SSO/MFA yet.",
                    ],
                    [
                        "Server mutations",
                        "Pydantic validation, parameterised ORM, current role checks, CSRF header and allowed Origin.",
                        "Restore valid auth; never weaken origin/access policy for recovery.",
                    ],
                    [
                        "Source disclosure",
                        "Tenant/project/source ACL checks apply to text, graph, reports, derived evidence and saved history.",
                        "Admin does not bypass source permission; upstream ACL mirroring absent.",
                    ],
                    [
                        "Sensitive input",
                        "Pattern-based secret quarantine and selected contact-PII redaction before indexing.",
                        "Bounded detection, not comprehensive DLP; false positives/negatives possible.",
                    ],
                    [
                        "Provider credentials",
                        "Server-side Fernet encryption; tokens excluded from responses/audit. Processing requires opt-in.",
                        "Stable encryption-key recovery; provider retention/contract review.",
                    ],
                    [
                        "Human decisions",
                        "No testimony self-approval, incoming-only acceptance and independent supervisor assessment.",
                        "Source statements and uploaded staging records require honest qualified review.",
                    ],
                    [
                        "Access lifecycle",
                        "Single-use expiring invites, current readers, independent access request decisions and revocation audit.",
                        "Manual invitation sharing; project removal is not external IAM offboarding.",
                    ],
                ],
                [0.21, 0.44, 0.35],
            ),
            p("Accessibility and product safeguards", "h2"),
            p(
                "Responsive navigation, day/night themes, keyboard controls, reduced-motion support and explicit empty/error/readiness states are implemented. Representative viewport and bounded axe checks are recorded. Full assistive-technology certification and unfamiliar-user outcomes are not claimed."
            ),
            box(
                "Responsible operation",
                "Missing evidence stays missing; simulations state assumptions. INHERIA transfers knowledge and records review—it executes no production deploy, rollback or restore. Retention settings are not automated deletion governance. Source-derived deletion exists; scheduled retention and enterprise controls remain future work.",
            ),
            evidence(
                "docs/architecture.md", "docs/feature-status.md", "docs/deployment.md"
            ),
        ],
    )

    page(
        "Evidence lifecycle and recoverable processing",
        "PROVENANCE · CURRENT AUTHORITY · JOB CONSISTENCY",
        [
            lifecycle(),
            tbl(
                ["Mechanism", "Implemented behaviour"],
                [
                    [
                        "Candidate evidence",
                        "Exact quotes identify source/chunk version and locator. Active reads check current permission, ready status, identity/version and quote membership.",
                    ],
                    [
                        "Replace / revoke / delete",
                        "Replacement retains history and invalidates dependent claims/assessments. Revocation removes authority; deletion purges indexed/derived text.",
                    ],
                    [
                        "Derived lineage",
                        "Parent evidence restrictions propagate through interview/ownership records and stored views. Missing/cyclic lineage denies access.",
                    ],
                    [
                        "Checkpoint / resume",
                        "Candidate writes and source-version checkpoint commit atomically. Authorised resume rechecks authority, skips unchanged checkpoints and deduplicates fingerprints.",
                    ],
                    [
                        "Concurrent state",
                        "Project-row locks and refreshed ORM state protect invitation accept/revoke and duplicate Sync. One active logical enqueue; conflicts remain explicit.",
                    ],
                    [
                        "Transfer recovery",
                        "Active handovers support corrections, regeneration, reapproval, reconfirmation and reassessment. Closed ownership changes use a follow-up transition.",
                    ],
                ],
                [0.27, 0.73],
            ),
            box(
                "Hardest engineering problem",
                "Permissions and evidence validity must remain current across derived knowledge, reports and assessments. Historic/cached content cannot retain authority after source or access changes. Transactional lock/reload boundaries and evidence-version checks prevent misleading approval and readiness.",
            ),
            p(
                "Workers are bounded/in-process; persisted progress supports controlled resume but is not a distributed scheduler. Hypothetical risk and measured evidence counts are separate from financial or operational predictions.",
                "small",
            ),
            evidence("docs/architecture.md", "docs/three-improvements-acceptance.md"),
        ],
    )

    page(
        "Installation and configuration",
        "LOCAL SETUP · PRODUCTION SETTINGS · OPTIONAL AI",
        [
            p(
                "Verified environment: Python 3.13, uv, Node 24 and npm; Python metadata supports 3.12+. Locked dependencies define installed versions. Use a normal project directory and preserve existing .env files.",
                "body",
            ),
            box(
                "PowerShell · repository and API",
                '<font face="Courier" size="8">git clone https://github.com/Gauravwakle96/INHERIA.git<br/>cd INHERIA/backend<br/>uv sync --frozen<br/>Copy-Item .env.example .env<br/>uv run alembic upgrade head<br/>uv run uvicorn app.main:app --host 127.0.0.1 --port 8010</font>',
            ),
            box(
                "Second terminal · frontend",
                '<font face="Courier" size="8">cd frontend<br/>npm ci<br/>npm run dev -- --host 127.0.0.1 --port 5173</font><br/>Run from the repository root. Open http://127.0.0.1:5173; backend documentation: http://127.0.0.1:8010/docs.',
            ),
            tbl(
                ["Variable", "Purpose"],
                [
                    [
                        "INHERIA_DATABASE_URL",
                        "SQLite local default; production PostgreSQL/psycopg with TLS.",
                    ],
                    [
                        "INHERIA_ENVIRONMENT",
                        "Production validates database/origin settings.",
                    ],
                    [
                        "INHERIA_TOKEN_ENCRYPTION_KEY",
                        "Stable server Fernet key for private PAT and organisation AI credentials.",
                    ],
                    [
                        "INHERIA_ALLOWED_ORIGINS",
                        "Exact permitted write origins; preserve CSRF and same-site policy.",
                    ],
                    [
                        "INHERIA_DEMO_MODE",
                        "Shared development fixture access; false in production.",
                    ],
                    [
                        "INHERIA_JUDGE_DEMO_ENABLED",
                        "Separate expiring visitor workspaces; four-hour / forty-visit defaults.",
                    ],
                    [
                        "INHERIA_LLM_ENABLED",
                        "Optional structured-extraction opt-in; false by default.",
                    ],
                ],
                [0.44, 0.56],
            ),
            p("Optional organisation AI", "h2"),
            p(
                "Administrator → Digital successor → AI settings. Bynara: https://router.bynara.id/v1, agnes-2.5-flash, Chat Completions. Existing AgentRouter choices remain. Enter your own key privately, enable and test. Low/High changes context/output budgets; keys stay encrypted server-side. Core source/review/transfer needs no model key. Provider usage may incur charges."
            ),
            evidence("README.md", "backend/.env.example", "docs/deployment.md"),
        ],
    )

    page(
        "Operating and troubleshooting guide",
        "HEALTH · RECOVERY · MIGRATIONS · RESOURCE LIMITS",
        [
            tbl(
                ["Condition", "Safe recovery"],
                [
                    [
                        "Cold start / hosting quota",
                        "Allow free service wake-up, then retry when offered. Monitor allowance; no keep-alive or extra-resource bypass.",
                    ],
                    [
                        "Missing access",
                        "Incoming person requests knowledge access; independent source reviewer decides. Cloud/IAM grants remain separate.",
                    ],
                    [
                        "Closure blocked",
                        "Follow readiness links; resolve required acceptance, independent tasks, evidence and prerequisites; refresh.",
                    ],
                    [
                        "Interrupted / duplicate work",
                        "Original authorised investigator resumes committed checkpoint. Wait on 409 existing job/state; do not loop enqueue.",
                    ],
                    [
                        "429 / failed sync",
                        "Honour cooldown; inspect safe auth/rate/partial warnings. Distinguish transient outage from permission loss.",
                    ],
                    [
                        "Changed / rejected knowledge",
                        "Inspect sources, correct and independently review; regenerate/reapprove active transfer and reassess.",
                    ],
                    [
                        "Optional provider failure",
                        "Saved conversation remains; labelled evidence retrieval is available. Check private provider/model settings.",
                    ],
                ],
                [0.31, 0.69],
            ),
            p("Deployment verification", "h2"),
            p(
                "Docker builds the UI and serves it with FastAPI. Startup upgrades Alembic migrations. Production uses PostgreSQL, HTTPS, stable encryption key and disabled shared development login. Check /api/health for process liveness and explicitly /api/ready for database readiness; verify SPA route, login, CSRF rejection, ingestion and restricted read."
            ),
            box(
                "Migration and rollback",
                "Review additive schema/data impact before release. Application rollback requires compatibility with the current schema. Database downgrade/restore is separately approved, never automatic. Preserve encryption-key recovery with backups. Current production restore objectives/drills are not claimed.",
            ),
            p("Persistence and limits", "h2"),
            p(
                "Application records live in PostgreSQL; Render local files are ephemeral. Jobs run in-process. Render/Neon Free have cold starts, storage/transfer/compute quotas and shared-IP limits; remaining allowance is not guaranteed. Idle pages avoid continuous polling; active status refreshes work completion/failure. No distributed capacity guarantee."
            ),
            evidence(
                "docs/operating-guide.md", "docs/deployment.md", "docs/architecture.md"
            ),
        ],
    )

    page(
        "Quality assurance and known limitations",
        "EXECUTED CHECKS · EVALUATION SCOPE · HONEST BOUNDARIES",
        [
            tbl(
                ["Verification", "Recorded result and scope"],
                [
                    [
                        "Backend / database",
                        "239 passed, zero failures/skips, including 17 real PostgreSQL cases. Previous coverage 89%; latest run did not collect coverage.",
                    ],
                    [
                        "Feature acceptance",
                        "34/34 journeys: 7 onboarding, 10 source-change/revoke, 5 interruption positions, 12 practical role flows. Isolated fixtures/mocked failures.",
                    ],
                    [
                        "UI / installation",
                        "9/9 focused browser checks; complete local fresh-to-closed journey ~203 seconds. Fresh archive install/migration/build/start/deep link passed.",
                    ],
                    [
                        "Connector / checks",
                        "Own public repository: 40 authenticated imports, zero new on incremental resync; token revoked. Lint/typecheck/build/audits and scoped secret scan passed.",
                    ],
                    [
                        "Separate internal evaluation",
                        "60 prose docs: precision 50/50, recall 50/52, owner 19/20, rationale 11/12, dependencies 20/20. Two conservative misses retained; internal labels are not independent enterprise evidence.",
                    ],
                ],
                [0.29, 0.71],
            ),
            p("Findings corrected", "h2"),
            p(
                "Fixed invitation accept/revoke stale-state and duplicate-sync races, mobile source-table overflow, immediate retry loops and missing connector warnings. Failed/missing readiness disables closure. Source changes invalidate dependent knowledge and assessment. Original extraction failures stay published separately from tuned regressions."
            ),
            p("Known limitations", "h2"),
            p(
                "Supported explicit English patterns; no broad multilingual/pronoun accuracy claim. Scanned PDFs require external OCR. GitHub imports selected recent history/files, without OAuth/webhooks. No email delivery/reset/SSO/MFA, distributed workers, automated retention, general workflow builder or multi-successor split. External observation authenticity and competence require qualified review."
            ),
            box(
                "Additional AI and usability boundaries",
                "Optional chat is provider-limited: one recorded 50-question run had nine valid replies and 41 labelled fallbacks. Citation structure alone does not establish semantic correctness. No independent unfamiliar-user study or complete screen-reader audit is claimed. Production command execution remains absent.",
            ),
            evidence(
                "docs/judge-upgrade-verification.json",
                "docs/postfix-internal-first-report.json",
                "docs/feature-status.md",
            ),
        ],
    )

    page(
        "Development roadmap and delivery order",
        "FOUR MILESTONES · RESOURCES · DEPENDENCIES · USER BENEFIT",
        [
            p(
                "Strengthen the current workflow before expanding integrations. Estimates below are small-team planning ranges, not release dates. All items are future work and separate from delivered capability.",
                "lead",
            ),
            tbl(
                [
                    "Milestone / estimate",
                    "Users and planned delivery",
                    "Prerequisite / release decision",
                ],
                [
                    [
                        "<b>M1 · Independent reconstruction</b><br/>P0 · 2–3 weeks",
                        "Technical reviewers: consented labels, category quality, shared owner/pronoun/rationale/dependency depth.",
                        "Permissioned data and two reviewers; frozen split before changes; publish precision, field accuracy, recall and misses.",
                    ],
                    [
                        "<b>M2 · Identity and onboarding</b><br/>P0 · 3–4 weeks",
                        "Admins/successors: verified email, invite delivery, password recovery, one approved identity provider and accessible role guidance.",
                        "Freeze ACL contract; approved email/identity access. Permission/replay/concurrency and consented unaided usability acceptance.",
                    ],
                    [
                        "<b>M3 · Durable jobs and recovery</b><br/>P1 · 3–4 weeks",
                        "Operators/larger teams: queue/worker, shared limits, freshness/retention and rehearsed application backup/restore.",
                        "Measure workload/budget; retain checkpoints. Test failures, acceptable data loss/recovery time (RPO/RTO) and capacity before a support promise.",
                    ],
                    [
                        "<b>M4 · Permissioned pilot</b><br/>P2 · 4–6 weeks per pilot",
                        "A real consenting team: one needed connector, specialist review and explicit domain/evidence requirements.",
                        "After M1–M3 gates; actual auth/sync/revocation/E2E and observed user benefit before “available” status.",
                    ],
                ],
                [0.24, 0.39, 0.37],
            ),
            p("Ownership and dependencies", "h2"),
            p(
                "Product coordination prioritises; data/AI owns evaluation; backend/security owns access; platform owns recovery; QA/UX owns observation and release evidence. These are proposed functional workstreams, not individual-delivery claims. Consent, specialist time, provider policy and hosting budget are explicit dependencies."
            ),
            box(
                "Scope and risk policy",
                "If independent data is unavailable, retain disclosed internal quality limits. Start with one supported identity/integration configuration. Keep bounded processing when queues exceed approved budget. Unnamed ownership stays unresolved. No milestone changes source permission or authorises production operations.",
            ),
            evidence("docs/roadmap.md"),
        ],
    )

    page(
        "Roadmap acceptance and release governance",
        "MEASURABLE GATES · FAILURE CASES · RELEASE ARTEFACTS",
        [
            tbl(
                ["Milestone", "Proposed acceptance and required evidence"],
                [
                    [
                        "M1 · Quality",
                        "Target ≥100 permissioned docs, ≥40 prose and ≥20 ambiguous/negative cases. Two independent reviewers, disagreement/adjudication, lineage-safe frozen split. ≥90% precision and ≥85% owner/rationale/dependency accuracy; publish recall/category failures. Valid spans and zero restricted disclosures in acceptance cases.",
                    ],
                    [
                        "M2 · Identity / use",
                        "Positive/negative verification/reset/invite/login/replay/expiry/revoke and PostgreSQL concurrent-use tests. No forbidden titles/text/history after access loss. ≥5 consented unfamiliar sessions across roles; proposed ≥4/5 unaided completion, fix/retest blockers. Publish assistive-technology scope.",
                    ],
                    [
                        "M3 · Reliability",
                        "Restart before/after checkpoint and duplicate delivery preserve one logical result. Revocation during retry never restores authority. Exhausted retry/cancel gives terminal state. Retention purges derivatives; owned test restore meets operator-approved RPO/RTO without tenant leakage.",
                    ],
                    [
                        "M3 · Capacity",
                        "Proposed initial profile: 10 concurrent users + 3 investigations over 30 minutes. Publish hardware, inputs, p95 latency, failures, memory/transfer. Choose limits after measurement; not achieved throughput.",
                    ],
                    [
                        "M4 · Pilot",
                        "Real authentication, incremental sync, source-loss/delete/retry and role-specific E2E tests. Consenting pilot confirms current owner, procedure and unresolved next action are understandable. Uploaded operational records require qualified review.",
                    ],
                ],
                [0.26, 0.74],
            ),
            p("Every milestone ships a review packet", "h2"),
            p(
                "1. User-visible scope and implemented/partial/unimplemented inventory.<br/>2. Updated API/schema/environment contract and additive migration/recovery plan.<br/>3. Permission/lifecycle/failure tests and original evaluation results.<br/>4. Actual user/accessibility observations appropriate to the change.<br/>5. Service/licence/cost disclosure, verified installation and known limitations."
            ),
            box(
                "Expansion gate",
                "A failed gate delays rollout rather than changing reported results. Future targets stay labelled planned. Preserve a useful non-provider/manual-review path. Platform restoration includes encryption-key recovery; database downgrade is never an automatic application rollback.",
            ),
            evidence("docs/roadmap.md", "docs/operating-guide.md"),
        ],
    )

    page(
        "Future scope with practical differentiation",
        "AFTER QUALITY GATES · LIMITED PILOTS · CONTROLLED EXPANSION",
        [
            tbl(
                [
                    "Order / users",
                    "Capability and user benefit",
                    "Requirement and boundary",
                ],
                [
                    [
                        "1 · Successor / supervisor",
                        "<b>Read-only staging CI evidence.</b> Begin with authorised GitHub Actions run references, commits, environments, timestamps/results linked to submissions.",
                        "Least privilege, safe logs, forged reference/missing artefact/revoke tests. CI success is not competence; no production command execution.",
                    ],
                    [
                        "2 · Manager / security",
                        "<b>Evidence packages.</b> Permission-filtered handover version, acceptance, assessment, open follow-ups and citation/version manifest for review.",
                        "Redaction, export permission, integrity and audit. Historic approval differs from current readiness; downloaded copies cannot be remotely revoked.",
                    ],
                    [
                        "3 · Split-duty teams",
                        "<b>Multi-successor coordination.</b> Separate deployment/monitoring/recovery owners, each with acceptance, access and validation.",
                        "After single-successor stability, extend schema/readiness; test partial completion, reassignment, revoke and concurrent changes.",
                    ],
                    [
                        "4 · DevOps / backend / IT",
                        "<b>Versioned templates.</b> Organisation-defined knowledge expectations, evidence, escalation and assessment criteria.",
                        "Admin/schema/version/migration controls and one consented pilot. Template/job title never proves a responsibility or validates knowledge.",
                    ],
                ],
                [0.23, 0.41, 0.36],
            ),
            p("Selection criteria and sequencing", "h2"),
            p(
                "Read-only staging evidence directly deepens practical verification first. Evidence packages improve review/accountability next. Multi-successor and templates follow demonstrated pilot demand. Scope/effort estimates require source access and schema impact analysis; these are not fixed-date promises."
            ),
            box(
                "Outside near-term scope",
                "Cross-company knowledge sharing, speculative predictive scores, historical digital-twin restoration and unrestricted autonomous remediation are not priorities. Any new connector needs real auth/sync/permission-loss and end-to-end evidence before being labelled connected. Confidential data never becomes shareable merely through integration.",
            ),
            evidence("docs/roadmap.md", "docs/feature-status.md"),
        ],
    )

    page(
        "Reference index and maintenance contract",
        "AUTHORITATIVE DOCUMENTS · VERIFIED EVIDENCE · UPDATE POLICY",
        [
            tbl(
                ["Reference", "Purpose"],
                [
                    [
                        link("README / setup", base + "README.md"),
                        "Product entry, local installation, optional key configuration and check commands.",
                    ],
                    [
                        link("Architecture", base + "docs/architecture.md"),
                        "Data flow, permission/evidence lifecycle, storage and processing choices.",
                    ],
                    [
                        link("API contract", base + "API_CONTRACT.md")
                        + " · "
                        + link("Models", base + "backend/app/models.py"),
                        "Request/response and actor guards; persisted relationships and constraints.",
                    ],
                    [
                        link("Deployment", base + "docs/deployment.md")
                        + " · "
                        + link(
                            "Operating guide", guides_base + "docs/operating-guide.md"
                        ),
                        "Docker/hosting, secrets, health, migration, expected failures and recovery.",
                    ],
                    [
                        link("Feature status", base + "docs/feature-status.md"),
                        "Implemented, partial, postponed and unimplemented scope.",
                    ],
                    [
                        link(
                            "Acceptance map",
                            base + "docs/three-improvements-acceptance.md",
                        ),
                        "Delivered onboarding/access, source-change investigation and practical transfer.",
                    ],
                    [
                        link("Verification", base + "docs/verification.md")
                        + " · "
                        + link(
                            "Latest suite",
                            base + "docs/judge-upgrade-verification.json",
                        ),
                        "Executed checks, corrections, original failures and current test scope.",
                    ],
                    [
                        link(
                            "Internal extraction report",
                            base + "docs/postfix-internal-first-report.json",
                        ),
                        "Exact denominators, preserved misses and label-independence limits.",
                    ],
                    [
                        link("Roadmap", guides_base + "docs/roadmap.md"),
                        "Milestone order, dependencies, effort, release gates and future scope.",
                    ],
                    [
                        link("Dependencies", base + "backend/uv.lock")
                        + " · "
                        + link("Frontend lock", base + "frontend/package-lock.json"),
                        "Reproducible dependencies; separate report tooling in docs/report.",
                    ],
                ],
                [0.36, 0.64],
            ),
            box(
                "Maintain together",
                "Update README, API/schema/environment, architecture, feature status, verification, operations and roadmap with each release. Document checks actually run and limits. Preserve original evaluation failures and source authority. Planned capabilities never become claimed results before implementation and measurement.",
            ),
            p("External services and licences", "h2"),
            p(
                "GitHub, Render, Neon and optional model providers have separate access, usage and pricing conditions. PyMuPDF uses AGPL/commercial licensing; review deployment/distribution obligations. Inter and report Bitstream Vera fonts retain their redistribution licences. Provider retention/security agreement requires operator review."
            ),
            p(
                "Document scope: current bounded implementation and proposed development. PDF diagrams are original vectors; no demonstration scenario is presented. The report rebuild and text/layout/link checks are documented under docs/report. Public test evidence is revision-linked; roadmap and operating guides are current-version references.",
                "small",
            ),
        ],
    )
    return pages
