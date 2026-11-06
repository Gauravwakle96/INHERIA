# INHERIA controlled synthetic evaluation

24 hand-labelled synthetic documents plus one source-ACL negative; isolated in-memory SQLite; no live LLM calls.

Fixture `labelled-continuity-v1`; SHA-256 `20c27738e9495aa80c9586d593332f7d475a47bf1fa8e3324052544ae64d8b50`.

Run from `backend`: `uv run python -m app.evaluation`. The command uses an isolated in-memory database and makes no external AI requests.

| Measure | Numerator / denominator | Rate |
| --- | ---: | ---: |
| candidate kind and title: precision | 19 / 19 | 100.0% |
| candidate kind and title: recall | 19 / 20 | 95.0% |
| owner mapping | 4 / 5 | 80.0% |
| decision rationale field | 4 / 5 | 80.0% |
| dependency endpoints | 2 / 3 | 66.7% |
| project state kind coverage | 8 / 8 | 100.0% |
| exact source citations | 19 / 19 | 100.0% |
| claims with citations | 19 / 19 | 100.0% |
| pending before human review | 19 / 19 | 100.0% |
| commit authorship ownership abstention | 1 / 1 | 100.0% |
| unverified answer abstention | 1 / 1 | 100.0% |
| supported retrieval after review | 1 / 1 | 100.0% |
| unsupported answer abstention | 4 / 4 | 100.0% |
| restricted source excluded from reconstruction | 1 / 1 | 100.0% |
| potential decision conflict: precision | 1 / 1 | 100.0% |
| potential decision conflict: recall | 1 / 1 | 100.0% |
| stale source review: precision | 1 / 1 | 100.0% |
| stale source review: recall | 1 / 1 | 100.0% |
| unfinished work: precision | 2 / 2 | 100.0% |
| unfinished work: recall | 2 / 2 | 100.0% |
| missing decision rationale: precision | 1 / 1 | 100.0% |
| missing decision rationale: recall | 1 / 1 | 100.0% |
| unknown responsibility owner: precision | 2 / 3 | 66.7% |
| unknown responsibility owner: recall | 2 / 2 | 100.0% |

## Observed errors and limits

- `prose_responsibility`: owner mapping expected `Ada Vale`, observed `None`.
- `prose_decision`: decision rationale expected `the traffic pattern includes repeated lookups`, observed ``.
- `prose_dependency`: dependency endpoints expected `{'from_component': 'billing-api', 'to_component': 'PostgreSQL'}`, observed `{'from_component': None, 'to_component': None}`.
- `prose_dependency`: candidate labels differed from the hand-authored reference. See the JSON case results.

## Interpretation

- This controlled synthetic corpus is small and intentionally includes the supported structured syntax. It is not a representative organisational dataset.
- Labels were written for these fixtures; this is deterministic rule evaluation, not an independently validated real employee handover benchmark.
- Exact citation checks establish attribution only, not source truth, semantic entailment, completeness, operational competence or business continuity.
- The potential-conflict metric measures requests for human review, not reliable semantic contradiction resolution.
- Only one source-ACL negative is counted here; comprehensive tenant/project/source enforcement is exercised in separate API tests.
- No model accuracy, onboarding-time reduction, production readiness or financial benefit is claimed.

Precision = matched labelled candidates / all predicted candidates. Recall = matched labelled candidates / all gold candidates. Field accuracy includes missed candidates in its denominator. Kind coverage is the presence of eight labelled entity types, not project reconstruction correctness.

The JSON report retains every fixture label, predicted field, missed positive, false positive and unsupported question. Evaluation gaps are not concealed by the test suite: tests check reproducibility and measurement consistency, rather than forcing every metric to 100%.
