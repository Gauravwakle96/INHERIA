# The three submitted Round 2 improvements

The team leader confirmed in this session that the submitted commitments are
Secure Team Onboarding & Access Readiness, Investigation and Source-Change
Intelligence, and Practical Transfer Validation & Recovery. This confirmation
supersedes the earlier uncertainty caused by a different saved PDF draft.
Chat was not one of the three submitted commitments. Its existing implementation
and historical evaluation are additional product work, outside this acceptance map.
No original submission, commit history or test result has been rewritten.

## 1. Secure Team Onboarding & Access Readiness

### Submitted promise

> We will extend INHERIA’s existing account and permission system with single-use,
> expiring invitation links, project and document access management, and handover
> access-readiness checks. Incoming employees will set their own passwords, request
> missing access, and track approval decisions. Authorised administrators will be
> able to revoke invitations or project membership, with access changes recorded
> in the audit trail.
>
> For example, when Savinay takes over from Gaurav, INHERIA will identify whether
> Savinay can access the required handover documents. Missing access will become
> a request for an authorised reviewer to approve or reject.
>
> This helps teams prepare a usable handover, reduces manual account coordination,
> and prevents responsibility assignment from being mistaken for access readiness.
> The scope covers INHERIA projects and documents; it does not automatically grant
> AWS or other external-system access.

### Implemented behaviour

- Invitations have hashed, expiring, single-use tokens. New recipients choose
  their password. Existing accounts authenticate without role/password overwrite.
- Administrators revoke pending invitations or project membership. Pending access
  requests and explicit reader grants are revoked; other projects and contribution
  history remain. Last-reader removal never widens access to everyone.
- Source reviewers edit current document readers. Backend membership and source
  permissions also apply to derived interview and accepted-ownership evidence.
- Team shows required/accessible/missing handover knowledge and membership status.
  Hidden source titles remain hidden. Incoming employees submit an access request;
  an independent authorised reviewer grants a readable source or rejects it.
- Request decisions and invitation/membership/source changes are auditable.
  Ownership acceptance and readiness are separate checks.

**Demonstrate:** Team → Invite member → open one-time link in another browser →
set recipient password. In Sources, restrict one required document; in Team,
inspect missing access. As the incoming person request access; switch to the
reviewer to decide it. Revoke project membership and verify knowledge is denied.

**Evidence:** `routers/onboarding.py`, `routers/sources.py`,
`test_onboarding_completion.py`, `test_source_access_completion.py`,
`onboarding-completion.spec.ts`, `source-permissions.spec.ts`, and
[live access verification](four-workstream-live-verification.json).

**Limit:** Invitation links require private sharing; no mail delivery, SSO/MFA,
external IAM grants or upstream permission mirroring. Access requests require an
incoming user's action; discovery does not automatically grant or silently request
access. Project removal is not organisation-wide offboarding.

## 2. Investigation and Source-Change Intelligence

### Submitted promise

> Improve natural-prose extraction, evidence-linked dependency impact analysis and
> revalidation after source changes or deletion. Add resumable incremental job
> checkpoints so interrupted investigations can continue without duplicating
> artefacts.
>
> Evaluate at least 60 separately labelled documents, including 20 prose-heavy
> cases. Target at least 85% owner, rationale and dependency-field accuracy and 90%
> candidate precision on held-out data. Test 10 source-change/revocation scenarios
> and five interrupted-job scenarios.

### Implemented behaviour

- Conservative English prose patterns extract explicit responsibilities, reasons
  and dependencies with exact source spans. Historical/negated/proposed ownership
  statements do not become current responsibilities.
- The graph attaches evidence to relationships. Source impact links changed
  sources to claims, handovers and exercises, including transitive derived copies.
- Replacement invalidates current knowledge/assessments while retaining historical
  versions. Deletion purges source-derived text. Revocation or lost access removes
  authority immediately; reauthorisation requires new evidence review.
- Source-version checkpoints and candidate writes commit atomically. Resume
  rechecks authority and skips unchanged checkpoints without duplicate candidates.

**Measured first-run internal holdout:** 60 separately authored documents, 34
prose cases; owner 20/20, rationale 14/14, dependency endpoints 14/14, candidate
precision and recall 50/50, exact quotations 50/50. These exceed the stated
thresholds on this bounded set. Internal labels were implementation-informed and
frozen before first use; the corpus is now regression data. There is no independent
enterprise accuracy claim. See [frozen extraction report](extraction-holdout-report.json).

**Distinct source scenarios:** uploaded replacement/reviewed recovery; explicit
revocation; deletion and derivative purge; successor ACL loss before closure;
transitive interview evidence invalidation; GitHub credential revocation;
repository permission denial; repository disappearance; complete-tree file
removal; README removal/revalidation. These are separate state changes, not ten
different notes sent through the same replacement test.

**Interrupted jobs:** failures at five source positions (2, 3, 4, 7, 11), followed
by authorised resume and candidate deduplication checks.

**Demonstrate:** upload prose documents → Investigate → inspect candidate evidence
and dependency graph → independently review → Sources → New version → Impact →
reinvestigate → reopen/regenerate/reapprove the handover. Resume is demonstrated
by controlled test interruption, rather than claiming a real live server outage.

**Limit:** Supported English patterns, bounded lexical retrieval and in-process
workers. The five positions test one checkpoint algorithm, not a distributed job
system. Arbitrary/multilingual semantic accuracy remains unmeasured.

## 3. Practical Transfer Validation & Recovery

### Submitted promise

> Extend current validation with responsibility-specific scenario rubrics, cited
> staging evidence, rejected or reopened handover recovery, critical-gap closure
> gates and traceable reapproval. Successors and supervisors will be able to
> identify incomplete prerequisites, request corrections and repeat validation
> before closure.
>
> Deliver deployment-review, rollback-readiness and recovery-evidence scenarios.
> Test at least 12 positive and negative role flows, including rejection,
> correction, revoked evidence and reopening. Preserve separate supervisor
> assessment and execute no production commands.

### Implemented behaviour

- Deployment, rollback and recovery tasks use responsibility-specific criteria,
  supporting citations and safe escalation. Acceptance is incoming-only; a
  separate authorised supervisor assesses every criterion.
- Knowledge walkthroughs and externally supplied staging observation records are
  distinguished. Observation citations must be verified, readable, current and
  identify a staging/test-environment observation/result. A runbook alone is refused.
- Missing prerequisites and unaccepted/unvalidated responsibilities block closure.
  Rejected submissions support correction/resubmission and traceable review history.
- Reopened active handovers require a regenerated version, reapproval, incoming
  reconfirmation and reassessment. Closed ownership records require a separate
  follow-up transition; they are preserved rather than rewritten.
- Changed/revoked/deleted observation evidence prevents continued readiness and
  assessment. Hidden evidence is withheld from read paths.

**Twelve role flows:** correct acceptance; wrong actor; missing citations;
supervisor submission denied; successor self-assessment denied; rejection blocks
closure; incomplete rubric; correction/reassessment; critical prerequisite;
reopen/reapproval; cited staging observation; revoked observation evidence.

**Demonstrate:** Savinay rejects incomplete recovery ownership → Rudransh adds
or reviews required checks → Savinay submits cited explanations → Rudransh
requests correction → Savinay resubmits → Rudransh assesses all criteria → close
only after current evidence, acceptance, validation and required checks pass.

**Limit:** Observation authenticity and operational competence require honest
permissioned records and qualified external supervisors. Tests use authored
records. INHERIA never executes production/cloud commands and does not claim a
real deployment or restore from a checkbox or fixture.

## Verification and reproduction

[Submission acceptance tests](three-improvements-tests.json) records the executed
seven onboarding, ten distinct source-change/revocation, five interrupted-job and
twelve role journeys: **34/34 passed**, with test file hashes. The runner is
`uv run python evaluation/run_submission_acceptance.py` from `backend`; it uses
existing isolated fixtures/mocked GitHub and makes no paid model call.

The last full product regression passed 198 backend tests with 90% line coverage;
judge/onboarding/source browser acceptance passed 14 tests, with subsequent
focused source reruns and two live access tests. See [verification](verification.md)
for dates, exact counts and any later increments. This document is an acceptance
map, not an awarded score, independent audit or event eligibility certification.


Final experience update: completed account case-study mode, guided current continuation steps, typed evidence checks, critical-gap follow-up gates, cited dependency paths and actual isolated-process restart testing are documented in [completion hardening](completion-hardening.md). Original challenge extraction results remain preserved separately from corrected regression results. No independent human usability or cloud execution claim is added.
