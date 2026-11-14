# Feature status and scope

This file reports implementation, not the complete long-term product vision. The central challenge workflow takes priority over additional engines.

| Capability | Status | Practical limit |
| --- | --- | --- |
| Organisation registration, login, team account creation, project membership | Implemented | Expiring single-use invitations; one organisation per account; no email delivery/reset/SSO/MFA |
| GitHub REST connector | Implemented | Public repositories or encrypted PAT; bounded snapshots, no OAuth/webhooks |
| PDF/DOCX/Markdown/TXT/JSON parsing | Implemented | Bounded files; scanned PDFs need external OCR |
| Source ACL, versions, provenance, revoke/delete | Implemented | External source permission changes require resync/revocation; no source-system permission mirror |
| Source-statement extraction and project reconstruction | Implemented | Deterministic rules and supported English prose with exact field spans; broader semantics remain incomplete |
| Optional structured LLM extraction | Implemented and tested with mocked provider | Live provider operation/quality depends on configured credentials; no claimed live accuracy |
| Autonomous knowledge investigation | Implemented | Authorised local sources; bounded gap rules, targeted questions, review tasks; no autonomous source discovery outside connected data |
| Tacit knowledge capture | Implemented | Targeted text interviews; no voice transcription |
| Decision intelligence | Implemented | Source-linked rationale/alternatives and same-topic conflict candidates; no semantic proof of every contradiction |
| Knowledge graph | Implemented | Evidence-backed project/person/responsibility/system relationships; no digital-twin historical restoration |
| Continuity simulations | Implemented | Single employee, dependency component and stale/unverified procedures; no multi-person or financial prediction |
| Handover versioning and human approval | Implemented | Active handovers reopen for correction, reapproval and reacceptance; closed ownership requires a follow-up transition |
| Responsibility assignment / acceptance / rejection | Implemented | One incoming participant per transition; no responsibility splitting |
| Practical validation and readiness | Implemented | Predefined criteria, evidence selection, explanation and supervisor review; INHERIA executes no sandbox commands |
| Current ownership after closure | Implemented | Auditable accepted-transfer evidence, previous owner retained in provenance |
| Workspace completion and team contributions | Implemented | Every project page shows the latest accessible closed handover, acceptance/review totals and recorded participant contributions; current readiness is rechecked and source removal hides dependent completion. Completed transfer does not resolve open incidents or certify cloud recovery |
| Digital Successor private chat | Implemented and live-verified with Bynara | Owner-only persisted history, Low/High effort, provider-specific model choices, citations and fallback; `agnes-2.5-flash` live reply returned two citations in 66.4 seconds; availability depends on provider limits |
| Chat actions and encrypted organisation AI settings | Implemented | Admin-only opt-in/key/test/disconnect; supported domain actions require preview confirmation; no production execution |
| Explainable risk / readiness / evidence metrics | Implemented | Measurable ratios and counts; no arbitrary resilience index or predictive AI |
| Day and night themes | Implemented | Browser-persisted manual selection; current browsers with CSS light-dark() support |
| Privacy center and filtered audit | Implemented | Disclosure of current controls/limits; retention setting is informational until automated deletion exists |
| Synthetic Nexora and controlled evaluation | Implemented | Clearly labelled fixtures; not real contributor/employee data |
| General workflow builder / scheduled orchestration | Not implemented | Outside central workflow |
| Isolated judge demo beside sign-in | Implemented | Completed 51-source account case study or fresh 13-source workflow; scoped persona switching; four-hour default; real accounts remain inaccessible |
| Knowledge access requests | Implemented | Independent source-ACL decisions; grants no AWS/IAM access |
| Document replacement and source-change impact | Implemented | Preserved versions; filtered claim/handover/task lineage; stale evidence blocks current actions |
| Investigation resume | Implemented | Atomic per-source checkpoints; original authorised investigator can resume; no distributed worker |
| Recovery prerequisites and scenario criteria | Implemented | Mandatory cited checks and explicit supervisor assessment; cloud evidence must be supplied externally |
| Industry profiles / custom roles / departments | Partial architecture | Industry field and role enums exist; full configuration UI/policy engine absent |
| Cross-project memory reuse | Postponed | No cross-company learning or confidential data sharing |
| Predictive decay / multi-person continuity / advanced restoration | Postponed | Requires historical data and additional validation |
| PostgreSQL deployment / Docker / CI | Deployed; CI configured | Render Free Docker build/runtime and Neon PostgreSQL verified; see deployment evidence |
| Automated retention / legal hold / data residency / enterprise governance | Not implemented | Must be designed and validated for an actual deployment |

The eleven engines remain logical product domains: discovery, capture, decisions, relationships, trust, organisation configuration, handover, continuity, readiness, workflow and memory. They share persisted models and services. INHERIA does not claim that every long-term engine feature is implemented.

14 November acceptance update: project membership revocation, current-document
reader management, handover access readiness, cited staging observation records
and traceable assessment history are implemented. The separate 60-document
internal extraction holdout met its targets. The 50-question live chat run found
only 9/50 valid provider replies, so Conversational Digital Successor remains
provider-limited despite working private history, citations/actions and fallback.
See [measured delivery and limits](four-workstream-acceptance.md).


Final experience update: completed account case-study mode, guided current continuation steps, typed evidence checks, critical-gap follow-up gates, cited dependency paths and actual isolated-process restart testing are documented in [completion hardening](completion-hardening.md). Original challenge extraction results remain preserved separately from corrected regression results. No independent human usability or cloud execution claim is added.

Latest full reliability verification: **239 backend tests passed**,
including **17 real PostgreSQL cases**. The previous coverage measurement was
89%; this newer run did not collect fresh coverage. The invitation
accept/revoke stale-state race was reproduced and corrected. The new 72-document
all-prose challenge's original misses and corrected known-case regression results
remain separate. Live upload → investigation → citation review → handover,
completed/fresh judge entry and restricted evidence/visitor isolation passed.
See [verification](verification.md) and [future roadmap](roadmap.md).

Handover closure now displays current acceptance, supervisor review, evidence
coverage and blockers before the action. Missing/failed readiness disables the
Close button; links lead to access, sources and practical review. Refresh retries
readiness without reloading the workspace. Backend closure validation remains
authoritative; the UI never turns a simulated/test response into real approval.

Further hardening: supported explicit prose variants, scoped dependency fields,
training-example rejection, duplicate sync enqueue protection, source warnings
and mobile table containment. A separate frozen 60-document first run meets
submitted targets with two disclosed misses. Real authenticated live sync of the
own public repository imported 40 sources; incremental resync added none. See
[judge-input evidence](judge-input-hardening.md).
