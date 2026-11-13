# Round 3 form answers — review draft
Do not submit this draft unchanged. Confirm the exact Round 2 form promises,
event/team/participant details and final public PDF link. Dates and limitations
below are intentional. Do not classify pre-window work as event-window delivery.
## Product and repository
Product: https://inheria.onrender.com
Judge guide: https://inheria.onrender.com/demo
Repository: https://github.com/Gauravwakle96/INHERIA
Judge login instructions: Select Open judge workspace on the sign-in page. No
email/password or API key is required. The visitor enters as Rudransh and can
switch to Gaurav/Savinay within a separate expiring case-study workspace.
Final PDF Drive URL: pending.
## Complete list of working features
Organisation registration and password-based sign-in
Project membership and backend-enforced project/source permissions
One-click isolated judge workspace with scoped Gaurav/Savinay/Rudransh switching
Expiring single-use team invitations and recipient-chosen passwords
Independent knowledge access requests with source-level approval/rejection
PDF, DOCX, Markdown, TXT and JSON document ingestion
Secret quarantine and personal-contact redaction before indexing
Source versions, replacement, disconnection and deletion
GitHub REST connector for selected public repositories or encrypted PAT access
Bounded repository synchronisation with pagination, retries and health status
Source-linked project reconstruction and knowledge candidates
Supported English prose and structured-field extraction with exact quotations
Knowledge-gap investigation with targeted capture questions and persisted resume
Decision rationale, alternatives and conflicting-authority review
Evidence-backed relationship graph and source-change impact inspection
Targeted text interviews with independent review of employee explanations
Claim correction, approval, rejection and verification history
Hypothetical continuity/dependency/procedure risk reports
Versioned permission-filtered handover generation and human approval
Successor responsibility acceptance/rejection and ownership-transfer records
Practical walkthroughs with selected evidence, escalation and supervisor criteria
Required cited readiness prerequisites and blocked incomplete closure
Handover reopening, correction, reapproval and reassessment
Workspace-wide closed-handover summary and recorded participant contributions
Private persisted Digital Successor conversations with Low/High context budgets
Encrypted per-organisation provider settings and provider connection test
Cited Bynara chat replies with honest evidence-retrieval fallback on failure
Previewed role-checked project actions requiring confirmation
Permission-filtered audit and privacy views
Explainable source, verification, gap and acceptance metrics
Day/night themes, responsive navigation, keyboard support and reduced motion
This list describes features present in the final product, not their event-window
eligibility. GitHub snapshots and extraction are bounded. Live generated chat
requires the organisation's configured provider key; the anonymous judge workflow
works without one. No external cloud command or recovery execution is provided.
## Technical architecture and implementation summary
INHERIA uses React 19, TypeScript, Vite, TanStack Query, React Router, React Flow,
Lucide and Inter. A FastAPI modular monolith uses Pydantic validation, SQLAlchemy
and Alembic. Render Free hosts the Docker image containing the frontend and API;
Neon PostgreSQL stores the deployed data. SQLite is the local/test option.
Authorised source selection is followed by bounded parsing, privacy filtering,
versioned source/chunk storage and structured evidence extraction. Claims retain
exact quoted spans and source IDs/versions. Only authorised human reviewers can
verify knowledge. Handover generation filters verified claims by the recipient's
access; assignment, incoming acceptance, reviewed practical evidence and required
checks are separate state-machine gates. Source replacement/revocation removes
stale authority and requires revalidation. Persisted job checkpoints support
bounded investigation resume. Background work runs in-process; there is no
separate durable distributed worker in this version.
Document libraries include PyMuPDF and python-docx; GitHub is accessed through
REST/httpx rather than whole-repository cloning. Passwords use Argon2. Sessions
and invite/demo capabilities are opaque random tokens stored as hashes, with
HttpOnly cookies, origin checks and CSRF protection. Provider/connector secrets
use server-side Fernet encryption and are never returned to the frontend.
The optional chat provider interface supports Responses/Chat Completions and
provider-specific models. Live Bynara agnes-2.5-flash operation was recorded;
AgentRouter previously failed for the application. Low/High alters context and
output budgets, not a claimed Bynara reasoning parameter. External model output
is structurally validated against accessible citations. Citation structure does
not establish semantic correctness. No embeddings/pgvector or separate graph
database is used in this MVP. PyMuPDF's AGPL/commercial licence is disclosed.
The difficult boundary is maintaining permissions and evidence currency through
extraction, reports, conversations, ownership transfer and changed/deleted sources.
The UI cannot bypass those server-side checks or mark unsupported claims verified.
## Testing details and four-workstream delivery
See docs/four-workstream-acceptance.md and docs/verification.md for the final
run records. During this increment the full suite passed 187 tests with 88%
coverage, followed by focused checks for final source/staging boundaries. Final
full-run totals are recorded in verification.md. Ruff, frontend lint/typecheck/
production build and Python/Node dependency audits passed on executed checks.
Browser acceptance passed the complete judge handover, own-password invitation /
revocation and source permission editor reopen/readers. Responsive axe checks
were included; these are not independent usability or screen-reader audits.
A separate 60-document authored internal holdout (34 prose) passed 50/50 candidate
precision/recall, owners 20/20, rationale 14/14 and dependency endpoints 14/14.
Its initial run is frozen; labels are internal and implementation-informed, not
independent enterprise accuracy evidence. Original development fixtures remain.
## Improvement 1 — conditional on the submitted commitment
Conversational Digital Successor includes private saved history, encrypted org
settings, Low/High budgets, citations, confirmation-gated actions and fallback.
The promised 50 questions plus four paired calls were run against Bynara
agnes-2.5-flash. Only 9/50 primary requests returned valid provider responses;
41 fell back. Unsupported questions abstained 25/25 including fallback and 4/4
in the successful provider subset. All 19 cited primary responses had correct
source attribution; five generated project parts were supported in AI-assisted
review. The >=95% broad semantic citation target is not established from such
limited successful model coverage. Low/High measurements and upstream HTTP-200
error diagnostics are published. Provider reliability remains a known limit.
If the submitted promise is instead Secure Team Onboarding & Access Readiness,
it includes single-use/expiring invites, recipient passwords, source permission
editor, missing knowledge access requests, explicit handover access-readiness,
admin member/invite revocation, old grant removal and audited decisions. Scope
covers INHERIA knowledge, not AWS grants. Confirm actual submitted text; do not
claim a substitution was approved without evidence.
## Improvement 2 — Investigation and source-change intelligence
Delivered supported prose duty/rationale/dependency extraction, historical and
negated abstention, evidence-linked source/change impacts, deletion/revocation
revalidation and resumable source-version checkpoints. Fresh 60-document / 34
prose internal holdout met the 85% field / 90% precision targets. Existing ten
source-change/recovery cases and five interruption positions were exercised;
permission-loss and deletion cases are separately tested. General unrestricted
or multilingual prose accuracy and independent label audit remain limitations.
## Improvement 3 — Practical transfer validation and recovery
Delivered deployment/rollback/recovery rubrics, cited staging observation records,
separate documentation walkthroughs, current evidence/version checks, rejected
and reopened transfer recovery, acceptance, supervisor assessment history and
critical prerequisite closure gates. Twelve distinct positive/negative API role
journeys passed, including correction, rejection, reapproval, source revocation,
wrong actor and incomplete rubric. The complete browser handover passed.
No actual production, rollback or recovery command is executed by INHERIA.
## Final regression checks

198 backend tests passed with 90% line coverage; 14 judge/onboarding/source and
nine chat browser tests passed. Three affected source-change/revocation UI checks
passed again after the final backend change. Lint/typecheck/build, Python/Node
dependency audits and credential-pattern review passed in the documented scope.
See verification.md for bounded accessibility and test/setup limitations.

## What does not work yet
Bynara upstream chat reliability is poor in the measured run: 41/50 primary calls
used fallback. Fallback excerpts are useful evidence, not generated chat answers.
No claim of model-wide >=95% semantic citation correctness is made. Missing or
contradictory evidence needs human resolution; English pattern extraction has
bounded coverage. SSO/MFA, email invitation/password reset, OAuth/webhooks,
source-system permission mirroring, distributed workers, vector retrieval,
automated retention and enterprise governance remain unimplemented. Staging
observation authenticity and operational competence require authorised external
records and qualified supervisors. In-process work and free hosting are limited.
## Future roadmap
1. Reliable provider agreement/routing and independently labelled semantic
   evaluation; improve retrieval and unrestricted prose on fresh held-out data.
2. Verified identity, reset/invitation email, designed SSO/MFA and permission sync.
3. Durable workers, scheduled reviews/retention and operational monitoring/backups.
4. Real permissioned staging evidence and specialist review without production
   automation. No fabricated operations, company data or external feedback.
## Required confirmations still owned by the team leader
Exact event/team/leader/member details; the actual submitted Round 2 commitments;
truthful participant attribution; final PDF and publicly accessible Viewer link;
private-window link tests; accurate feature/improvement declaration; once-only
submission. The form has not been submitted by this work.
