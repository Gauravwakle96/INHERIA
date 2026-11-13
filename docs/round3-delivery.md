# Round 3 delivery and submission mapping

The team leader confirmed the submitted Round 2 commitments: Secure Team
Onboarding & Access Readiness, Investigation and Source-Change Intelligence, and
Practical Transfer Validation & Recovery. Chat was not submitted as one of the
three. The earlier saved PDF is preserved as historical material; its different
list no longer creates an open decision. See [the exact promise-to-delivery map](three-improvements-acceptance.md)
and [submission checklist](round3-submission-checklist.md). This is not an awarded
score or event eligibility certification.

## Implementation workstreams already present

| Improvement | What changes for users | Demonstrable evidence |
| --- | --- | --- |
| Secure Team Onboarding & Access Readiness | Recipients set their own password through an expiring single-use invitation; missing source access is reviewed independently, without granting unrelated operational access. | Team invitation/join UI, revocation, hashed token storage, existing-account identity checks, scoped request/review API and tests. |
| Knowledge Change & Impact Investigation | A changed runbook exposes downstream impact; interrupted investigations resume from committed source-version checkpoints instead of losing progress or duplicating candidates. | Document replacement/Impact UI, exact prose field spans, old evidence invalidation, Resume action, ten change/recovery and five interruption-position cases. |
| Handover Recovery & Practical Validation | Missing information/rejected tasks lead to a corrected version and reconfirmation. Acceptance, supervisor criteria and mandatory cited checks gate closure. | Reopen/history, required prerequisites, scenario-v2 criteria, incoming-only acceptance, independent assessment and complete browser journey. |

These are the three submitted improvements. Their acceptance evidence includes
the 60-document / 34-prose internal holdout, ten distinct source-change/revocation
inputs, five interruption positions, twelve transfer-role journeys and live
onboarding/source-permission checks. See [three-improvement acceptance](three-improvements-acceptance.md)
for exact denominators and scope limits. Existing conversational features are
additional product work; historical provider failures remain disclosed but are
not an unfulfilled target of these three commitments.

## Announced event window

The 14 November announcement sets the window at 13 November 23:59 through
16 November 23:59. Much of the existing implementation above predates that
opening; dated Git history is preserved. Existing documents named Round 3 do
not establish that the code was built during the announced window. New
finalisation work is recorded at its actual date. This document does not certify
eligibility or relabel earlier work as event-window delivery.

## Rubric acceptance map

| Criterion | Implemented proof | Practical limit |
| --- | --- | --- |
| Completeness / 25 | Documents/GitHub sources → reconstruction → citations → correction/approval → scoped handover → acceptance → practical review → closure; isolated judge demo. | GitHub is bounded REST/PAT, not OAuth/webhooks. No production/cloud automation. |
| Improvements / 20 | Confirmed three changes above with UI, storage, trust gates and measured acceptance. | Extraction labels are internal; staging observations require permissioned external records and human review. |
| Reliability / 20 | Invalid files, missing/conflicting evidence, permission loss, stale versions, duplicate/expired invitations, provider failure, interruptions and source changes handled explicitly. | English rule extraction and in-process workers are bounded; free hosting and upstream quotas can interrupt availability. |
| Usability / 20 | Sign-in demo, role-specific guide, grouped handover, next risk questions, linked metrics, day/night, responsive layouts and keyboard/axe checks. | Automated axe is not a full screen-reader or usability study; no external feedback claims. |
| Documentation / 15 | Setup/env/API/schema/architecture, judge script, evaluation, tests, status, privacy/security/accessibility explanation and roadmap. | Final PDF/link and participant identities/contributions remain team-owned submission items. |

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

1. Evaluate on independently labelled permissioned documents; broaden prose
   extraction and evidence-linked dependency/conflict review on fresh holdouts.
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
