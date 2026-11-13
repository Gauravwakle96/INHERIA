# Frozen acceptance corpus

These records describe authored, fictional test situations, not company records or
independent employee assessments. Labels were written before the first evaluation
run on this corpus. Existing `app.evaluation.CASES` remain development fixtures.
The new corpus is separately authored and frozen after development changes;
after results have been inspected it becomes a regression set. Any subsequent
tuning must be reported and evaluated on another fresh set.

Extraction labels specify kind, title and explicit fields; missed candidates count
as field failures. Chat questions specify supporting facts or reasons to abstain,
including missing, old, conflicting and permission-restricted evidence. Public
reports distinguish real provider calls from fallback or mocked contract tests.
An exact source link is a structural check, not semantic correctness or proof that
the organisation's source is true. Automated rubric checks need human review.

No private source, login, API credential or live application database is used by
the evaluators. The optional live chat runner accepts a key from an environment
variable, sends only the authored corpus, and caps concurrency and output budgets.
