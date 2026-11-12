# Digital Successor chat integration

Extend the existing `/successor` experience and keep the existing excerpt API for compatibility. This increment adds private project conversations, low/high effort, organisation-owned provider settings, evidence-grounded answers and explicit action previews.

## Design and trust boundaries

- React uses the existing query client, theme, dialog, citation and error components. No extra UI or agent framework dependency.
- FastAPI chat routes reuse cookie/CSRF, project membership, source ACL and existing domain endpoints. Provider calls are server-only, timeout/budget bounded, stateless and never execute tools.
- An administrator explicitly selects a provider/model and enables external processing. Bynara uses Chat Completions with `agnes-2.5-flash`; AgentRouter retains its Responses-compatible route. Do not impersonate a supported client or bypass provider refusals. A connection test must report actual availability. The backend publishes provider-specific model choices; unsupported overrides fail before a turn is created. Changing endpoint requires a new key rather than forwarding the previous provider's credential.
- Encrypt the organisation-specific key using the existing Fernet key. Return only configuration metadata, never the credential. Disconnect erases the saved provider key.
- Persist conversations/turns under organisation, project and owning user. Source-dependent turns retain cumulative claim/source version signatures; current access and verification are checked before history is displayed or sent to a model. Source deletion purges affected turn contents, including dependent follow-ups.
- Context contains only accessible verified evidence and scoped operational status. Pending information stays explicitly uncertain. Generated project statements must cite an allowed evidence ID; general guidance is labelled; missing information leads to abstention. Structured output validation does not establish semantic truth.
- Low/high effort change evidence/history/output budgets and request reasoning effort for compatible GPT models. Other models still receive different context and detail budgets; provider reasoning support is not assumed.
- Supported action previews: investigate, retry a selected GitHub sync, start capture on a selected gap, generate an existing handover, generate its exercises, or run a hypothetical simulation. Confirmation rechecks permission and resource state, delegates to existing handlers and is idempotent. No automatic claim approval, owner acceptance, supervisor assessment, source deletion or production command.
- Safe provider errors fall back to the existing evidence retrieval while showing the failure. No raw provider error, credential or prompt is logged. Missing key/model never produces fake model output.

## Implementation sequence

1. Add models and immutable Alembic migration; typed chat/settings schemas.
2. Add provider adapter, current-evidence/history filtering and action preview/confirmation services.
3. Replace successor UI with persistent conversations, effort controls, citations, settings and previews.
4. Test model failures, unsupported citations, prompt injection boundaries, permissions, stale history, secrets and duplicate confirmations; check browser layout/accessibility and production build.
5. Update API/setup/feature documentation and deploy the authorised update after successful checks.

Provider probes on 11 November 2026: `/v1/models` and actual stateless Responses requests returned HTTP 401; Responses was tested against both official endpoints. No credential was logged. This prevents confirming live model answers. The client reports the failure and continues verified retrieval; no client impersonation or bypass is used.

Bynara probes on 12 November 2026: an actual Chat Completions request to
`https://router.bynara.id/v1/chat/completions` using `agnes-2.5-flash` returned
HTTP 200 with usable text in 45.58 seconds. A second request using INHERIA's
real adapter and structured-answer schema succeeded in 47.5 seconds and
abstained when no project evidence was supplied. These are individual smoke
checks, not an accuracy or availability guarantee. Live integration results
are recorded in [verification](verification.md).

## Operational limits

Provider request timeout is 110 seconds (10-second connect timeout). Low effort selects up to 8 evidence records, 14,000 evidence characters, 4 prior turns and 1,600 output tokens; High selects 20 / 36,000 / 8 / 3,200. Reasoning effort is passed to compatible GPT models. No automatic model switch or paid retry occurs. Provider retention/permission agreements need organisation review; `store=false` is not a confidentiality guarantee.

History limits are 50 conversations and 100 turns per conversation; delete old conversations when needed. Prompts are secret-filtered and PII-redacted. Conversations have neutral titles to avoid restricted source text in navigation. Role changes conservatively invalidate earlier history. Lexical fallback uses the existing method, so Low/High affects model calls only. Partial source data, rule-based extraction and citation validation do not establish knowledge completeness or generated semantic truth.

An interrupted confirmed action may remain executing if the process stops after its domain mutation commits. Inspect the linked project workspace before requesting another action; replay is intentionally blocked. Restarts mark unfinished replies failed. Durable workers, streaming/cancel, semantic answer evaluation and automatic retention are future work.

Live QA revealed lexical matching can return related documents for an unrelated question. Fallback matches are explicitly labelled related excerpts and do not set `known=true`; they are not presented as model explanations.
