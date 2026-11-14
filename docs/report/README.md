# INHERIA product documentation

The [13-page PDF](../INHERIA_Round3_Final_Product_Report.pdf) is a concise product
reference: workflow and users, architecture, data/API contracts, security,
evidence lifecycle, installation, operations, recorded quality and limitations.
The roadmap specifies milestone order, user benefit, effort, dependencies and
measurable release gates. Future scope covers staging-CI evidence, controlled
evidence exports, multi-successor coordination and versioned templates.

Original vector diagrams explain the workflow, architecture and evidence
lifecycle. Clickable contents, bookmarks and source references support navigation.
No ShopEase case study, scenario screenshots or work-dates narrative is included.
Application evidence is pinned to `55b11e1`; documentation evidence to `9ed1d05`.
Roadmap and operating-guide links use their current repository versions.

## Rebuild separately from application dependencies

From the repository root, using Python and uv:

```powershell
uv venv .local/pdf-build-env
uv pip install --python .local/pdf-build-env/Scripts/python.exe -r docs/report/requirements.txt
.local/pdf-build-env/Scripts/python.exe docs/report/build_round3_report.py
.local/pdf-build-env/Scripts/python.exe docs/report/verify_round3_report.py
```

On Linux/macOS use `.local/pdf-build-env/bin/python`. The builder uses
`product_sections.py` and the layout/diagram helpers in `build_round3_report.py`.
It reads no private accounts, credential files or provider keys.

If `C:/documents` exists, a copy is saved as
`INHERIA_Product_Documentation_Final.pdf`. A locked older Round 3 filename uses a
`_Revised.pdf` fallback. Rendered inspection pages are stored under ignored
`.local/round3-pdf-review`.

The manifest records the PDF SHA-256 and evidence revisions. Verification checks
page count, bookmarks, navigation, frozen-source/current-guide references, text
bounds, glyphs and credential patterns. Visual inspection is recorded separately
in [visual-review.md](visual-review.md). Rebuilding can change the PDF timestamp/ID
and therefore its hash. These are document checks, not new application tests.

## Publication and scope

The PDF is public through this repository. If the submission requires Drive,
upload the final file and select “Anyone with the link” as Viewer. Verify the
submitted links in a private window. Form submission, participant contributions
and personal confirmations remain with the team leader.

Recorded tests retain their original limitations. No unfamiliar-user study or
independent enterprise accuracy is invented. Future targets remain planned.

ReportLab's bundled Bitstream Vera fonts retain their font licence. PyMuPDF used
for inspection is AGPL/commercial licensed; review applicable obligations.
Report tooling remains isolated from application dependency locks.
