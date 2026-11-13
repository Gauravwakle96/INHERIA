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

## Testing details

The last full backend run passed 169 tests with 90% line coverage. Coverage spans
auth, tenants/projects/source ACLs, files, connectors, chat, provenance, decision
authority, source removal, invitations, interruptions and transfer recovery.
The completion module had 100% line coverage in that run. One existing
FastAPI/Starlette TestClient deprecation warning remains.

During the announced window, three direct judge-entry browser tests passed for
entry, refresh, separate visitors, duplicate-click protection, retry and disabled
demo configuration. Six day/night 390/768/1440px sign-in/guide checks passed with
no overflow or automated WCAG A/AA violations. The complete real UI handover
journey also passed again. Frontend lint, typecheck, production build and npm
audit passed. Backend was unchanged in this direct-entry increment; its earlier
full test run is not misrepresented as a new event-window run.

Earlier live verification covered the private ShopEase project's twelve pages,
three roles, exact closed handover link, refresh persistence and mobile/day versus
desktop/night layouts. The recorded case study has eight accepted responsibilities
and eleven reviewed explanations; it asserts no real Wipro/cloud operation.
GitHub CI, deployment checks and evidence are linked in docs/verification.md.

Testing found source-removal completion ambiguity, rejected drafts counted as
current ownership, misleading obsolete chat documentation and rapid-reload test
rate limits. The first three were corrected; the expanded browser journey uses
normal navigation/pacing without disabling rate limits. Automated accessibility
checks are bounded coverage, not screen-reader certification or external user
feedback.

Extraction evaluation currently has 60 development fixtures, 46/47 candidate
precision and 46/46 recall with 47/47 exact citations. One prose false positive
remains. There is no held-out split or independent annotation audit. These figures
are controlled rule measurements, not general model accuracy or business impact.

## Improvement 1 — conditional on the actually submitted text

The saved PDF commits to Conversational Digital Successor: project-scoped history,
encrypted organisation provider configuration, Low/High modes, cited answers and
previewed role-checked actions. Those capabilities are implemented. A live Bynara
reply with two citations was verified in 66.4 seconds; history persisted. Provider
failure preserves the conversation and offers labelled evidence retrieval.
AgentRouter failed for this application and Bynara was added after an authorised
provider change. The promised 50-question held-out assessment and both-mode live
quality/latency/usage benchmark are incomplete; do not claim those targets passed.

If the actual submitted form instead commits to Secure Team Onboarding & Access
Readiness, describe the expiring single-use invitation, own-password join,
existing-account identity preservation, independent source-access decisions,
revocation, audit and permission/expiry tests. Confirm that this replacement was
submitted before using it as the graded Improvement 1.

## Improvement 2 — based on the saved PDF

Committed: Investigation and source-change intelligence, with validated prose,
evidence-linked impact, changed/deleted-source revalidation and resumable
checkpoints. Delivered: supported prose field-span extraction, source replacement
with filtered downstream impact, stale authority invalidation and checkpointed
resume. Ten source-change/revocation and five interrupted-job scenarios are
covered by tests. The 60-document/20-prose quantity is met by the development
fixture; the promised development/held-out separation and held-out field/precision
targets remain incomplete. Misses and measurement limits are published.

## Improvement 3 — based on the saved PDF

Committed: Practical transfer validation and recovery, with responsibility-specific
rubrics, cited evidence, rejected/reopened recovery and critical-gap closure gates.
Delivered: release-review, rollback-readiness and recovery-evidence criteria,
incoming-only acceptance, selected citations/escalation, independent supervisor
assessment, required prerequisites and corrected-version reapproval/reassessment.
Positive/negative role, rejection, correction, revocation and reopening flows are
tested. The app records evidence walkthroughs; actual authorised external staging
execution must be performed and evidenced separately. No production command runs.

## Other improvements after Round 2

Workspace-wide completed handover/contribution summaries, accurate current-owner
counts, exact-version navigation, provider-scoped Bynara configuration and live
reply verification, source-deletion completion checks, and clearer judge guides.
Direct sign-in judge access, retry/duplicate-start feedback and the reconciled
submission checklist were added after the announced Round 3 opening. Earlier
changes retain their real timestamps and are not described as built inside it.

## Roadmap

1. Establish a separately labelled, permissioned held-out corpus and 50-question
   conversation benchmark; publish misses, citation entailment, abstention and
   per-mode latency/usage before claiming broader extraction/model quality.
2. Add verified identity, reset/invitation email and designed SSO/MFA, with upstream
   source-permission synchronisation and an enterprise security review.
3. Introduce durable queued workers/checkpoints, scheduled refresh/retention and
   operational monitoring/backups once traffic and hosting resources justify it.
4. Add permissioned staging-test artifact intake and specialist assessment so
   organisations can verify operational readiness from actual evidence without
   autonomous production execution.

No cross-company learning, predictive continuity score or unrestricted automation
is promised. Roadmap requires real user feedback, authorised test environments,
reliable data, provider agreements and appropriate hosting resources.

## Required confirmations still owned by the team leader

Exact event/team/leader/member details; the actual submitted Round 2 commitments;
truthful participant attribution; final PDF and publicly accessible Viewer link;
private-window link tests; accurate feature/improvement declaration; once-only
submission. The form has not been submitted by this work.
