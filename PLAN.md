# INHERIA implementation plan

Scope authorised: build a new application; the hackathon development window has started.
Existing INHERIA application was not located. Preserve unrelated projects and all Codex settings.

Status: the central MVP workflow is implemented and locally verified. The controlled browser and both preview services remain running. Final results and deployment limitations are recorded in [docs/verification.md](docs/verification.md); the full capability inventory is in [docs/feature-status.md](docs/feature-status.md). No application or Codex provider settings were replaced to resolve the preview interruption.

## Success criteria

A persisted, permission-enforced Connect → Reconstruct → Verify → Review → Handover → Validate workflow. Functional GitHub API ingestion and PDF/DOCX/Markdown/TXT/JSON parsing, synthetic Nexora organisation, evidence-linked claims, targeted investigation, hypothetical continuity analysis, human approval, successor acceptance and supervisor validation. No fabricated metrics, evidence or working connectors.

## Architecture and trade-offs

- React + TypeScript + Vite frontend, reusable accessible components and a navy/cyan enterprise design.
- FastAPI + Pydantic + SQLAlchemy modular monolith. PostgreSQL for deployment; SQLite for an immediately runnable local development environment with the same models and Alembic migrations.
- Database-backed jobs with bounded sync/extraction workloads and observable status; no Redis/Celery infrastructure until needed.
- Deterministic evidence extraction works without paid credentials and is explicitly labelled. Optional stateless LLM structured extraction validates every citation against authorised source excerpts; failure leaves source ingestion usable.
- GitHub REST API adapters use bounded pagination, retries, ETags and incremental sync. Private tokens are encrypted on the server using an environment-provided key; public repositories work without a token.
- Source ACLs are enforced before extraction, retrieval, graph building, metrics, reports and AI calls. Revocation invalidates derived evidence.
- File uploads are capped and parsed in bounded workers; secrets/PII are quarantined before indexing or external processing.

## Data and contracts

Organisations/users/roles/memberships; projects; connections/sources/versions/chunks; claims/evidence/verification; responsibilities/dependencies/gaps; investigations/questions/remediation; transitions/transfers/exercises/assessments; sync jobs/audit events. UUID identifiers, tenant/project foreign keys, indexed status and timestamps.

REST /api: session registration/login/logout/me; organisations/projects/team; sources/upload/GitHub/sync/revoke/delete; claims/evidence/review; investigations; graph; risk simulations; transitions/handover/transfers; validation tasks/supervisor review; successor query; metrics; audit/privacy. Errors use readable detail and request identifiers. API schemas drive TypeScript types.

Authentication uses hashed passwords and opaque HttpOnly sessions, same-origin checks on mutations, explicit project roles and source restrictions. Human approval is mandatory for authoritative claims and critical transfers. Synthetic login options are available only in explicitly enabled demo mode and still produce role-enforced sessions.

## Implementation sequence

1. Foundation: models, migrations, permission boundaries, auth, synthetic Nexora seed and contracts.
2. Ingestion: parsers, privacy guard, GitHub connector, duplicate detection, jobs and provenance.
3. Investigation: evidence extraction, reconstruction, contradictions, questions and remediation tasks.
4. Continuity: graph and clearly hypothetical, evidence-backed ownership-loss simulations.
5. Transfer: human verification, handover versioning, assignment/acceptance/rejection and practical exercises with supervisor review.
6. Product: connected UI, evidence explorer, successor, explainable metrics, privacy and audit.
7. Validation: API and failure/permission tests, labelled evaluation, frontend lint/typecheck/build, dependency audits, responsive/keyboard browser QA, Docker and documentation.

## Boundaries

No cross-company learning, predictive scores, production execution, multi-person simulation or arbitrary competence ratings. Future connectors are visibly Coming Soon. Enterprise SSO/MFA, data residency and large-scale distributed jobs are documented limitations unless implemented and verified. LLM accuracy is reported only from measured evaluation; deterministic extraction is not described as a general semantic AI model.

## Azure Responses diagnosis

Inspect endpoint/model/configuration metadata without reading or printing credentials. The reported error indicates a referenced item belongs to another Azure resource; inspect routing/continuation evidence before claiming a root cause. Preserve model/provider/security configuration. Use fresh stateless requests for INHERIA so it never reuses resource-specific response IDs.

## Verification checklist

- Cross-tenant/project/source denial and revocation.
- Missing/stale/contradictory/sensitive/duplicate evidence.
- Invalid documents, integration failures/rate limits and failed LLM extraction.
- Approval/acceptance/supervisor-validation gates across the full workflow.
- Synthetic data and citation evaluation report with reproducible counts.
- Local server and frontend preview; actual browser checks at mobile/tablet/desktop.
- Document all completed/partial/unimplemented features and actual check results.
