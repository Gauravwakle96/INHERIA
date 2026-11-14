# Round 3 visual product report

The [19-page PDF](../INHERIA_Round3_Final_Product_Report.pdf) describes the final
working source-to-continuation product, the exact three confirmed commitments,
test/evaluation evidence, privacy/security/accessibility, setup and an ordered
roadmap. It uses existing authorised product screenshots and original vector
diagrams, with clickable frozen evidence links, page bookmarks and a live-product
QR code.

Application evidence is pinned to `55b11e1`; documentation evidence to `9ed1d05`.
PDF build/inspection is separate from the application's already recorded tests.
No private account data, credential files or provider keys are read by the builder.

## Rebuild in a separate tool environment

From the repository root, using Python and uv:

```powershell
uv venv .local/pdf-build-env
uv pip install --python .local/pdf-build-env/Scripts/python.exe -r docs/report/requirements.txt
.local/pdf-build-env/Scripts/python.exe docs/report/build_round3_report.py
.local/pdf-build-env/Scripts/python.exe docs/report/verify_round3_report.py
```

On Linux/macOS use `.local/pdf-build-env/bin/python` for the Python executable.
The optional copy to `C:/documents` occurs only if that directory exists. PDF
rendered review images are written under ignored `.local/round3-pdf-review`.
The generator and verification script are the editable source. The output manifest
records the actual PDF SHA-256 and evidence commits. Regeneration can change the
PDF's build timestamp/ID and therefore its hash.

## Remaining team-owned submission details

- Actual individual contributions require confirmation. The report transcribes
  the existing Round 1 roster/assigned roles and does not claim those assignments
  prove personal delivery. Do not infer participant contributions from the
  ShopEase case-study identities.
- No unfamiliar-user observations were supplied. The report does not invent a
  five-person study; the repository includes a task pack for real sessions.
- Publish/share the final PDF for judges and verify submitted links in a private
  window. A public GitHub PDF is available after push; if the form requires Drive,
  upload it and select “Anyone with the link” as Viewer.
- The form is not submitted and personal confirmations are not ticked by this work.

ReportLab's bundled Bitstream Vera fonts are used under their bundled font
licence. PyMuPDF used for rendering is AGPL/commercial licensed; review licence
obligations for distribution/deployment. Tooling is isolated from application
dependency locks.
