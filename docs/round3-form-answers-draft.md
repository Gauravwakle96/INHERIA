# Round 3 form answers — review draft

The three submitted Round 2 improvements are confirmed by the team leader.
Review event/team/participant details and the final public PDF link before submitting. Dates and limitations
below are intentional. Do not classify pre-window work as event-window delivery.

## Product and repository

Product: https://inheria.onrender.com
Judge guide: https://inheria.onrender.com/demo
Repository: https://github.com/Gauravwakle96/INHERIA
Judge login instructions: Select Open judge workspace on the sign-in page. No
email/password or API key is required. The visitor enters as Rudransh and can
switch to Gaurav/Savinay within a separate expiring case-study workspace. The default completed mode includes 51 sources, eight accepted responsibilities and eleven reviewed walkthroughs. Try a fresh handover starts the same users with a new unapproved journey.
Final PDF Drive URL: pending.

## Complete list of working features

Organisation registration and password-based sign-in
Project membership and backend-enforced project/source permissions
One-click completed and fresh judge workspaces with scoped Gaurav/Savinay/Rudransh switching
Server-calculated next handover step and evidence-linked personal continuation plan
Expiring single-use team invitations and recipient-chosen passwords
Project membership revocation and current source-reader management
Recipient handover knowledge-access readiness with independent access review
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
Cited staging observation references with source-version checks and review history
Typed readiness checks with category-relevant citations and blocked incomplete closure
Critical-gap follow-ups with evidence, accountable project member and due date
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

## Testing details for the three submitted improvements

See docs/three-improvements-acceptance.md, docs/three-improvements-tests.json and
docs/verification.md. The dedicated acceptance run passed 34 existing isolated
journeys: seven onboarding/access, ten genuinely distinct source-change/revocation,
five interruption positions and twelve practical-transfer role flows. Tests use
owned SQLite fixtures and mocked GitHub; no model call or production mutation.
The latest full backend run passed 232 tests with 89% coverage, including 16 real
PostgreSQL cases in isolated loopback QA schemas. An
invitation revocation race was reproduced and corrected; duplicate actions,
source changes and recipient access loss are checked against real database locks.
Frontend lint,
typecheck/build, dependency audits and judge/onboarding/source browser checks
passed in their recorded scope. Automated accessibility is bounded, not an
independent user study or full screen-reader audit.

A separate 60-document internal holdout (34 prose) passed candidate precision/recall
50/50, owner 20/20, rationale 14/14 and dependency endpoints 14/14. These exceed
the submitted thresholds on the bounded set. Its frozen initial run is preserved;
labels are internal and implementation-informed, not independent enterprise
accuracy evidence. Original development fixtures remain separate.

A new 72-document all-prose challenge first measured precision 94.6%, recall
88.3%, owners 84.6%, rationales 75.0% and dependencies 83.3%. The first-run report
is unchanged. General fixes now pass these known-case regressions at precision
100%, recall 98.3%, owners 92.3%, rationales 100% and dependencies 94.4%.
These corrected results are tuned internal regression performance, not fresh
independent accuracy. Newly uploaded prose also passes the API investigation,
exact-citation review and generated-handover journey. See
docs/postgres-and-extraction-hardening.md for methodology and remaining misses.

## Improvement 1 — Secure Team Onboarding & Access Readiness

Delivered expiring single-use hashed invitation links, recipient-chosen passwords,
authenticated existing-account joins without role/password overwrite, project and
document access management, incoming access requests and independent decisions.
Team displays current membership and accessible/missing handover knowledge.
Administrators revoke invitations or project membership; old explicit source
reader grants and pending requests are revoked, with an audit trail. A source's
last-reader removal never opens access to everyone. Derived knowledge also obeys
parent-source permissions. Live browser checks passed invitation/password/revoke
and source-reader editing. This grants INHERIA knowledge access only; no automatic
AWS access. Links require private sharing; email/SSO/MFA remain outside this scope.

## Improvement 2 — Investigation and source-change intelligence
Delivered supported prose duty/rationale/dependency extraction, historical and
negated abstention, evidence-linked source/change impacts, deletion/revocation
revalidation and resumable source-version checkpoints. Fresh 60-document / 34
prose internal holdout met the 85% field / 90% precision targets. Ten distinct
source-change/revocation cases and five interruption positions passed;
permission-loss and deletion cases are separately tested. A subsequent 24-document challenge exposed passive-owner, rationale and dependency misses; the original results remain published. General pattern fixes pass those now-known regression cases, including explicitly uncertain joint ownership. An actual checkpointed worker exit and new API process resume also passed without duplicates. General unrestricted or multilingual prose accuracy and independent label audit remain limitations.

## Improvement 3 — Practical transfer validation and recovery
Delivered deployment/rollback/recovery rubrics, cited staging observation records,
separate documentation walkthroughs, current evidence/version checks, rejected
and reopened transfer recovery, acceptance, supervisor assessment history and
critical prerequisite closure gates. Twelve distinct positive/negative API role
journeys passed, including correction, rejection, reapproval, source revocation,
wrong actor and incomplete rubric. The complete browser handover passed.
A separate local toy-service exercise was actually run: a failed release was detected, v1 was restored, an empty backup was rejected and a correct SQLite backup restored three orders. Its downloadable record requires review and does not certify cloud operations, INHERIA PostgreSQL recovery or human competence. No production command is executed by INHERIA.

## Final regression checks

The latest full backend suite passed 232 tests with 89% line coverage. Exact-three
acceptance passed 34/34 again on 14 November. Earlier judge/onboarding/source and
chat browser tests are dated separately in verification.md. New closure readiness,
changed/failed evidence, cooldown/retry and onboarding UI checks passed. Build,
lint/typecheck, dependency audits and credential-pattern review passed in the
documented scope. Automated accessibility is bounded; no external user study is
claimed.

## What does not work yet

Missing or contradictory evidence needs human resolution; English pattern
extraction has bounded coverage and internal evaluation labels. SSO/MFA, email
invitation/password reset, OAuth/webhooks,
source-system permission mirroring, distributed workers, vector retrieval,
automated retention and enterprise governance remain unimplemented. Staging
observation authenticity and operational competence require authorised external
records and qualified supervisors. In-process work and free hosting are limited.

The optional chatbot is additional functionality, outside the three submitted
improvements. Its upstream provider was unreliable in the recorded run (41/50
fallbacks); it must not be presented as reliable full conversational automation.

## Future roadmap
1. Independently labelled permissioned extraction evaluation; improve prose,
   dependency impact and conflict analysis on fresh held-out data.
2. Verified identity, reset/invitation email, designed SSO/MFA and permission sync.
3. Durable workers, scheduled reviews/retention and operational monitoring/backups.
4. Real permissioned staging evidence and specialist review without production
   automation. No fabricated operations, company data or external feedback.

## Required confirmations still owned by the team leader

Exact event/team/leader/member details; truthful participant attribution;
final PDF and publicly accessible Viewer link;
private-window link tests; accurate feature/improvement declaration; once-only
submission. The form has not been submitted by this work.
