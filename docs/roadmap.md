# INHERIA future development roadmap

The shipped scope is authorised source ingestion, evidence-linked reconstruction,
human review, controlled handover, incoming acceptance, supervisor assessment and
project continuation. The three submitted improvements are mapped separately in
[three-improvements-acceptance.md](three-improvements-acceptance.md). The stages
below are future work, not additional delivered commitments or fixed release dates.

## Stage 1 — Independently evaluated knowledge reconstruction

**User benefit:** reviewers spend less time correcting prose extraction and can
understand the reliability limits for their document types.

- Obtain permissioned, independently labelled documents and reviewer agreement.
- Freeze a new evaluation split before development; keep training/regression and
  held-out results separate.
- Improve explicit/shared ownership, pronoun resolution, rationale extraction,
  multiword dependencies and conflicting/current decision review.
- Measure candidate precision/recall, field accuracy, exact attribution,
  uncertainty/abstention and permission filtering by case category.
- Compare rule-based extraction with optional structured providers using bounded
  cost, latency and failure budgets; retain a useful non-provider path.

**Exit criteria:** publish the label process, sample sizes, held-out denominators,
misses and source-attribution checks. Meet at least the existing 90% candidate
precision and 85% owner/rationale/dependency targets on the new held-out split;
report category failures even when aggregate targets pass. No result is called
independent until labels and review actually meet that definition.

Current baseline: the new 72-document first run had real misses; fixes pass
now-known regression thresholds. [Original and corrected results](postgres-and-extraction-hardening.md)
remain published.

## Stage 2 — Verified identity and permission lifecycle

**User benefit:** administrators coordinate less account work and successors can
join, recover access and leave a project through a complete identity process.

- Add verified-email onboarding, transactional invitation email and password reset
  with single-use expiry and account-enumeration protections.
- Design SSO/MFA against an authorised identity provider; preserve existing identity
  and role boundaries.
- Add GitHub OAuth/webhooks where justified and test upstream permission change,
  token expiry, replay and removal handling.
- Surface knowledge-access readiness separately from cloud/IAM access requests.
- Expand assistive-technology and keyboard testing, then run recorded unfamiliar-user
  sessions with consent and actual outcomes.

**Exit criteria:** positive/negative invitation, reset, sign-in, revocation and
provider-permission journeys pass; audit events are complete; forbidden information
does not appear in retrieval, reports or saved history after access loss. Run at
least five recorded unfamiliar-user journeys and fix observed blocking confusion.
Do not infer AWS/IAM access from project membership.

Current baseline: manually shared expiring invitations, project/source ACLs,
independent access decisions and real PostgreSQL invitation races are implemented.
Email delivery, reset, SSO/MFA and upstream permission mirroring are absent.

## Stage 3 — Durable processing and operational governance

**User benefit:** source investigation remains recoverable during restarts and
normal team growth; operators can monitor, retain and recover project data.

- Introduce a durable queue/worker only when workload measurements justify it,
  retaining the existing source-version checkpoint and deduplication contract.
- Use shared rate limiting, controlled concurrency and idempotent job scheduling.
- Add scheduled source freshness reviews and observable sync/investigation alerts.
- Implement explicit retention/deletion policies with source-derived purge checks.
- Establish deployment backups and actually rehearse restoration in an owned
  non-production environment.
- Collect realistic load/latency, retry and resource-use measurements.

**Exit criteria:** restart/duplicate-delivery/cancellation tests preserve one
logical result; revoked sources never regain authority through replay; retention
removes derived content; a documented backup restores a separately owned test
database; published load results declare hardware, sample size and limits.

Current baseline: database-backed statuses, bounded workers, real restart/resume,
15 PostgreSQL concurrency cases and source-derived deletion are tested. Distributed
workers, enterprise throughput, automatic retention and production recovery are
not claimed.

## Later expansion

After those gates pass, prioritise one connector at a time using real authorised
customer needs. Consider configurable industry schemas, specialist reviewer roles
and externally supplied staging-test artefacts. Each connector needs functioning
authentication, sync, permission-loss behaviour and end-to-end tests before it is
labelled available/connected.

Cross-company learning, speculative predictive scores, unrestricted autonomous
remediation and production command execution are outside this roadmap's near-term
scope. A roadmap item does not grant permission to process or expose a source.

## Evidence and maintenance

Maintain [feature status](feature-status.md), [verification](verification.md),
[API documentation](../API_CONTRACT.md), migrations and setup instructions with each
increment. Preserve original evaluation failures and actual commit timestamps.
Publish measurable outcomes and known limits instead of treating a successful
local test, attractive screenshot or planned capability as proof of readiness.
