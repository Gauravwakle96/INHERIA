# Executed isolated local operational exercise
Procedure: recovery test evidence
System: recovery
Test environment: isolated local staging (toy service and SQLite)
Run ID: local-5e6d5b8121e3
Timestamp: 2026-11-13T22:15:36.777244+00:00
Artifact: sha256:386bbf6fe96ce8b63979366ea013f9d3c3a0d99150cee1d644abab0727a5a5e0
Observation: version v1 returned HTTP 200 with three orders; broken-v2 returned
HTTP 503. Rollback to v1 restored HTTP 200. An empty backup failed restore
validation with zero orders. The correct backup restored three orders totaling
800, and SQLite integrity_check returned ok.
Result: passed after the incorrect backup was rejected and the correct backup selected.
Evidence file: docs/local-operational-exercise.json
Executed by: coding agent in an isolated local test environment.
This records actual local execution, not Wipro/AWS/production activity or a
qualified human supervisor's assessment. It does not prove INHERIA PostgreSQL
backup/restore readiness. A separate supervisor must review its relevance.
