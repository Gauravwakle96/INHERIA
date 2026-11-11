# Round 3 delivery and submission mapping

This is an implementation map, not an awarded score or guarantee. The exact
Round 2 form commitments have not yet been confirmed. The historical Round 2 PDF
is preserved; the proposed replacement of the conversational commitment must not
be described as organiser-approved without confirmation.

## Three improvements delivered in this build

| Improvement | What changes for users | Demonstrable evidence |
| --- | --- | --- |
| Secure Team Onboarding & Access Readiness | Recipients set their own password through an expiring single-use invitation; missing source access is reviewed independently, without granting unrelated operational access. | Team invitation/join UI, revocation, hashed token storage, existing-account identity checks, scoped request/review API and tests. |
| Knowledge Change & Impact Investigation | A changed runbook exposes downstream impact; interrupted investigations resume from committed source-version checkpoints instead of losing progress or duplicating candidates. | Document replacement/Impact UI, exact prose field spans, old evidence invalidation, Resume action, ten change/recovery and five interruption-position cases. |
| Handover Recovery & Practical Validation | Missing information/rejected tasks lead to a corrected version and reconfirmation. Acceptance, supervisor criteria and mandatory cited checks gate closure. | Reopen/history, required prerequisites, scenario-v2 criteria, incoming-only acceptance, independent assessment and complete browser journey. |

The previous conversational successor remains optional with private history,
citations and honest retrieval fallback. Live paid-provider operation is not
claimed as delivered by these changes. If the submitted commitment was a live
conversational assistant, that commitment remains partial until provider access
and quality are established or the organiser permits substitution.

## Rubric acceptance map

| Criterion | Implemented proof | Practical limit |
| --- | --- | --- |
| Completeness / 25 | Documents/GitHub sources → reconstruction → citations → correction/approval → scoped handover → acceptance → practical review → closure; isolated judge demo. | GitHub is bounded REST/PAT, not OAuth/webhooks. No production/cloud automation. |
| Improvements / 20 | Three changes above with UI, storage, trust gates and regression tests. | Exact submitted commitments still require reconciliation. |
| Reliability / 20 | Invalid files, missing/conflicting evidence, permission loss, stale versions, duplicate/expired invitations, provider failure, interruptions and source changes handled explicitly. | English rule extraction and in-process workers are bounded; free hosting and upstream quotas can interrupt availability. |
| Usability / 20 | Sign-in demo, role-specific guide, grouped handover, next risk questions, linked metrics, day/night, responsive layouts and keyboard/axe checks. | Automated axe is not a full screen-reader or usability study; no external feedback claims. |
| Documentation / 15 | Setup/env/API/schema/architecture, judge script, evaluation, tests, status, privacy/security/accessibility explanation and roadmap. | Participant identities/contributions and exact form commitments need team confirmation. |

## Privacy, security, accessibility and responsible design

Tenant/project/source access is enforced on the backend, including retrieval and
derived histories. Sessions and invitation/visitor capabilities use opaque random
tokens with stored hashes. Passwords use Argon2; mutations require CSRF/origin
checks. Private integration/provider tokens stay encrypted server-side. Documents
have size limits and secret/PII quarantine/redaction before indexing/model input.
No claim of absolute confidentiality or complete PII detection is made.

The demo contains authored case-study content and no actual employee confirmations.
Important assertions retain citations and explicit human verification state.
Missing information, conflicts and hypothetical scenarios are distinguished from
verified knowledge. Practical explanations do not certify cloud competence.

Both themes use semantic colors, visible focus, native dialogs/forms, responsive
navigation and reduced-motion support. Representative keyboard, mobile/tablet/
desktop and automated WCAG A/AA checks are recorded in verification.md. A full
assistive-technology audit and external user study remain future work.

## Limitations and realistic next steps

1. Establish approved live provider access and evaluate on independently labelled
   held-out permissioned documents; broaden semantic extraction and conflict review.
2. Add production invitation email, verified identity/password recovery and a
   designed SSO/MFA integration; preserve least-privilege source permissions.
3. Replace in-process jobs with durable worker orchestration when traffic warrants
   it; scheduled refresh/retention, upstream permission sync and operational
   observability need real deployment validation.
4. Add externally supplied staging-test artifacts and specialist reviewer roles;
   do not let a checkbox stand in for actual recovery execution.

## Participant and contribution record

Repository owner: GitHub account Gauravwakle96. Complete legal participant names,
team roles and individual contributions have not been confirmed. Do not infer
participant contributions from the fictional Gaurav/Savinay/Rudransh personas.
AI-assisted implementation is visible in repository changes and tests. The team
must review the final commit history and supply an accurate contribution statement
before submission. No video, final form submission or independent feedback is
claimed by this document.
