# INHERIA operating guide

This guide covers the deployed bounded product and local installation. Enterprise
capacity, cloud access provisioning and production command execution are outside
its current scope.

## Start a journey

Judges choose **Open judge workspace** for completed records or **Try a fresh
handover** for a new transfer. Visitor tenants expire after four hours by default;
case-study role switching never reaches real accounts. Real teams use separate
authenticated accounts within one organisation/project.

Create the project, invite members, connect permitted sources and follow the
next-action panel. Select source readers before sharing restricted documents.

## Authority and completion

| Activity | Responsible actor | Required boundary |
| --- | --- | --- |
| Invite/revoke project member | Authorised administrator | Current tenant/project rights, single-use invite and audit |
| Connect or change source access | Authorised user/source reviewer | Source permission and current reader policy |
| Review employee testimony | Separate authorised reviewer | No self-approval; current citations |
| Approve report version | Authorised coordinator/reviewer | Current version and reviewed accessible knowledge |
| Accept/reject ownership | Nominated successor | Admin cannot accept for them |
| Submit practical work | Assigned participant | Supporting evidence and responsibility-specific criteria |
| Pass/request correction | Separate supervisor | No self-assessment; current rubric/evidence |
| Close transition | Authorised coordinator | Acceptance, assessment, evidence and prerequisites pass |

## Expected failures and recovery

| Symptom | Safe action | Inspect |
| --- | --- | --- |
| Slow first live page | Allow free service wake-up, then retry once | Cold start; avoid keep-alive traffic |
| Missing permission | Successor requests access; independent reviewer decides | Source ACL/membership; external IAM remains separate |
| Disabled closure | Follow readiness links, resolve work and refresh | Acceptance, assessments, source versions, mandatory checks |
| Old/conflicting knowledge | Inspect sources, correct/resolve and reapprove | Current versus historical authority; do not approve to hide warnings |
| Interrupted investigation | Original authorised investigator resumes/retries as offered | Persisted job/source-version checkpoints |
| Failed GitHub sync | Correct auth or honour provider reset | Transient outage versus permission loss and safe warnings |
| Duplicate action / 409 | Wait for current job/state and refresh | One logical Sync or stale version; avoid repeated enqueue |
| Request limit / 429 | Honour cooldown; preserve saved work | Shared request budget; no immediate retry loop |
| Changed/revoked/deleted source | Investigate and review new evidence; reapprove active handover | Claims/report/assessments invalidated; inaccessible quotes withheld |
| Rejected ownership/exercise | Correct prerequisites, resubmit and reassess | Participant response remains separate from supervisor review |
| Provider failure | Use labelled evidence retrieval/saved conversation | Private organisation key/model; AI is optional |
| Expired/capacity-limited visit | Start a permitted new visit when available | No private-account sharing or limit bypass |

## Deploy and verify

Use locked installation commands in the README. Production requires PostgreSQL,
HTTPS origins, disabled shared development persona access and a stable encryption
key. Docker builds UI/API, runs migrations and serves one origin.

Check `/api/health` for process liveness and explicitly `/api/ready` for database
readiness. Verify deep links, login, CSRF rejection, ingestion and a restricted
read. Do not continuously probe the database to keep free services awake.

Application records are persisted in PostgreSQL. Render local storage is
ephemeral. In-process work may interrupt on restart; use checkpoints and resume.

## Migration and rollback

1. Review additive migration/data impact and approved encryption-key recovery.
2. Run `alembic upgrade head` through startup and inspect safe health output.
3. Redeploy a known-good application only if compatible with the current schema.
4. Database downgrade/restore is a separately approved operator procedure; no
   automatic production downgrade is supplied. Toy/local recovery does not prove
   application PostgreSQL recovery.

## Secrets, logs and resource limits

- Keys, sessions, private PATs and database URLs belong in approved server secret
  storage, never screenshots/reports/log text. Preserve the encryption key.
- Source text/derived views retain ACLs; restore login for authentication/CSRF
  failures rather than weakening origin or permission checks.
- Monitor hosting transfer/storage/compute allowance. Quota snapshots lag traffic;
  no silent paid upgrade or extra project to bypass limits.
- Source-derived deletion is implemented; scheduled retention is future work.
- Staging authenticity requires qualified review and permitted external records.
  INHERIA executes no deployment, rollback or restore.

## Release documentation

Record changes, checks actually run, known failures, migration effect, external
services/licences/costs and clean setup. Keep README, API, architecture, feature
status, verification and roadmap consistent. Actual individual contributions and
unfamiliar-user feedback require supplied records.
