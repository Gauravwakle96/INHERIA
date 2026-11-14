# PostgreSQL races and fresh extraction checks

Real PostgreSQL 17.11 ran locally with the application's production transaction
semantics, using separate SQLAlchemy sessions and uniquely named QA schemas.
No existing Neon data, account credentials or provider settings were used.
Alembic upgraded the separate local QA database to `b19e47a2c805`.

The 15 transaction cases cover duplicate ownership acceptance/assignment,
closure, claim and handover approval, supervisor assessment, exercise generation,
concurrent JSON prerequisite edits, source change/revocation, recipient ACL loss,
membership loss with a stale reader edit, single-use invitation acceptance,
acceptance versus revocation and a retained stale invitation state.
The harness waits until PostgreSQL reports actual overlapping lock waits.
These are direct route-handler/database tests; HTTP authentication/CSRF coverage
is separately present in the existing API suite. They are not a load benchmark
or proof of arbitrary transaction schedules.

The stale-invitation test exposed a real pre-fix failure: a pending ORM instance
could overwrite an accepted invitation after an overlapping commit. Revocation
now acquires the same project lock as acceptance and reloads current state.
[Recorded results and original failure](postgres-concurrency-verification.json).

The final backend suite passed **228 tests**, including these 15 PostgreSQL cases,
with **90% line coverage** and one existing FastAPI TestClient deprecation warning.
Configured Ruff lint/format and the locked-environment Python dependency audit
passed. The new API extraction test verifies upload, investigation, pending exact
evidence, authorised claim review and inclusion in a generated handover.

## Reproduce

Use a temporary PostgreSQL database on loopback whose name ends in `_qa`.
Set `INHERIA_TEST_POSTGRES_URL` in the test shell, then run from `backend`:

```powershell
uv run pytest -q tests/test_postgres_concurrency.py
```

The fixture creates and removes only its generated `qa_<uuid>` schema. It rejects
remote URLs and database names that do not end in `_qa`. No database URL means
these tests are explicitly skipped, not counted as a pass. GitHub CI now supplies
an ephemeral PostgreSQL 17 service and runs them as part of the existing backend
suite. Its trust authentication is restricted to disposable CI/local test services;
production database authentication is unchanged.

Local Windows testing used a checksum-verified PostgreSQL 17.11 binary package
from the maintained Zonky embedded-PostgreSQL binary distribution. It is an
ignored test dependency, not an application dependency or system installation.
PostgreSQL rejected the System32 data directory; the disposable cluster was
created under the user's normal project workspace. No sandbox or ACL was weakened.
The PostgreSQL licence and upstream components remain their own licences.

The lock design follows PostgreSQL's documented `FOR UPDATE` behaviour and
READ COMMITTED visibility, supplemented by expiring SQLAlchemy cached objects:
https://www.postgresql.org/docs/17/explicit-locking.html
https://www.postgresql.org/docs/17/transaction-iso.html

## Fresh extraction evidence

72 additional internally authored prose documents and expected labels were
frozen before first use at application baseline `561746a`. The challenge includes
current/passive/shared/unresolved duties, negated or historical claims, direct
and passive dependency relationships, decision reasons and missing rationales.
The implementing coding agent authored the labels; no independent human-label
quality or enterprise accuracy is claimed.

The [unchanged first-run report](fresh-extraction-first-report.json) measured:

- Candidate precision 53/56 = 94.6%; recall 53/60 = 88.3%.
- Owner fields 22/26 = 84.6%.
- Rationale fields 12/16 = 75.0%.
- Dependency endpoints 15/18 = 83.3%.

General pattern fixes add explicit assigned/provided ownership, reverse passive
and `depends upon`/`uses` dependencies, additional causal phrases and clearer
abstention for unconfirmed/rumoured statements. One valid duty can coexist with
a separate denial of a different duty. A statement later described as unconfirmed
or historical remains excluded. Missing rationale is not itself a rationale.

[Known-case regression results](fresh-extraction-regression-report.json): candidate
precision 59/59 and recall 59/60, owners 24/26, rationales 16/16, dependencies 17/18.
Three field misses remain: pronoun-only owner attribution is deliberately unresolved,
a shared-duty paragraph with an unconfirmed accountable lead is conservatively
excluded, and a dependency endpoint retains an article instead of matching its
shorter gold label.
Exact citation quotes remain available. These results are tuned regression
performance, not fresh held-out or independent accuracy after the fixes.

Reproduce the current known-case metrics from `backend` without replacing the
original first-run report:

```powershell
uv run python -c "import json; from pathlib import Path; from app.acceptance_evaluation import evaluate_extraction; print(json.dumps(evaluate_extraction(Path('evaluation/fresh-extraction-challenge.json')), indent=2))"
uv run pytest -q tests/test_acceptance_evaluation.py
```

All existing frozen reports and authored account history remain unchanged.
Practical tests still require separate incoming acceptance and human review;
these extraction checks certify neither operational readiness nor source truth.
Independent user outcomes are not supplied by the automated tests.
