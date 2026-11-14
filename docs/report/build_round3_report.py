"""Rebuild concise product documentation from public repository evidence.

Run from the repository root with an isolated environment; see README.md here.
No application secrets, private account records or provider keys are read.
"""

import hashlib
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from product_sections import build
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "report"
PDF = ROOT / "docs" / "INHERIA_Round3_Final_Product_Report.pdf"
APP_SHA = "55b11e1a8fc2486b738b920cd4c639481890c5be"
EVIDENCE_SHA = "9ed1d05dae8cd1d67b108fb24311246714f8b4f3"
LIVE = "https://inheria.onrender.com"
REPO = "https://github.com/Gauravwakle96/INHERIA"
BASE = REPO + "/blob/" + EVIDENCE_SHA + "/"
GUIDES_BASE = REPO + "/blob/main/"

FONTDIR = Path(reportlab.__file__).parent / "fonts"
for name, filename in [
    ("Vera", "Vera.ttf"),
    ("Vera-Bold", "VeraBd.ttf"),
    ("Vera-Italic", "VeraIt.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONTDIR / filename)))
pdfmetrics.registerFontFamily(
    "Vera",
    normal="Vera",
    bold="Vera-Bold",
    italic="Vera-Italic",
    boldItalic="Vera-Bold",
)
NAVY, INK, TEAL, MUTED, PALE, LINE, AMBER = map(
    HexColor,
    ["#10283A", "#22394B", "#087F80", "#556A7C", "#F0F6F7", "#DCE7EC", "#895C17"],
)
W, H = A4
M = 40
CW = W - 2 * M
STYLES = {
    "body": ParagraphStyle(
        "body", fontName="Vera", fontSize=9.3, leading=13.6, textColor=INK, spaceAfter=7
    ),
    "lead": ParagraphStyle(
        "lead",
        fontName="Vera",
        fontSize=11.2,
        leading=16.5,
        textColor=INK,
        spaceAfter=13,
    ),
    "small": ParagraphStyle(
        "small",
        fontName="Vera",
        fontSize=8,
        leading=11.2,
        textColor=MUTED,
        spaceAfter=6,
    ),
    "cell": ParagraphStyle(
        "cell", fontName="Vera", fontSize=8.3, leading=11.8, textColor=INK
    ),
    "headcell": ParagraphStyle(
        "headcell", fontName="Vera-Bold", fontSize=8.1, leading=11.4, textColor=white
    ),
    "h2": ParagraphStyle(
        "h2",
        fontName="Vera-Bold",
        fontSize=12,
        leading=16.5,
        textColor=NAVY,
        spaceBefore=9,
        spaceAfter=7,
    ),
    "code": ParagraphStyle(
        "code", fontName="Courier", fontSize=8, leading=12, textColor=INK, spaceAfter=7
    ),
}


def p(t, style="body"):
    return Paragraph(t.replace("→", " / "), STYLES[style])


def link(label, url):
    return f'<a href="{escape(url, {chr(34): "&quot;"})}" color="#087F80"><u>{escape(label)}</u></a>'


def evidence(*paths):
    return p(
        "Evidence: "
        + " · ".join(
            link(
                Path(path).name,
                (
                    GUIDES_BASE
                    if path in {"docs/roadmap.md", "docs/operating-guide.md"}
                    else BASE
                )
                + path,
            )
            for path in paths
        ),
        "small",
    )


def tbl(headers, rows, fractions):
    data = [[p(t, "headcell") for t in headers]] + [
        [p(t, "cell") for t in row] for row in rows
    ]
    t = Table(data, colWidths=[CW * f for f in fractions], hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, PALE]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, -1), (-1, -1), 0.6, LINE),
            ]
        )
    )
    return t


def box(title, body, color=TEAL):
    t = Table(
        [[p(f'<font color="{color.hexval()}"><b>{title}</b></font><br/>{body}')]],
        colWidths=[CW],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return t


def arrows(draw, x1, y1, x2, y2, color=TEAL):
    draw.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.5))
    if abs(x2 - x1) >= abs(y2 - y1):
        s = 1 if x2 >= x1 else -1
        pts = [x2, y2, x2 - 5 * s, y2 + 3, x2 - 5 * s, y2 - 3]
    else:
        s = 1 if y2 >= y1 else -1
        pts = [x2, y2, x2 + 3, y2 - 5 * s, x2 - 3, y2 - 5 * s]
    draw.add(Polygon(pts, fillColor=color, strokeColor=color))


def node(draw, x, y, w, h, title, sub="", fill=PALE):
    title_size = 9.2
    while pdfmetrics.stringWidth(title, "Vera-Bold", title_size) > w - 20:
        title_size -= 0.2
    draw.add(
        Rect(x, y, w, h, rx=7, ry=7, fillColor=fill, strokeColor=LINE, strokeWidth=0.7)
    )
    draw.add(
        String(
            x + 10,
            y + h - 19,
            title,
            fontName="Vera-Bold",
            fontSize=title_size,
            fillColor=NAVY,
        )
    )
    for j, line in enumerate(sub.split("|")):
        if line:
            line_size = 7.8
            while pdfmetrics.stringWidth(line, "Vera", line_size) > w - 20:
                line_size -= 0.2
            draw.add(
                String(
                    x + 10,
                    y + h - 35 - j * 12,
                    line,
                    fontName="Vera",
                    fontSize=line_size,
                    fillColor=MUTED,
                )
            )


def journey():
    d = Drawing(CW, 170)
    labels = [
        ("01 · Connect", "Documents / GitHub"),
        ("02 · Reconstruct", "Candidates / gaps"),
        ("03 · Verify & review", "Exact sources / approval"),
        ("04 · Handover", "Current approved version"),
        ("05 · Accept & validate", "Successor + supervisor"),
        ("06 · Continue", "Ownership + next steps"),
    ]
    nw = (CW - 28) / 3
    for i, (title, sub) in enumerate(labels):
        col = i % 3
        row = i // 3
        x = col * (nw + 14)
        y = 97 if row == 0 else 18
        node(d, x, y, nw, 62, title, sub)
        if col < 2:
            arrows(d, x + nw + 2, y + 31, x + nw + 12, y + 31)
    d.add(Line(CW - 17, 97, CW - 17, 90, strokeColor=TEAL, strokeWidth=1.5))
    d.add(Line(CW - 17, 90, 16, 90, strokeColor=TEAL, strokeWidth=1.5))
    arrows(d, 16, 90, 16, 82)
    d.add(
        String(
            8,
            4,
            "Permission and source-version checks apply at every step.",
            fontName="Vera-Italic",
            fontSize=8,
            fillColor=TEAL,
        )
    )
    return d


def architecture():
    d = Drawing(CW, 265)
    nw = (CW - 24) / 2
    node(
        d,
        0,
        198,
        nw,
        60,
        "React + TypeScript workspace",
        "React Query / Router / React Flow",
    )
    node(
        d,
        nw + 24,
        198,
        nw,
        60,
        "FastAPI REST boundary",
        "Cookie session / CSRF / validation",
    )
    arrows(d, nw + 2, 228, nw + 22, 228)
    node(
        d,
        0,
        111,
        nw,
        66,
        "Sources and privacy filter",
        "GitHub REST / five document formats|Secret quarantine / selected PII",
    )
    node(
        d,
        nw + 24,
        111,
        nw,
        66,
        "Current authority + evidence",
        "Tenant / project / source ACL|Version / exact-quote checks",
    )
    arrows(d, nw + 24 + nw / 2, 196, nw + 24 + nw / 2, 179)
    arrows(d, nw + 24 - 2, 143, nw + 2, 143)
    node(
        d,
        0,
        18,
        nw,
        70,
        "PostgreSQL + SQLAlchemy",
        "Sources / claims / evidence / history|Alembic / atomic checkpoints",
    )
    node(
        d,
        nw + 24,
        18,
        nw,
        70,
        "Knowledge and transfer services",
        "Investigate / review / approve|Accept / assess / gate closure",
    )
    arrows(d, nw / 2, 109, nw / 2, 90)
    arrows(d, nw + 24 + nw / 2, 109, nw + 24 + nw / 2, 90)
    arrows(d, nw + 2, 54, nw + 22, 54)
    return d


def lifecycle():
    d = Drawing(CW, 178)
    nw = (CW - 28) / 3
    labels = [
        ("Source v1", "Original locator / ACL"),
        ("Candidate + citation", "Pending human verification"),
        ("Approved knowledge", "Review identity + timestamp"),
        ("Source v2 / revoked", "Preserve history / remove authority"),
        ("Invalidate downstream", "Claims / report / assessment"),
        ("Revalidate transfer", "Review / reapprove / reconfirm"),
    ]
    for i, (a, b) in enumerate(labels):
        col = i % 3
        y = 100 if i < 3 else 20
        x = col * (nw + 14)
        node(d, x, y, nw, 62, a, b)
        if col < 2:
            arrows(d, x + nw + 2, y + 31, x + nw + 12, y + 31)
    d.add(Line(CW - 17, 100, CW - 17, 92, strokeColor=AMBER, strokeWidth=1.5))
    d.add(Line(CW - 17, 92, 16, 92, strokeColor=AMBER, strokeWidth=1.5))
    arrows(d, 16, 92, 16, 84, AMBER)
    return d


PAGES = build(
    p,
    tbl,
    box,
    evidence,
    link,
    journey,
    architecture,
    lifecycle,
    REPO,
    BASE,
    GUIDES_BASE,
    LIVE,
)


def render():
    c = canvas.Canvas(str(PDF), pagesize=A4, pageCompression=1)
    c.setTitle("INHERIA | Product Documentation")
    c.setAuthor("Team JAEGERS")
    c.setSubject(
        "Product workflow, architecture, setup, operations, security, quality, roadmap and future scope"
    )
    layout = []
    for idx, (title, subtitle, items) in enumerate(PAGES):
        n = idx + 1
        c.setFillColor(NAVY)
        c.rect(0, H - 13, W, 13, stroke=0, fill=1)
        c.setFont("Vera-Bold", 10)
        c.setFillColor(NAVY)
        c.drawString(M, H - 38, "INHERIA")
        c.setFont("Vera", 7)
        c.setFillColor(MUTED)
        c.drawRightString(W - M, H - 38, "PRODUCT DOCUMENTATION")
        c.setFont("Vera-Bold", 8)
        c.setFillColor(TEAL)
        c.drawString(M, H - 69, subtitle.replace("→", "/"))
        heading = Paragraph(
            title,
            ParagraphStyle(
                "title", fontName="Vera-Bold", fontSize=23, leading=28, textColor=NAVY
            ),
        )
        _, hh = heading.wrap(CW, 100)
        heading.drawOn(c, M, H - 84 - hh)
        y = H - 98 - hh
        c.bookmarkPage(f"page-{n}")
        c.addOutlineEntry(title, f"page-{n}", 0, False)
        bounds = []
        for item in items:
            _iw, ih = item.wrap(CW, 700)
            if y - ih < 46:
                raise ValueError(
                    f"Page {n} overflow: {title}: y={y:.1f}, item={ih:.1f}"
                )
            item.drawOn(c, M, y - ih)
            bounds.append(
                {"top": round(y, 2), "bottom": round(y - ih, 2), "height": round(ih, 2)}
            )
            y -= ih + 5
        c.setStrokeColor(LINE)
        c.line(M, 37, W - M, 37)
        c.setFont("Vera", 7)
        c.setFillColor(MUTED)
        c.drawString(
            M,
            23,
            "People leave. Knowledge lives on. | Technical and operating reference",
        )
        c.drawRightString(W - M, 23, f"{n:02d} / {len(PAGES):02d}")
        layout.append(
            {"page": n, "title": title, "bottom": round(y, 2), "items": bounds}
        )
        c.showPage()
    c.save()
    (OUT / "layout-check.json").write_text(
        json.dumps(layout, indent=2), encoding="utf-8", newline="\n"
    )
    manifest = {
        "pages": len(PAGES),
        "filename": PDF.name,
        "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "application_commit": APP_SHA,
        "evidence_commit": EVIDENCE_SHA,
        "sources": "Public repository documentation and recorded evaluation; original vector diagrams.",
        "scope": "Concise product documentation, development roadmap and future scope; no scenario narrative.",
        "unfamiliar_user_study": "Not claimed; observations not supplied.",
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )
    target = Path("C:/documents")
    if target.exists():
        shutil.copy2(PDF, target / "INHERIA_Product_Documentation_Final.pdf")
        try:
            shutil.copy2(PDF, target / PDF.name)
        except PermissionError:
            shutil.copy2(
                PDF, target / "INHERIA_Round3_Final_Product_Report_Revised.pdf"
            )
    print(
        json.dumps(
            {"pdf": str(PDF), "pages": len(PAGES), "bytes": PDF.stat().st_size},
            indent=2,
        )
    )


if __name__ == "__main__":
    render()
