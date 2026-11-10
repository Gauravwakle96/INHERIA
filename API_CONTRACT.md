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

- `GET /ai-settings` → `{provider,base_url,model,protocol,enabled,has_key}`; never the key.
- `PUT /ai-settings {base_url?,model,protocol?,api_key?,enabled?}` → settings metadata. Bases: `https://agentrouter.org/v1` or `https://ps.air-outer.com/v1`; protocols: `responses`, `chat_completions`. Omit key to retain it.
- `DELETE /ai-settings` → `{ok:true}`; removes saved encrypted key.
- `POST /ai-settings/test` → `{ok:true,model,usage}` after a real bounded request, or safe 502.
- `GET /chat/conversations` → `{id,title,updated_at}[]` owned by the current user.
- `POST /chat/conversations` → Conversation (201); maximum 50 per user/project.
- `GET /chat/conversations/{id}` → Conversation. `DELETE` removes its messages/previews; confirmed project changes persist.
- `POST /chat/conversations/{id}/messages {message,effort:'low'|'high',model?,request_id:UUID}` → Conversation. 3–4000 characters, 100 turns per conversation. Duplicate IDs reuse results; running turns return 409. Models: `gpt-6.1-sol`, `gpt-6-astra`, `gpt-5.6-sol`.
- `GET /chat/actions` → `{id,kind,target_id,title}[]` filtered by current role/state.
- `POST /chat/conversations/{id}/actions {kind,target_id?}` → Conversation (201) with an unexecuted preview.
- `POST /chat/actions/{id}/confirm {confirm:true}` → Action; rechecks actor, role, expiry and evidence, idempotent after completion.

Conversation `{id,title,updated_at,turns:[{id,question,effort,status,response,created_at}]}`. Response `{answer,parts:[{kind,text,references}],citations,actions,unknowns,known,engine,warning?,model?,elapsed_ms?,usage?}`. Part kinds: project/status/guidance/unknown/excerpt. Excerpt marks keyword-matched verified documents, not a generated answer; known stays false for fallback matches. Action `{id,kind,title,status,expires_at,result:{resource_id?,status?,path?}}`. Supported kinds: investigate, sync, start_capture, generate_handover, generate_exercises, simulate. Previews expire in 20 minutes. No approval, ownership acceptance or infrastructure execution is exposed.

Source, verification and role changes withhold dependent history; source deletion purges saved derived text including follow-ups. Provider failure uses visible verified-retrieval fallback. Structural citation validation does not prove semantic correctness.

## Backend services

SQLAlchemy 2 sync Session in sync FastAPI routes; BackgroundTasks invoke bounded job services with their own sessions. `database.get_db`, `database.SessionLocal`, `models.Base`. `security.current_user`, `security.project_access(db,user,project_id,write=False)`, `security.require_role(user,roles)`, `security.visible_sources(db,user,project_id)` (source IDs), `security.can_read_source(db,user,source)`, `security.audit(db,user,project_id,action,resource_type,resource_id,details)`.

All domain services must call source permission filters. Current claims are visible only if all evidence sources are authorised, ready and at the cited version; mixed ACL claims are hidden in full. Rejected/invalidated knowledge cannot enter authoritative handovers/answers/graphs.

Model timestamps via `created_at, updated_at`, IDs UUID strings, `org_id,project_id` on project entities. JSON payloads named `data`, reports named `report`. Evidence points to `claim_id,chunk_id,source_id,source_version,quote`. Claims have `created_by`, `verified_by`, `verified_at`. Users are global unique email and one org initially. Every source mutation audits, revocation removes derived access immediately.

## Final extensions

- `POST /api/projects/{project_id}/members {name,email,title,role,password}` creates an organisation account and project membership; administrator only. Roles manager/lead/employee/incoming/security; minimum password length12; password never returned. No email is sent.
- `POST /api/projects/{project_id}/gaps/{gap_id}/respond {answer}` records a targeted human interview as a pending Claim with interview provenance and inherited source access restrictions. Another authorised reviewer is required.
- Claim review supports optional `owner_id`, `backup_id`, `component`, `critical` fields for explicit human confirmation; corrected summaries return to pending.
- Exercise includes optional `transfer_id`. Tasks are generated for each assigned responsibility plus related knowledge. Readiness requires a supervisor-validated task for every accepted transfer.
- Closure adds human acceptance/validation provenance and updates the current owner while preserving the previous owner.
