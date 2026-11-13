# Shared implementation contract

All JSON dates are ISO strings; IDs are UUID strings. Lists are plain arrays. Mutations return the updated entity. Errors: `{detail: string, request_id?: string}`. Cookie auth, `X-CSRF-Token` on authenticated mutations. Vite proxies `/api` to `http://127.0.0.1:8010`.

## Endpoints

`GET /api/health` → `{status, version, demo_mode, ai_mode}`.
`GET /api/auth/demo-users` → User[]. Enabled only in demo mode.
`POST /api/auth/demo-login {user_id}` / `POST /api/auth/login {email,password}` / `POST /api/auth/register {name,email,password,organisation}` → `{user,csrf_token}`.
`GET /api/auth/me` → `{user,csrf_token}`. `POST /api/auth/logout` → `{ok:true}`.
User: `{id,org_id,name,email,title,role}`; roles admin/manager/lead/employee/incoming/security.

`GET /api/projects` → Project[]. `POST /api/projects {name,description}` → Project.
Project: `{id,name,description,status,stack,is_demo}`.
`GET /api/team?project_id=...` → User[].

Project feature endpoints prefix `/api/projects/{project_id}`:

- `GET /overview` → `{metrics:[{key,label,value,numerator,denominator,description}],activity:Audit[],pipeline:[{stage,status,count}],ai_mode,synthetic,source_health:{ready,failed,quarantined}}`.
- `GET /continuity-summary` → `{completed_handovers,completion,contributors,scope}`. Completion is null until a closed handover has accessible current claims and ready source records; otherwise it includes its ID, title, participant names, version, closure date, accepted/total responsibility counts, validated/exercise counts, knowledge-item count and `current` readiness flag. Contributors contain project-member IDs/names and counts of accessible interview responses, knowledge reviews, owned/accepted/transferred responsibilities, backup assignments and submitted/reviewed walkthroughs. Counts come from stored workflow records and respect project/source permissions. No email, password or token is returned. Changed evidence may require revalidation; revoked/deleted/inaccessible evidence hides dependent completion.
- `GET /sources` → Source[]. Source `{id,name,kind,status,url,version,source_time,updated_at,synthetic,restricted,metadata,chunk_count}`; metadata never includes credentials/raw quarantined content.
- `POST /sources/upload` multipart `file`, optional `allowed_user_ids` JSON array → `{source,duplicate}`. PDF/DOCX/MD/TXT/JSON.
- `POST /connections/github {repository,token?}` → Connection. `GET /connections` → Connection[]. `POST /connections/{id}/sync` → Job. `POST /connections/{id}/revoke` → Connection. Connection `{id,name,provider,repository,status,last_sync_at,has_token}`.
- `POST /sources/{id}/revoke` → Source; `DELETE /sources/{id}` → `{ok:true}`.
- `GET /jobs` → Job[]. Job `{id,kind,status,error,stats,created_at,finished_at}`.
- `GET /claims?kind=...&status=...` → Claim[]. Claim `{id,kind,title,summary,status,confidence,confidence_reason,data,evidence:[Citation],updated_at}`. kinds responsibility/decision/procedure/dependency/incident/task/lesson/architecture; status pending/verified/rejected/invalidated/superseded. confidence is evidence strength label, not predicted accuracy.
- Citation `{id,source_id,source_name,source_kind,source_url,source_time,source_version,chunk_id,locator,quote,synthetic}`.
- `GET /evidence/{source_id}` → `{source,chunks:[{id,locator,text}]}`.
- `POST /claims/{id}/review {action:'approve'|'reject'|'correct',note,summary?}` → Claim. Only admin/manager/lead may approve; no author self-approval.
- `POST /investigations {focus?,employee_id?}` → Investigation; server creates persisted bounded job; UI polls `GET /investigations` and jobs.
- `GET /investigations` → Investigation[]. Investigation `{id,status,report:{summary,findings:[{title,kind,severity,details,question,source_ids,claim_id?}],questions:[{question,reason,source_ids}],searched_sources,unknowns,engine,limitations},created_at}`.
- `GET /gaps` → Gap[]. Gap `{id,title,kind,severity,status,details,question,source_ids,claim_id}`. `PATCH /gaps/{id} {status:'open'|'in_progress'|'resolved',note}` → Gap. Resolution requires manager/lead.
- `GET /graph` → `{nodes:[{id,label,kind,status}],edges:[{id,source,target,label,status,evidence:[Citation]}],limitations}`. Only evidenced authorised relations.
- `POST /simulations {employee_id,scenario:'unavailability'|'outdated_procedure'|'dependency_failure',component?,assumptions?:string[]}` → Simulation. `GET /simulations` → Simulation[]. Simulation `{id,created_at,employee_id,scenario,assumptions,report:{hypothetical:true,summary,affected:[{responsibility_id,title,system,critical,owner,backup,status,risks:string[],evidence:Citation[]}],recommendations:string[],unknowns:string[]}}`.
- `GET /transitions` → Transition[]. `POST /transitions {title,departing_id,successor_id,departure_date}` → Transition. Transition `{id,title,departing_id,successor_id,departure_date,status,version,report,transfers:Transfer[],exercises:Exercise[]}`.
- `POST /transitions/{id}/generate` → Transition. Generate uses verified claims and shows unknowns/pending claims. `POST /transitions/{id}/approve {note}` → Transition. `POST /transitions/{id}/close` → Transition. Close blocked until all responsibilities accepted and supervisor-validated.
- `POST /transitions/{id}/assign {claim_id,successor_id,backup_id?}` → Transfer. Transfer `{id,claim_id,title,successor_id,backup_id,status,note}`. Only verified responsibility claims; approval gate.
- `POST /transfers/{id}/respond {action:'accept'|'reject',note}` → Transfer. Only assigned successor; acceptance never validates readiness automatically.
- `POST /transitions/{id}/exercises` → Transition. Deterministic practical tasks from verified procedures/dependencies/incidents with predefined criteria.
- `POST /exercises/{id}/submit {answer,evidence_ids:string[],escalation:string}` → Exercise. Exercise `{id,title,prompt,criteria:string[],expected_source_ids:string[],status,answer,evidence_ids,escalation,supervisor_note,assessment}`.
- `POST /exercises/{id}/review {action:'pass'|'needs_revision',note}` → Exercise. Only authorised supervisor, never the participant.
- `GET /transitions/{id}/readiness` → `{accepted,total,validated,exercise_total,ready,blockers:string[],evidence_coverage:{numerator,denominator},limitations}`.
- `POST /successor/ask {question}` → `{answer,known:boolean,citations:Citation[],unknowns:string[],engine}`. Retrieval strictly permission filtered and unknown answers explicit.
- `GET /audit` → Audit[]. Audit `{id,action,resource_type,resource_id,actor_name,details,created_at}`.
- `GET /privacy` → `{sources:Source[],quarantined_count,retention_days,controls:string[],limitations:string[]}`.

## Backend module contract

## Private project chat

Prefix `/api/projects/{project_id}`. All routes enforce membership, cookies and CSRF. AI settings are organisation-wide; changes/test/disconnect require administrator and project write permission.

- `GET /ai-settings` → `{provider,base_url,model,models,protocol,enabled,has_key}`; never the key. `models` contains selectable models for that provider, including its configured default.
- `PUT /ai-settings {base_url?,model,protocol?,api_key?,enabled?}` → settings metadata. Bases: `https://agentrouter.org/v1`, `https://ps.air-outer.com/v1`, `https://router.bynara.id/v1`; protocols: `responses`, `chat_completions`. Bynara requires `chat_completions`; default UI model `agnes-2.5-flash`. Omit key to retain it at the same endpoint. Changing endpoint with an existing key requires a new key, preventing cross-provider credential disclosure.
- `DELETE /ai-settings` → `{ok:true}`; removes saved encrypted key.
- `POST /ai-settings/test` → `{ok:true,model,usage}` after a real bounded request, or safe 502.
- `GET /chat/conversations` → `{id,title,updated_at}[]` owned by the current user.
- `POST /chat/conversations` → Conversation (201); maximum 50 per user/project.
- `GET /chat/conversations/{id}` → Conversation. `DELETE` removes its messages/previews; confirmed project changes persist.
- `POST /chat/conversations/{id}/messages {message,effort:'low'|'high',model?,request_id:UUID}` → Conversation. 3–4000 characters, 100 turns per conversation. Duplicate IDs reuse results; running turns return 409. Model must appear in the saved provider's `models`; omit it to use the organisation default. Unsupported overrides return 422 before creating a turn. Bynara replies use `engine:'bynara'`; AgentRouter uses `engine:'agentrouter'`. Invalid output or provider failure uses labelled verified retrieval.
- `GET /chat/actions` → `{id,kind,target_id,title}[]` filtered by current role/state.
- `POST /chat/conversations/{id}/actions {kind,target_id?}` → Conversation (201) with an unexecuted preview.
- `POST /chat/actions/{id}/confirm {confirm:true}` → Action; rechecks actor, role, expiry and evidence, idempotent after completion.

Conversation `{id,title,updated_at,turns:[{id,question,effort,status,response,created_at}]}`. Response `{answer,parts:[{kind,text,references}],citations,actions,unknowns,known,engine,warning?,model?,elapsed_ms?,usage?}`. Part kinds: project/status/guidance/unknown/excerpt. Excerpt marks keyword-matched verified documents, not a generated answer; known stays false for fallback matches. Action `{id,kind,title,status,expires_at,result:{resource_id?,status?,path?}}`. Supported kinds: investigate, sync, start_capture, generate_handover, generate_exercises, simulate. Previews expire in 20 minutes. No approval, ownership acceptance or infrastructure execution is exposed.

Source, verification and role changes withhold dependent history; source deletion purges saved derived text including follow-ups. Provider failure uses visible verified-retrieval fallback. Structural citation validation does not prove semantic correctness.

## Backend services

## Round 3 API additions

`GET /api/auth/judge-demo` returns enabled/expiry configuration.
`POST /api/auth/judge-demo/start` (201) creates an isolated visitor tenant and
session, setting a separate HttpOnly visitor capability cookie. `GET /people`
and `POST /switch {user_id}` under `/api/auth/judge-demo` require the session and
matching visitor capability. Switching is restricted to the three demo personas.

Under `/api/projects/{project_id}`:

- `POST /invitations {email,name,title,role,expires_hours?}`: administrator only;
  returns metadata and a one-time `/join#token=...` link. GET lists metadata
  without tokens; `POST /invitations/{id}/revoke` revokes pending invitations.
- `POST /api/auth/invitation/accept {token,password?}` consumes a valid invitation.
  New users choose a password (12+ characters); existing invited accounts must
  authenticate and retain their identity role. Cross-tenant joins are refused.
- `GET/POST /access-requests`, POST body `{purpose}`. Ordinary members see only
  their requests. `POST /access-requests/{id}/review {action,source_id?,note}`
  requires another project reviewer; sources must be readable by that reviewer.
- `POST /members/{user_id}/revoke {note}`: project-write administrator only;
  removes this membership and pending invitations/requests, revokes existing
  source reader grants and audits metadata. Self-removal returns 409; unknown
  member returns 404. Other projects, account and historical contributions remain.
- `GET /access-readiness`: recipient knowledge counts per handover, current
  membership, accessible/required/missing counts and next steps. Non-reviewers
  see only assigned handovers; missing source titles are omitted when unreadable.
- `GET /sources/{id}/access` and `POST /sources/{id}/access
  {allowed_user_ids:string[],note}`: source-readable project reviewers only.
  Empty list permits all members. Restricted list must contain current members
  and the reviewer; derived retrieval/readiness always rechecks current ACLs.
- `POST /claims/{id}/resolve-authority {note}` explicitly selects a current
  decision and preserves competing accessible candidates as superseded.
  Conflicting decisions cannot use ordinary approval. No author self-review.
- `POST /investigations/{id}/resume` resumes an interrupted/failed checkpoint for
  the original authorised investigator, rechecking source versions and permissions.
- `GET /sources/{id}/impact` returns filtered historical claim, transition and
  exercise lineage. `POST /sources/{id}/replace` multipart `file` versions an
  uploaded source; connected/interview/transfer sources are refused. Source
  responses expose `replaceable` for the corresponding UI control.
- `POST /transitions/{id}/reopen {note}` preserves recovery/version history and
  resets acceptance and practical review. Closed ownership cannot reopen.
- `POST /transitions/{id}/prerequisites {title,required}` before approval;
  `POST /transitions/{id}/prerequisites/{id}/review {status,note,evidence_ids}`
  confirms with current verified references accessible to the incoming person.
- Exercise review accepts `criteria_passed:boolean[]`; scenario-v2 passes require
  every predefined criterion explicitly assessed.
- Exercise submission also accepts `validation_kind:knowledge_walkthrough|
  staging_observation` (default walkthrough), and `staging_evidence_ids:string[]`.
  Observations require verified accessible records explicitly describing a staging
  or test-environment observation/result; a runbook alone is insufficient.
  Source-version references and supervisor review history remain in assessment.
  Revocation/deletion/change blocks completion and withholds/purges derived text.

Readiness includes sanitized prerequisites. Source changes, permission loss,
claim corrections, incomplete acceptance, assessments and required checks block
closure. Handover responses include current accessible risk questions; historical
inaccessible quotations and prerequisite notes are withheld.

## Backend service conventions

SQLAlchemy 2 sync Session in sync FastAPI routes; BackgroundTasks invoke bounded job services with their own sessions. `database.get_db`, `database.SessionLocal`, `models.Base`. `security.current_user`, `security.project_access(db,user,project_id,write=False)`, `security.require_role(user,roles)`, `security.visible_sources(db,user,project_id)` (source IDs), `security.can_read_source(db,user,source)`, `security.audit(db,user,project_id,action,resource_type,resource_id,details)`.

All domain services must call source permission filters. Current claims are visible only if all evidence sources are authorised, ready and at the cited version; mixed ACL claims are hidden in full. Rejected/invalidated knowledge cannot enter authoritative handovers/answers/graphs.

Model timestamps via `created_at, updated_at`, IDs UUID strings, `org_id,project_id` on project entities. JSON payloads named `data`, reports named `report`. Evidence points to `claim_id,chunk_id,source_id,source_version,quote`. Claims have `created_by`, `verified_by`, `verified_at`. Users are global unique email and one org initially. Every source mutation audits, revocation removes derived access immediately.

## Final extensions

- `POST /api/projects/{project_id}/members {name,email,title,role,password}` creates an organisation account and project membership; administrator only. Roles manager/lead/employee/incoming/security; minimum password length12; password never returned. No email is sent.
- `POST /api/projects/{project_id}/gaps/{gap_id}/respond {answer}` records a targeted human interview as a pending Claim with interview provenance and inherited source access restrictions. Another authorised reviewer is required.
- Claim review supports optional `owner_id`, `backup_id`, `component`, `critical` fields for explicit human confirmation; corrected summaries return to pending.
- Exercise includes optional `transfer_id`. Tasks are generated for each assigned responsibility plus related knowledge. Readiness requires a supervisor-validated task for every accepted transfer.
- Closure adds human acceptance/validation provenance and updates the current owner while preserving the previous owner.
