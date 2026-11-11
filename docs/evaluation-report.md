# INHERIA controlled synthetic evaluation

60 hand-labelled case-study documents (including 23 prose cases) plus one source-ACL negative; isolated in-memory SQLite; no live LLM calls.

Fixture `labelled-continuity-v2`; SHA-256 `012bd2963ea604134e90e3b87d2beed60969d637cb21bae616d6192331fe523c`.

Run from `backend`: `uv run python -m app.evaluation`. The command uses an isolated in-memory database and makes no external AI requests.

| Measure | Numerator / denominator | Rate |
| --- | ---: | ---: |
| candidate kind and title: precision | 46 / 47 | 97.9% |
| candidate kind and title: recall | 46 / 46 | 100.0% |
| owner mapping | 19 / 19 | 100.0% |
| decision rationale field | 11 / 11 | 100.0% |
| dependency endpoints | 9 / 9 | 100.0% |
| project state kind coverage | 8 / 8 | 100.0% |
| exact source citations | 47 / 47 | 100.0% |
| claims with citations | 47 / 47 | 100.0% |
| pending before human review | 47 / 47 | 100.0% |
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
| unknown responsibility owner: precision | 2 / 2 | 100.0% |
| unknown responsibility owner: recall | 2 / 2 | 100.0% |

## Observed errors and limits

- `prose_uncertain_1`: candidate labels differed from the hand-authored reference. See the JSON case results.

## Interpretation

- This controlled synthetic corpus is small and intentionally includes the supported structured syntax. It is not a representative organisational dataset.
- No held-out split or independent labelling audit was used. Labels were written for these fixtures; this is deterministic rule evaluation, not an independently validated real employee handover benchmark.
- Exact citation checks establish attribution only, not source truth, semantic entailment, completeness, operational competence or business continuity.
- The potential-conflict metric measures requests for human review, not reliable semantic contradiction resolution.
- Only one source-ACL negative is counted here; comprehensive tenant/project/source enforcement is exercised in separate API tests.
- No model accuracy, onboarding-time reduction, production readiness or financial benefit is claimed.

Precision = matched labelled candidates / all predicted candidates. Recall = matched labelled candidates / all gold candidates. Field accuracy includes missed candidates in its denominator. Kind coverage is the presence of eight labelled entity types, not project reconstruction correctness.

The JSON report retains every fixture label, predicted field, missed positive, false positive and unsupported question. Evaluation gaps are not concealed by the test suite: tests check reproducibility and measurement consistency, rather than forcing every metric to 100%.
