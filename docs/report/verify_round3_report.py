"""Check PDF text, links, safe layout and public evidence references.

Renders review pages locally; human visual inspection is recorded separately.
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

import pymupdf as fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/INHERIA_Round3_Final_Product_Report.pdf"
REPORT = ROOT / "docs/report"
REVIEW = ROOT / ".local/round3-pdf-review"
REVIEW.mkdir(parents=True, exist_ok=True)
doc = fitz.open(PDF)
rows = (len(doc) + 3) // 4
sheet = Image.new("RGB", (1200, rows * 435), "#DCE5EB")
draw = ImageDraw.Draw(sheet)
metrics = []
texts = []
local_links = []
guide_links = []
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6))
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im.save(REVIEW / f"page-{i + 1:02d}.png")
    thumb = im.copy()
    thumb.thumbnail((282, 395))
    x = 9 + (i % 4) * 300
    y = 8 + (i // 4) * 435
    sheet.paste(thumb, (x, y))
    draw.text((x, y + 402), f"{i + 1:02d}", fill="#10283A")
    text = page.get_text()
    texts.append(text)
    outside = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if (
                    x0 < 25
                    or x1 > page.rect.width - 25
                    or y0 < 15
                    or y1 > page.rect.height - 15
                ):
                    outside.append(span["text"])
    links = page.get_links()
    for entry in links:
        url = entry.get("uri", "")
        guide_match = re.match(
            r"https://github.com/Gauravwakle96/INHERIA/blob/main/(.*)", url
        )
        if guide_match:
            guide_path = unquote(guide_match.group(1).split("#")[0])
            guide_links.append(
                {
                    "page": i + 1,
                    "path": guide_path,
                    "exists_locally": (ROOT / guide_path).is_file(),
                }
            )
        match = re.match(
            r"https://github.com/Gauravwakle96/INHERIA/blob/([a-f0-9]{40})/(.*)", url
        )
        if match:
            sha, path = match.groups()
            path = unquote(path.split("#")[0])
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{sha}:{path}"],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            local_links.append(
                {
                    "page": i + 1,
                    "path": path,
                    "exists_at_evidence_commit": result.returncode == 0,
                }
            )
    metrics.append(
        {
            "page": i + 1,
            "characters": len(text),
            "links": len(links),
            "bad_glyphs": text.count("\ufffd") + text.count("\x00"),
            "outside_safe_page": outside,
        }
    )
sheet.save(REVIEW / "contact-sheet.png")
combined = "\n\n".join(texts)
(REVIEW / "text.txt").write_text(combined, encoding="utf-8")
secret = bool(
    re.search(
        r"\bsk-[A-Za-z0-9_-]{15,}|postgres(?:ql)?://[^\s]+:[^\s]+@|gh[pousr]_[A-Za-z0-9]{20,}",
        combined,
    )
)
assert len(doc) == 23
assert len(doc.get_toc()) == 23
assert "Work dates and evidence scope" not in combined
assert "Repository created" not in combined
assert not secret
assert all(
    p["characters"] > 700 and not p["bad_glyphs"] and not p["outside_safe_page"]
    for p in metrics
), metrics
assert all(l["exists_at_evidence_commit"] for l in local_links), local_links
assert all(l["exists_locally"] for l in guide_links), guide_links
for value in [
    "Secure Team Onboarding",
    "Practical Transfer Validation",
    "239",
    "19/20",
    "11/12",
    "Gaurav Wakle",
    "Pranad Bhale",
    "Savinay Pathak",
    "Rudransh Jaiswal",
    "INHERIA_DATABASE_URL",
    "agnes-2.5-flash",
    "M1 · Independent reconstruction quality",
    "Operating guide and release maintenance",
]:
    assert value in " ".join(combined.split()), value
report = {
    "pages": len(doc),
    "bytes": PDF.stat().st_size,
    "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
    "page_checks": metrics,
    "secret_pattern_detected": secret,
    "outline_entries": len(doc.get_toc()),
    "frozen_evidence_links_checked": len(local_links),
    "missing_frozen_evidence_links": [],
    "current_guide_links_checked": len(guide_links),
    "text_layout_links": "passed",
    "visual_review": "See visual-review.md; generated pages inspected separately.",
    "scope": "PDF artefact checks; not a fresh application test, awarded score or verified individual contribution.",
}
(REPORT / "pdf-quality-check.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "pages": len(doc),
            "bytes": PDF.stat().st_size,
            "links": sum(p["links"] for p in metrics),
            "frozen_evidence_links": len(local_links),
            "checks": "passed",
        },
        indent=2,
    )
)
