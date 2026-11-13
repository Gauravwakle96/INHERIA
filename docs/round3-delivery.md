# Round 3 delivery and submission mapping

This is an implementation map, not an awarded score or guarantee. The exact
Round 2 form commitments have not yet been confirmed. The saved Round 2 PDF,
page 15, names Conversational Digital Successor, Investigation and source-change
intelligence, and Practical transfer validation and recovery. It is preserved;
the later proposed replacement of the conversational commitment must not be
described as organiser-approved without confirmation. See
[the final submission checklist](round3-submission-checklist.md) for exact acceptance
targets and the announced event-window baseline.

## Implementation workstreams already present

| Improvement | What changes for users | Demonstrable evidence |
| --- | --- | --- |
| Secure Team Onboarding & Access Readiness | Recipients set their own password through an expiring single-use invitation; missing source access is reviewed independently, without granting unrelated operational access. | Team invitation/join UI, revocation, hashed token storage, existing-account identity checks, scoped request/review API and tests. |
| Knowledge Change & Impact Investigation | A changed runbook exposes downstream impact; interrupted investigations resume from committed source-version checkpoints instead of losing progress or duplicating candidates. | Document replacement/Impact UI, exact prose field spans, old evidence invalidation, Resume action, ten change/recovery and five interruption-position cases. |
| Handover Recovery & Practical Validation | Missing information/rejected tasks lead to a corrected version and reconfirmation. Acceptance, supervisor criteria and mandatory cited checks gate closure. | Reopen/history, required prerequisites, scenario-v2 criteria, incoming-only acceptance, independent assessment and complete browser journey. |

These workstreams are not interchangeable with the exact submitted commitments.
The conversational successor also has private history, citations, Low/High modes,
encrypted provider settings and previewed role-checked actions. Bynara's
`agnes-2.5-flash` returned a live cited reply, recorded separately in
bynara-live-verification.json. AgentRouter previously failed for the web app.
The promised 50-question held-out model evaluation is not complete, and the
existing 60-document extraction evaluation is a development fixture rather than
a held-out corpus. Those acceptance limits must be disclosed if the saved PDF
is the final submitted commitment. Secure onboarding is additional progress
unless the team confirms that it was actually submitted as a replacement.

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
