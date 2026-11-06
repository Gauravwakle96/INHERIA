# Connectors, source limits and research datasets

Implementation and documentation checked on 6 November 2026. A repository licence, a dataset licence, API access conditions and permission to disclose a source are separate decisions. Public contributor activity is not employee responsibility or handover ground truth.

## Working connectors

| Source | Actual implementation | Authentication and limits |
| --- | --- | --- |
| GitHub | Functional REST adapter: repository metadata, README, bounded repository structure and documents, commits, pull requests, issues and releases | Public repositories work without a token. Private repositories use a server-encrypted personal access token. GitHub OAuth app installation and webhooks are not implemented. |
| PDF | PyMuPDF 2.1 text extraction with original page references | 10 MB input; at most 200 pages. Encrypted PDFs must be unlocked. Scanned PDFs require OCR before upload; no integrated OCR is claimed. |
| DOCX | python-docx paragraph, heading and table extraction | 10 MB input; total ZIP expansion at most 20 MB, at most 2,000 ZIP entries, compression-ratio checks. DOC/DOCM are unsupported. |
| Markdown / TXT | UTF-8 text, heading and line references | 10 MB input; binary data and invalid UTF-8 are rejected. |
| JSON | Parsed values with JSON-path references | UTF-8, valid JSON, at most 40 levels of nesting; bounded object/list traversal. This is generic authorised document ingestion, not a specialised dataset import adapter. |
| Jira, Confluence, Slack, Teams, GitLab, Azure DevOps, Google Drive, ServiceNow | Coming Soon | No credentials are requested and no connected status is displayed for an unimplemented adapter. |

Per source, indexing stops at 100,000 extracted characters or 200 chunks. Truncation appears in source metadata. Probable passwords, tokens, credential URLs and private keys quarantine the document without persisting its raw file or extracted body. Personal email and phone values are redacted; reserved `.example`, `.invalid` and `.test` identities are synthetic exceptions. Detection is pattern based and has false positives and false negatives; it is not a comprehensive data-loss prevention system.

GitHub requests use the fixed `https://api.github.com` origin, verify TLS and refuse authenticated redirects and unsafe pagination links. The default request budget is 30 per job. Collections are capped at two pages of 100 records; releases at one page. Up to five additional Markdown/TXT documents are retrieved. Structure is marked partial when GitHub reports truncation or the retained path limit is exceeded. The connector does not clone or execute repository code.

Metadata and document endpoints use ETags. Completed, non-partial synchronisation advances the timestamp used for incremental commits/issues and sorted pull requests. Partial jobs retain the prior cursor so a truncated history is not represented as complete. Repeated unchanged content is detected within its existing source and ACL scope. A duplicate never widens source permissions. Source changes keep historical chunk versions and invalidate dependent claims. Explicitly revoked sources stay excluded; reconnecting an integration restores only sources revoked with that integration.

Network/server retries are bounded to three attempts with short backoff. Rate limits, invalid authentication, access denial and moved repositories produce safe, persisted failure states instead of long blocking waits. Jobs are database-backed and run in bounded FastAPI background tasks; durable distributed workers, automatic webhook processing and enterprise-scale throughput are future work.

GitHub 401, permission-denied 403 and repository 404 failures mark previously cached connected sources unavailable and invalidate their claims. Primary/secondary rate limits, server outages and network failures keep the earlier authorised cache available while showing sync failure; they are not misreported as revoked permissions. A definite README/file 404 or an explicitly complete, bounded repository tree that excludes a previously known file also invalidates that file's cached claims. Partial trees and omitted completeness flags never establish deletion. Restored access or a recreated file produces a new source version and pending claims; it does not restore prior human approval automatically.

Private token storage requires `INHERIA_TOKEN_ENCRYPTION_KEY`, a valid Fernet key. Tokens are never returned to the frontend or included in source metadata, errors or audit details. This PAT flow is a partial implementation of the original OAuth requirement. The deployment owner must restrict PAT repository selection and permissions; a connected GitHub account does not imply permission to process every repository or disclose all returned sources.

### Observed integration verification

The live `fastapi/fastapi` REST smoke test returned 510 locatable source documents in 15 requests: two repository/structure documents, six Markdown documents, 200 commits, 200 pull requests, two issues and 100 releases. The result correctly reported partial history. This was a read-only connector test; it did not verify employee ownership, semantic reconstruction accuracy or a complete FastAPI handover. Django and Prometheus licence files were researched; their repositories were not fully synchronised in this verification.

The ingestion and connector tests cover real two-page PDF text extraction, DOCX paragraphs/tables, invalid formats, document limits, invalid JSON, secret quarantine, PII redaction, ACL-safe duplicates, retained historical citations, source revocation/deletion, GitHub pagination, unsafe redirect/link rejection, encrypted tokens, authentication/rate limits, bounded retries, incremental request parameters and persisted failed jobs.

### Parser licensing

[PyMuPDF's official licensing documentation](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) states that PyMuPDF and MuPDF are available under the AGPL and commercial agreements. The installed parser is PyMuPDF 2.1. Before a proprietary deployment, satisfy the AGPL obligations, obtain an appropriate Artifex commercial licence, or replace the parser with a licence-compatible alternative. Installing the package does not resolve that deployment decision.

## Public repository research

| Repository | Verified code licence | Appropriate use | Actual status |
| --- | --- | --- | --- |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) | Small initial connector/reconstruction demonstration with citations and explicit unknowns | Live bounded REST retrieval verified; licence researched |
| [django/django](https://github.com/django/django) | [BSD 3-Clause](https://github.com/django/django/blob/main/LICENSE) | Mature project history and issue/decision reconstruction tests | Licence researched; selectable using the generic GitHub connector; no full sync result claimed |
| [prometheus/prometheus](https://github.com/prometheus/prometheus) | [Apache 2.0](https://github.com/prometheus/prometheus/blob/main/LICENSE) | Go service/operational documentation and dependency test cases | Licence researched; selectable using the generic GitHub connector; no full sync result claimed |

Preserve required licence/copyright notices and source attribution when redistributing code or documentation. Issue descriptions, comments and contributor records can have third-party rights and personal information; the repository's code licence does not automatically settle every API record's processing or redistribution conditions. INHERIA does not contact contributors or infer employee departures from public activity.

## Dataset investigation

All entries below are **researched, not ingested**. No specialised dataset connector, dataset download, benchmark execution or dataset-derived handover claim is implemented. A user may upload a small, permitted UTF-8 JSON/Markdown export using the generic document parser, subject to the same source permissions and privacy checks. Arbitrary downloaded patches, installation scripts, Dockerfiles and test commands are treated as untrusted data and are never executed by INHERIA.

| Dataset / archive | Verified purpose | Licence / access finding | Suitable later use |
| --- | --- | --- | --- |
| [SWE-bench](https://github.com/SWE-bench/SWE-bench) | Given a real GitHub issue and codebase, evaluate a patch that resolves the issue; task records preserve repository, base revision, problem and tests | [Framework repository is MIT](https://github.com/SWE-bench/SWE-bench/blob/main/LICENSE). Review the selected dataset card and each upstream repository's rights separately. | Issue/PR reconstruction and citation evaluation; patch correctness is not responsibility-transfer or employee-readiness ground truth. |
| [SWE-rebench](https://huggingface.co/datasets/nebius/SWE-rebench) | Automated collection and validation of real software issue/PR tasks, with repository, base commit, problem statement, patches, tests and repository licence fields | [Official dataset card](https://huggingface.co/datasets/nebius/SWE-rebench/blob/main/README.md) declares CC BY 4.0 and explicitly requires respecting each repository's licence. | Broader issue/history reconstruction tests; maintain upstream attribution and held-out evaluation splits. |
| [SWE-rebench V2](https://huggingface.co/datasets/nebius/SWE-rebench-V2) | Multilingual software-engineering tasks and task-interface metadata | Dataset card declares CC BY 4.0 with per-repository licence requirements. [Builder tools](https://github.com/SWE-rebench/SWE-rebench-V2/blob/main/LICENSE) are MIT, which is distinct from the dataset licence. The card warns about benchmark overlap. | Future multilingual extraction tests, with overlap checks and independent handover labels. |
| [GH Archive](https://www.gharchive.org/) | Recorded public GitHub event history for historical activity analysis | [Official repository README](https://github.com/igrigorik/gharchive.org/blob/master/README.md) specifies MIT for repository code/docs and CC BY 4.0 for website content. It explicitly states that the event dataset is outside that repository and may contain third-party rights. A blanket MIT dataset licence was not established. | Historical activity and sync-completeness analysis, with event coverage and privacy limitations. |
| [GHTorrent](https://ghtorrent.org/) | Raw and linked GitHub API entities for repository/process analysis; [download docs](https://github.com/ghtorrent/ghtorrent.org/blob/master/downloads.md) warn that incremental raw dumps can contain duplicates | [Official FAQ](https://github.com/ghtorrent/ghtorrent.org/blob/master/faq.md) describes CC BY-SA 4.0 for non-commercial uses and separate maintainer arrangements for commercial use. The FAQ also states no data quality guarantee and possible stale/incomplete records. | Historical relationship and duplicate handling tests after confirming licence and archive availability. |
| [Software Heritage](https://docs.softwareheritage.org/) | Source-code preservation, origins, revisions, releases, directories, snapshots, content and persistent SWH identifiers | [Live API reference](https://archive.softwareheritage.org/api/1/) exposes archive and provenance endpoints and content-licence metadata. Documentation links [API terms](https://www.softwareheritage.org/aspects-juridiques/software-heritage-api-terms-of-use/). No universal licence covering every archived source was established in the fetched references. The main website had a TLS trust-chain failure in this environment; certificate verification was preserved. | Stable historical evidence/reference tests that retain original repository licences and archive provenance; no current adapter. |

The closed Nexora demonstration and `app.evaluation` controlled fixtures are the only labelled synthetic continuity ground truth in this implementation. The evaluation report documents their small scope, difficult cases and measured failures. Public software benchmarks cannot establish actual employee expertise, informal responsibilities, transition acceptance or operational competence without separately authorised human labels.

## Primary documentation consulted

- [GitHub REST pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api): follow validated `Link` URLs; respect endpoint page limits.
- [PyMuPDF tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html): in-memory PDF opening, page text extraction and page numbering.
- [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).
- Repository licence files and dataset cards linked above were actually fetched. Research does not imply that every repository, dataset or production integration has been tested.
