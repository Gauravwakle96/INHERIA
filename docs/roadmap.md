# INHERIA product roadmap and delivery strategy

## Product direction

The shipped release covers authorised ingestion, evidence-linked reconstruction,
human review, controlled handover, incoming acceptance, supervisor assessment and
continuation. The [three submitted improvements](three-improvements-acceptance.md)
remain the delivered commitments. This roadmap strengthens that journey before
expanding source coverage or operational scope.

Everything below is future work. Effort ranges are small-team planning estimates,
not promised release dates or evidence of completion. Workstreams describe future
responsibilities, not confirmed contributions by individual participants.

## Milestones and dependencies

| Milestone | Priority / estimated effort | User outcome | Dependency / release decision |
| --- | --- | --- | --- |
| M1: independently evaluated reconstruction | P0; 2–3 development weeks | Reviewers understand quality by document category and correct less knowledge | Obtain consented documents and independent labels; establish quality before broadening extraction |
| M2: identity, access and onboarding usability | P0; 3–4 development weeks | Successors join, recover access and understand prerequisites with less coordination | Freeze role/ACL contracts; verified email precedes reset and identity integration |
| M3: durable processing and application recovery | P1; 3–4 development weeks | Operators recover jobs and application data from expected failures | Measure workload first; preserve checkpoints, revocation and deduplication semantics |
| M4: permissioned integration and domain depth | P2; 4–6 development weeks per selected pilot | A real team uses its relevant source system and qualified operational evidence | Requires M1 quality, M2 identity and M3 operational gates; select one real pilot need |

Product coordination owns prioritisation; data/AI engineering owns extraction;
backend/security owns access; platform engineering owns processing and recovery;
QA/UX owns observed journeys and acceptance evidence. Stages overlap only where
the current permission/evidence invariants remain covered.

## M1 — Independently evaluated reconstruction

**Current limitation:** internal corpora target supported explicit English. They
do not establish independent enterprise accuracy for shared ownership, pronouns
or unrestricted prose.

**User benefit:** reviewers see uncertainty and category limits and focus their
corrections where needed.

### Implementation and deliverables

1. Obtain permissioned/anonymised documents from at least two source categories.
   Record consent, permitted use, redaction and retention before ingestion.
2. Label type, owner, historical/current state, rationale, dependency direction and
   exact evidence span using two independent reviewers; record disagreement and
   adjudication. Implementation-authored labels are never called independent.
3. Freeze a new held-out corpus before changes. Proposed collection target: at
   least 100 documents, 40 prose-heavy and 20 ambiguous/negative cases. Split by
   project/document lineage to avoid near-duplicate leakage. These are future targets.
4. Improve scoped pronouns, shared/unnamed owners, decision reasons and multiword
   dependency endpoints. Missing evidence remains unresolved.
5. Compare rules and optional structured providers on the same frozen cases,
   permissions, timeout and bounded cost policy. Keep a useful non-provider path.
6. Publish category/aggregate results, denominators, misses, review agreement and
   attribution checks; preserve first-run failures separately from tuned regressions.

### Release gates

| Measure | Proposed acceptance gate | Measurement |
| --- | --- | --- |
| Candidate precision | At least 90% | Correct candidates / all extracted candidates on untouched split |
| Owner/rationale/dependency fields | At least 85% for each | Correct fields / applicable labelled fields, with category results |
| Recall | Publish overall and category results | Recovered candidates / labelled relevant candidates; disclose abstention misses |
| Attribution | Every published candidate has a valid current source span | Source/version/quote membership; semantic support reviewed separately |
| Restricted/revoked evidence | Zero disclosures in acceptance suite | API, graph, report, retrieval, saved history and derived evidence checks |
| Label independence | Publish authorship and adjudication | Two independent reviewers and recorded disagreements |

**Dependencies/risks:** consent and reviewer availability may delay evaluation.
If unavailable, keep the current bounded scope and disclose internal labels.
Pronoun ambiguity may stay unresolved; optional model comparison must not block
source-backed review.

**Release evidence:** frozen corpus manifest, permission register, label guide,
agreement/adjudication, first-run results, regression suite and documented limits.

## M2 — Identity, access lifecycle and onboarding usability

**Current limitation:** invitations are manually shared. Verified email, recovery,
SSO/MFA and upstream permission mirroring are absent. Browser automation does not
establish independent usability.

**User benefit:** a successor joins safely, recovers credentials, requests missing
knowledge and understands the next responsible actor.

### Implementation sequence

1. Add verified-email registration and invitation delivery with an approved
   provider. Hash single-use expiring capabilities; protect account enumeration,
   resend and acceptance budgets.
2. Add password recovery, invalidation rules and notification; test expiry,
   replay, concurrent consumption and membership revocation.
3. Integrate one approved organisation identity provider. Bind identity to tenant,
   prevent role escalation/unsafe account merging and implement MFA according to
   its policy. Preserve existing identity and memberships during migration.
4. Add GitHub OAuth/signed webhooks only when a pilot needs them. Validate signatures,
   replay, token expiry, repository removal and permission-loss events.
5. Expand keyboard, focus, screen-reader and low-vision checks. Observe at least
   five consented unfamiliar-user sessions across three roles. Record task,
   completion, help, time and confusion; fix and retest blocking issues.

### Release gates

- Positive/negative invitation, verification, login, reset, expiry, concurrency
  and revocation flows pass against PostgreSQL.
- Forbidden titles/text/citations/history remain hidden after access loss. Admin
  privilege never overrides source permission.
- Proposed usability gate: at least four of five participants finish the assigned
  main task without facilitator intervention; every observed blocking issue is
  fixed and retested. Publish actual unsuccessful sessions too.
- Keyboard/focus and representative screen-reader tasks pass with stated scope;
  no accessibility certification is inferred.
- Audit events, identity configuration, incident recovery and migration guidance
  are documented. INHERIA membership still does not grant AWS/IAM access.

**Dependencies/risks:** email delivery, identity policy and upstream ACLs vary.
Support one tested configuration first; retain existing login during migration.

**Release evidence:** threat model, provider guide, permission/replay/concurrency
results, audit examples, consented user notes, accessibility scope and recovery plan.

## M3 — Durable jobs, governance and application recovery

**Current limitation:** processing is bounded/in-process; free hosting has quotas
and cold starts. Distributed workers, scheduled retention and production recovery
are not implemented.

**User benefit:** expected restarts preserve investigation progress and operators
can diagnose failure and recover application data.

### Implementation and deliverables

1. Measure source counts, sync duration, database transfer, memory, queue depth
   and API latency before choosing new infrastructure.
2. Add durable queue/worker semantics: transaction-safe enqueue, stable job identity,
   source-version checkpoint, bounded retry/backoff, cancellation and dead-letter
   recovery. Duplicate delivery yields one logical result.
3. Add shared limits and worker concurrency controls; distinguish revoked authority
   from transient provider failure. Retries never restore revoked knowledge.
4. Schedule source freshness review and retention policies; remove derived text
   according to policy, with observable completion/failure.
5. Define operator-approved recovery-point/time objectives (RPO/RTO) and backup scope.
   Restore to an owned test database; check rows, permissions, source versions and
   transfer state. Encryption-key recovery accompanies ciphertext restoration.
6. Document request errors, queue backlog, database readiness, quota pressure,
   migrations and compatible application rollback.

### Failure and release gates

| Failure | Required result |
| --- | --- |
| Restart before/after commit | Committed progress preserved; one candidate set; safe resume |
| Duplicate delivery/concurrent Sync | One active logical job and auditable result |
| Revocation while working/retrying | No new authoritative content; current source permission rechecked |
| Retry budget exhausted | Explicit terminal status and recovery instructions; no infinite loop |
| Cancellation | Clear terminal status; partial work never called complete |
| Retention/deletion | Source-derived content purged; audit metadata retained according to policy |
| Database restore | Meets approved test RPO/RTO; no tenant leakage or stale evidence revival |

Proposed initial capacity profile: 10 concurrent users and three active
investigations over 30 minutes. Measure target hardware, inputs, p95 latency,
failure rate, database transfer and memory; revise the support profile before
promising throughput. These are future targets, not current production results.

**Dependencies/risks:** queue services may exceed a free budget. Keep bounded mode
available; add services only with operator budget and measured need. A database
downgrade is not an automatic application rollback.

**Release evidence:** failure-injection matrix, restart/duplicate/revocation tests,
retention report, backup drill, capacity results, operator guide and migration plan.

## M4 — Permissioned integrations and operational depth

**User benefit:** a pilot team uses the knowledge already in its task/wiki system
and inspects specialist-reviewed operational-test evidence.

- Choose one connector from a consented pilot need. Deliver real authentication,
  incremental sync, provenance, permission-loss, delete/revoke and failure/retry
  handling before marking it available or connected.
- Preserve source permissions in graph, report and saved history; test upstream
  authority changes against controlled authorised fixtures.
- Support explicit domain schemas and specialist reviewers without combining
  participant acceptance with supervisor assessment.
- Import staging artefacts with environment, observer, result, timestamp and source
  identity. Qualified review remains necessary; upload is not authenticated
  execution telemetry.
- Observe the complete pilot journey and publish actual corrections and outcomes,
  without invented operational savings or user results.

**Release gate:** authentication/sync/permission-loss/E2E tests pass and the pilot
confirms incoming users can identify current owners, procedures and next steps.
Unsupported connectors remain unimplemented. Production command execution needs
a separate approval/safety design and stays outside near-term scope.

## Future depth after the core milestone gates

Prioritise these extensions after M1–M3, with scope/effort estimated after source
access and schema impact are known. They are not delivered features or fixed-date
commitments.

| Order / audience | Planned capability | Dependency and acceptance |
| --- | --- | --- |
| 1: successor and supervisor | Read-only staging CI evidence: begin with authorised GitHub Actions run IDs, commits, environment, timestamps and results linked to validation submissions | Least-privilege access, safe logs, forged-reference/missing-artefact/revocation tests; CI success alone never certifies competence |
| 2: project manager and security reviewer | Permission-filtered evidence package: approved handover version, acceptance, supervisor assessment, open follow-ups and citation/version manifest | Redaction/export permissions, integrity checks and audited download; historical approval is distinct from current readiness; downloaded copies cannot be remotely revoked |
| 3: team splitting one person's duties | Linked multi-successor transfers: separate deployment, monitoring and recovery owners with individual acceptance and assessment | Extend schema/readiness after single-successor stability; test partial completion, reassignment, revocation and concurrent writes |
| 4: DevOps/backend/IT reviewer | Versioned organisation templates for evidence requirements, questions, escalation and validation criteria | Admin policy, schema/version/migration tests and one consented DevOps pilot; job title/template never establishes a verified duty |

Read-only staging evidence comes first because it deepens practical verification.
Evidence packages support accountability next. Multi-successor and template work
follow observed pilot demand. Each extension must demonstrate real authentication,
permission lifecycle, source-linked output, missing-data/failure behaviour and
role-specific E2E tests before it is labelled available. Retain manual human review;
no production execution is implied.

## Release governance and documentation

Each milestone ships a review packet: user-visible scope; current/partial/not-built
status; API/schema/environment changes; additive migration and recovery plan;
positive/negative permission tests; original evaluation failures; appropriate
usability/accessibility results; service/licence/cost disclosures; clean setup
verification and known limitations.

Maintain [architecture](architecture.md), [API](../API_CONTRACT.md),
[verification](verification.md), [feature status](feature-status.md),
[operating guide](operating-guide.md) and README together. Roadmap targets never
become dashboard or report results until measured.
