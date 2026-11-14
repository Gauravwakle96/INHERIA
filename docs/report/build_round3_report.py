"""Rebuild the visual Round 3 report using public repository evidence only.

Run from the repository root with an isolated environment; see README.md here.
No application secrets, private account records or provider keys are read.
"""

import hashlib
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PILImage
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from roadmap_sections import enhance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "report"
ASSETS = OUT / "generated-assets"
PDF = ROOT / "docs" / "INHERIA_Round3_Final_Product_Report.pdf"
APP_SHA = "55b11e1a8fc2486b738b920cd4c639481890c5be"
EVIDENCE_SHA = "9ed1d05dae8cd1d67b108fb24311246714f8b4f3"
LIVE = "https://inheria.onrender.com"
REPO = "https://github.com/Gauravwakle96/INHERIA"
BASE = REPO + "/blob/" + EVIDENCE_SHA + "/"
GUIDES_BASE = REPO + "/blob/main/"
CI = REPO + "/actions/runs/43612957597"
ASSETS.mkdir(parents=True, exist_ok=True)

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


def screenshot(name, crop=None, width=CW, maxheight=290):
    src = ROOT / "docs" / "screenshots" / name
    im = PILImage.open(src)
    if crop:
        im = im.crop(crop)
        src = ASSETS / (Path(name).stem + "-crop.png")
        im.save(src)
    iw, ih = im.size
    height = width * ih / iw
    if height > maxheight:
        width *= maxheight / height
        height = maxheight
    return Image(str(src), width=width, height=height, hAlign="CENTER")


def cover_visual():
    pic = screenshot(
        "03-overview.png", crop=(251, 87, 1419, 1000), width=CW * 0.65, maxheight=250
    )
    d = Drawing(CW * 0.29, 220)
    q = QrCodeWidget(LIVE)
    x0, y0, x1, y1 = q.getBounds()
    size = 112
    qr = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    qr.add(q)
    d.add(qr)
    d.add(
        String(
            3,
            141,
            "OPEN THE PRODUCT",
            fontName="Vera-Bold",
            fontSize=8.6,
            fillColor=TEAL,
        )
    )
    d.add(
        String(
            3, 124, "inheria.onrender.com", fontName="Vera", fontSize=8, fillColor=INK
        )
    )
    d.add(
        String(
            3,
            182,
            "Gaurav → Savinay".replace("→", "to"),
            fontName="Vera-Bold",
            fontSize=10,
            fillColor=NAVY,
        )
    )
    d.add(
        String(
            3,
            166,
            "A reviewed DevOps handover",
            fontName="Vera",
            fontSize=7.5,
            fillColor=MUTED,
        )
    )
    t = Table([[pic, d]], colWidths=[CW * 0.68, CW * 0.32])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
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
    draw.add(
        Rect(x, y, w, h, rx=7, ry=7, fillColor=fill, strokeColor=LINE, strokeWidth=0.7)
    )
    draw.add(
        String(
            x + 10,
            y + h - 19,
            title,
            fontName="Vera-Bold",
            fontSize=9.2,
            fillColor=NAVY,
        )
    )
    for j, line in enumerate(sub.split("|")):
        if line:
            draw.add(
                String(
                    x + 10,
                    y + h - 35 - j * 12,
                    line,
                    fontName="Vera",
                    fontSize=7.8,
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
    arrows(d, 16, 98, 16, 84, AMBER)
    return d


def field_chart(report):
    d = Drawing(CW, 168)
    entries = [
        ("Candidate precision", report["candidate"]["precision"], 0.9),
        ("Owner accuracy", report["fields"]["owner"], 0.85),
        ("Rationale accuracy", report["fields"]["rationale"], 0.85),
        ("Dependency fields", report["fields"]["dependency"], 0.85),
    ]
    left = 143
    length = 270
    for i, (label, v, target) in enumerate(entries):
        y = 132 - i * 32
        d.add(String(0, y + 3, label, fontName="Vera", fontSize=8.5, fillColor=INK))
        d.add(Rect(left, y - 1, length, 15, fillColor=PALE, strokeColor=None))
        d.add(
            Rect(left, y - 1, length * v["rate"], 15, fillColor=TEAL, strokeColor=None)
        )
        d.add(
            Line(
                left + length * target,
                y - 5,
                left + length * target,
                y + 19,
                strokeColor=AMBER,
                strokeWidth=1.5,
            )
        )
        d.add(
            String(
                left + length + 10,
                y + 3,
                f"{v['numerator']}/{v['denominator']}",
                fontName="Vera-Bold",
                fontSize=9,
                fillColor=NAVY,
            )
        )
    d.add(
        String(
            left,
            2,
            "Amber marker = submitted target. Scale: 0 to 100%.",
            fontName="Vera",
            fontSize=8,
            fillColor=MUTED,
        )
    )
    return d


def metrics():
    d = Drawing(CW, 90)
    cards = [
        ("239", "Backend tests passed"),
        ("17", "Real PostgreSQL cases"),
        ("34/34", "Exact-three journeys"),
    ]
    width = (CW - 20) / 3
    for i, (val, label) in enumerate(cards):
        x = i * (width + 10)
        d.add(Rect(x, 10, width, 76, rx=7, ry=7, fillColor=PALE, strokeColor=LINE))
        d.add(
            String(x + 12, 48, val, fontName="Vera-Bold", fontSize=27, fillColor=TEAL)
        )
        d.add(String(x + 12, 26, label, fontName="Vera", fontSize=8, fillColor=INK))
    return d


PAGES = []


def page(title, subtitle, items):
    PAGES.append((title, subtitle, items))


page(
    "Knowledge that stays usable.",
    "FINAL PRODUCT REPORT · ROUND 3 · TEAM JAEGERS",
    [
        p("INHERIA", "h2"),
        p(
            "<b>People leave. Knowledge lives on.</b><br/>Technical knowledge continuity, from authorised sources to accepted responsibility and a reviewed continuation plan.",
            "lead",
        ),
        cover_visual(),
        p(
            "Live ShopEase judge workspace. Authored DevOps case study; captured 14 November 2026.",
            "small",
        ),
        journey(),
        box(
            "Open the working product",
            link("inheria.onrender.com", LIVE)
            + "<br/>"
            + link("Public source code · Gauravwakle96/INHERIA", REPO)
            + "<br/>Choose <b>Open judge workspace</b> or <b>Try a fresh handover</b>. No core-workflow API key or shared password required.",
        ),
        p(
            "Gaurav Wakle · Pranad Bhale · Savinay Pathak · Rudransh Jaiswal<br/>MIT, Chhatrapati Sambhajinagar. Roster transcribed from the Round 1 proposal.",
            "small",
        ),
    ],
)

page(
    "Try the product without a walkthrough.",
    "JUDGE QUICK START · LINKS, ROLES AND EXPECTED RESULTS",
    [
        p(
            "Open the live link in a private window. The sign-in screen gives judges a complete example and a separate fresh workflow.",
            "lead",
        ),
        screenshot("01-judge-entry.png", maxheight=225),
        tbl(
            ["Entry", "What the judge receives"],
            [
                [
                    "<b>Open judge workspace</b>",
                    "Completed ShopEase example: 51 sources, 81 claim records, 8 accepted responsibilities and 11 reviewed walkthroughs. Inspect evidence and remaining work.",
                ],
                [
                    "<b>Try a fresh handover</b>",
                    "13 authorised case-study sources and an unapproved transition. Reconstruct, review and perform the transfer yourself.",
                ],
                [
                    "<b>Explore demo</b>",
                    "Scenario and role guide at "
                    + link("/demo", LIVE + "/demo")
                    + ". Real teammates use separate accounts in one project.",
                ],
            ],
            [0.29, 0.71],
        ),
        p("Follow this short inspection", "h2"),
        p(
            "1. Open a knowledge record and inspect its source quotation, version and locator.<br/>2. Inspect Handover, acceptance and separate supervisor review.<br/>3. Switch to Savinay in the case-study topbar; open My continuation plan.<br/>4. Use fresh mode to upload permitted text, run Investigation and review candidates.<br/>5. Try a missing prerequisite: Close transition remains blocked and points to the next action."
        ),
        box(
            "Access and hosting expectations",
            "Visits are separate, expiring workspaces (four-hour default). Demo role switching is restricted to that visitor. Render Free can need about a minute to wake; quota/capacity failures show a retryable message. The README also provides a verified local installation path.",
        ),
        evidence(
            "README.md",
            "docs/final-product-readiness.md",
            "docs/judge-upgrade-target-verification.json",
        ),
    ],
)

page(
    "A DevOps engineer leaves ShopEase.",
    "PROBLEM, USERS AND THE CHOSEN CONTINUITY OUTCOME",
    [
        p(
            "A shopping application still needs safe releases, monitoring and recovery when its experienced DevOps engineer leaves. Files alone do not tell the successor what is current, who owns it or what remains unresolved.",
            "lead",
        ),
        tbl(
            ["Person", "Role and contribution to the handover"],
            [
                [
                    "<b>Gaurav</b><br/>Departing engineer",
                    "Explains release routines, rollback restrictions, troubleshooting and implicit duties. Reviews candidate ownership and answers gap-driven questions.",
                ],
                [
                    "<b>Savinay</b><br/>Incoming engineer",
                    "Inspects approved evidence, requests missing knowledge access, accepts or rejects responsibility and submits cited validation work.",
                ],
                [
                    "<b>Rudransh</b><br/>Coordinator / reviewer",
                    "Connects sources, manages membership, arranges authorised technical review, approves the current handover and verifies closure gates.",
                ],
            ],
            [0.27, 0.73],
        ),
        p("What actually transfers?", "h2"),
        tbl(
            ["Knowledge bundle", "Relevant material and unresolved risks"],
            [
                [
                    "Release and rollback",
                    "Pipeline configuration, runbooks, health checks, approval boundaries, schema-change constraints and deployment failures.",
                ],
                [
                    "Infrastructure and operations",
                    "Infrastructure configuration, monitoring alerts, incident history, escalation contacts and recurring maintenance.",
                ],
                [
                    "Backup and recovery",
                    "Backup responsibility, restore-test references, recovery prerequisites and missing or outdated recovery evidence.",
                ],
                [
                    "Project context",
                    "Architecture, decision rationale, service dependencies, open tasks and responsibility/backup gaps.",
                ],
            ],
            [0.30, 0.70],
        ),
        box(
            "Credible outcome",
            "The successor receives current, reviewed knowledge and explicitly accepts ownership. Missing evidence becomes a visible task or blocker. Completion preserves open operational issues with accountable follow-up; it does not claim every incident or cloud recovery was solved.",
        ),
        p(
            "ShopEase and its role identities are authored demonstration material, not Wipro/client operational records. Scenario actions are case-study history, not independent assessments or actual participant contributions.",
            "small",
        ),
        evidence("README.md", "docs/feature-status.md"),
    ],
)

page(
    "The central workflow is complete.",
    "CONNECT → RECONSTRUCT → VERIFY → REVIEW → HANDOVER → CONTINUE",
    [
        journey(),
        tbl(
            ["Step", "Implemented behaviour", "Visible continuation result"],
            [
                [
                    "Connect",
                    "GitHub REST/PAT; PDF, DOCX, MD, TXT, JSON ingestion.",
                    "Source status, locator, timestamp, ACL and version.",
                ],
                [
                    "Reconstruct",
                    "Bounded source investigation and explicit English extraction.",
                    "Candidates, decisions, duties, dependencies, gaps.",
                ],
                [
                    "Verify",
                    "Exact evidence quotes and current source checks.",
                    "Unsupported, stale and conflicting knowledge remains visible.",
                ],
                [
                    "Review",
                    "Authorised correction, approval or rejection; employee explanations independently reviewed.",
                    "Review state and correction/audit history.",
                ],
                [
                    "Handover",
                    "Permission-filtered report, current-version approval and proposed responsibility owner.",
                    "Role-appropriate knowledge and open work.",
                ],
                [
                    "Accept & validate",
                    "Incoming acceptance/rejection; cited scenario submissions; separate supervisor assessment.",
                    "Recovery, reapproval and explicit prerequisite gates.",
                ],
                [
                    "Continue",
                    "Close only when current gates pass; record accepted ownership.",
                    "Successor duties, procedures, source links and next actions.",
                ],
            ],
            [0.18, 0.44, 0.38],
        ),
        screenshot(
            "12-closure-readiness.png", crop=(570, 715, 1410, 998), maxheight=140
        ),
        p(
            "Current readiness in the built local QA case study: eight accepted duties, eleven supervisor-reviewed tasks and 72 current accessible handover records. Changed evidence removes current readiness; these are not production-competence scores.",
            "small",
        ),
        evidence("API_CONTRACT.md", "docs/three-improvements-acceptance.md"),
    ],
)

page(
    "Exactly the three submitted improvements.",
    "PROMISE → DELIVERY → ACCEPTANCE EVIDENCE",
    [
        p(
            "The team-confirmed Round 2 commitments guide this report. Conversational chat is additional functionality and does not replace any of these three.",
            "lead",
        ),
        tbl(
            ["Committed improvement", "Delivered user benefit", "Recorded proof"],
            [
                [
                    "<b>1. Secure Team Onboarding & Access Readiness</b>",
                    "Single-use expiring invitation, self-chosen password, project/document access request and independent decision, revocation and audit.",
                    "7 dedicated journeys; live access checks; PostgreSQL invitation/permission races.",
                ],
                [
                    "<b>2. Investigation & Source-Change Intelligence</b>",
                    "Explicit prose owner/rationale/dependency extraction; cited downstream impact; revalidation after change/removal; source-version checkpoints and resume.",
                    "60 labelled docs (34 prose) initial internal holdout; 10 distinct changes/revocations; 5 interruption positions. Separate later first-run evaluation.",
                ],
                [
                    "<b>3. Practical Transfer Validation & Recovery</b>",
                    "Deployment/rollback/recovery rubrics; cited staging records; correction/reopening; critical prerequisites and traceable reapproval.",
                    "12 positive/negative role flows; complete UI transfer; current and revoked observation evidence checks.",
                ],
            ],
            [0.29, 0.43, 0.28],
        ),
        metrics(),
        box(
            "Delivered scope and measured limits",
            "The dedicated acceptance runner passed 34/34 journeys. Internal evaluation labels are implementation-informed. External staging authenticity and operational competence need authorised records and qualified supervisors. INHERIA executes no production commands.",
        ),
        p("Changes from the broad Round 1 vision", "h2"),
        p(
            "The eleven-engine proposal was narrowed to the technical source-to-continuation journey. Existing components were extended. Industry profiles, workflow builder, cross-company learning, predictive scores and broad autonomous remediation were deferred. PostgreSQL, lexical retrieval and bounded workers keep the deployment understandable and affordable."
        ),
        evidence(
            "docs/three-improvements-acceptance.md",
            "docs/three-improvements-tests.json",
            "docs/round3-form-answers-draft.md",
        ),
    ],
)

page(
    "1 · A usable handover starts with access.",
    "SECURE TEAM ONBOARDING & ACCESS READINESS",
    [
        p(
            "Responsibility assignment does not grant knowledge access. The successor must be able to read the current documents supporting the handover.",
            "lead",
        ),
        tbl(
            ["Mechanism", "Implemented safeguard"],
            [
                [
                    "Invitation",
                    "Random hashed, expiring, single-use token. New recipients set a password; existing recipients authenticate without role/password overwrite.",
                ],
                [
                    "Access request",
                    "Incoming user requests missing knowledge access. A separate authorised source reviewer approves or rejects with a note. Unreadable source titles stay hidden.",
                ],
                [
                    "Document permissions",
                    "Current reader list applies to source text, derived claims, graph, handover, saved history and readiness. Admin does not bypass a source ACL.",
                ],
                [
                    "Revocation",
                    "Project member removal revokes pending requests/invitations and explicit reader grants. Last-reader removal never opens access to everyone.",
                ],
                [
                    "Audit and concurrency",
                    "Invitation/member/access decisions are traceable. PostgreSQL project-row locks and fresh ORM checks prevent stale acceptance/revocation races.",
                ],
            ],
            [0.25, 0.75],
        ),
        p("A judge can exercise this improvement", "h2"),
        box(
            "Try it",
            "Knowledge owners → Invite member → privately open the one-time link → choose a password. Restrict a required source, inspect missing access as the successor, request access and review it as an authorised reviewer. Revoke membership and check denial.",
        ),
        tbl(
            ["Acceptance cases", "Outcome and scope"],
            [
                [
                    "7 dedicated journeys",
                    "Single-use, expiry, independent review, missing-access recovery, membership denial, document-reader updates and last-reader safety.",
                ],
                [
                    "Live + PostgreSQL",
                    "Browser invitation/source-reader checks and bounded overlapping database writes. No enterprise identity certification.",
                ],
            ],
            [0.32, 0.68],
        ),
        p(
            "Limit: links are manually shared. Email delivery, verified email, password reset, SSO/MFA and external AWS/IAM grants remain future work. Project removal does not mean organisation-wide offboarding.",
            "small",
        ),
        evidence(
            "docs/three-improvements-acceptance.md",
            "backend/tests/test_onboarding_completion.py",
            "backend/tests/test_source_access_completion.py",
        ),
    ],
)

page(
    "2 · Source changes cannot leave false readiness.",
    "INVESTIGATION & SOURCE-CHANGE INTELLIGENCE",
    [
        p(
            "Knowledge keeps its provenance through extraction, review and transfer. A changed, deleted or revoked source removes current authority from dependent work.",
            "lead",
        ),
        lifecycle(),
        tbl(
            ["Delivered capability", "Practical effect"],
            [
                [
                    "Explicit prose extraction",
                    "Owner, rationale and dependency spans remain exact-cited candidates. Historical/negated/training-example ownership is excluded; absent rationale stays absent.",
                ],
                [
                    "Cited dependency impact",
                    "Graph relationships and cycle-safe paths link affected systems, duties, knowledge and transfer work to accessible evidence.",
                ],
                [
                    "Change/revoke/delete",
                    "Preserve version history, invalidate dependent claims/assessments, withhold inaccessible evidence and purge source-derived text on deletion.",
                ],
                [
                    "Checkpointed recovery",
                    "Candidate writes and source-version checkpoint commit atomically. Authorised resume skips unchanged checkpoints and avoids duplicates.",
                ],
            ],
            [0.29, 0.71],
        ),
        box(
            "Acceptance delivered",
            "10 distinct changes/revocations: replacement, revoke, deletion, successor ACL loss, transitive interview invalidation, GitHub 401/403/404, definitive tree-file removal and README removal. Five interruption positions (2, 3, 4, 7, 11) resume without duplicate candidates. A separate actual process-restart test also passed.",
        ),
        p(
            "Initial submitted evaluation: 60 separately authored documents, including 34 prose cases, met the 90% precision and 85% field targets on internal labels. Page 12 gives the later first-run evaluation, denominators and preserved failures.",
            "small",
        ),
        p(
            "Limit: explicit English patterns and bounded in-process work. This is not unrestricted semantic understanding or a distributed durable job system.",
            "small",
        ),
        evidence(
            "docs/three-improvements-tests.json",
            "docs/judge-input-hardening.md",
            "docs/extraction-holdout-report.json",
        ),
    ],
)

page(
    "3 · Prove transfer, recover incomplete work.",
    "PRACTICAL TRANSFER VALIDATION & RECOVERY",
    [
        p(
            "Savinay submits a cited explanation or supplied staging observation. A separate authorised supervisor reviews the relevant criteria before closure.",
            "lead",
        ),
        tbl(
            ["Scenario", "What the successor must demonstrate"],
            [
                [
                    "Deployment review",
                    "Identify the current pipeline, prerequisites, approval boundary, post-release checks and escalation when evidence is missing.",
                ],
                [
                    "Rollback readiness",
                    "Locate approved steps, identify schema/data compatibility restrictions and explain when specialist review is required.",
                ],
                [
                    "Recovery evidence",
                    "Locate backup/restore evidence and accountable owner. A runbook alone is not accepted as a staging restore observation.",
                ],
            ],
            [0.28, 0.72],
        ),
        screenshot(
            "07-supervisor-validation.png", crop=(260, 330, 1410, 1000), maxheight=230
        ),
        p(
            "Cropped live case-study supervisor view. Documentation walkthroughs and externally supplied staging observations are distinguished; source versions and assessment history remain inspectable.",
            "small",
        ),
        box(
            "Recovery is part of the workflow",
            "Reject incomplete ownership → request corrections → resubmit → reassess. Reopened active handovers require a new report, reapproval, renewed acceptance and assessment. Missing critical prerequisites or changed/revoked evidence block closure. Closed ownership remains history; later changes use a follow-up transition.",
        ),
        p(
            "12 role flows passed: correct/wrong acceptance, missing citation, wrong submitter, self-assessment denial, rejection, incomplete rubric, correction, critical prerequisite, reopening, staging observation and revocation. External observation authenticity still needs qualified review.",
            "small",
        ),
        evidence(
            "backend/tests/test_transfer_acceptance.py",
            "docs/three-improvements-acceptance.md",
        ),
    ],
)

page(
    "Small architecture, explicit trust boundaries.",
    "TECHNOLOGY, DATA FLOW AND IMPORTANT DECISIONS",
    [
        architecture(),
        tbl(
            ["Layer", "Stack and consequential choice"],
            [
                [
                    "Frontend",
                    "React 19, TypeScript, Vite 7, React Query, Router and React Flow. One responsive workspace; same-origin REST in production.",
                ],
                [
                    "Backend",
                    "Python / FastAPI / Pydantic / httpx. Modular monolith with domain rules separate from UI and provider adapters.",
                ],
                [
                    "Persistence",
                    "SQLAlchemy 2, PostgreSQL/psycopg in production; SQLite local default; immutable Alembic migrations. UUIDs, foreign keys, indexes and uniqueness constraints.",
                ],
                [
                    "Processing",
                    "PyMuPDF, python-docx and bounded GitHub REST. Database-backed job state, atomic source checkpoints and in-process workers.",
                ],
                [
                    "Hosting",
                    "Docker builds UI and API; one Render Free HTTPS origin plus Neon Free PostgreSQL. No separate graph/vector database or paid worker.",
                ],
                [
                    "Optional AI",
                    "Provider adapters validate structured outputs and accessible citations. Rule-based core and retrieval remain usable without a model key.",
                ],
            ],
            [0.22, 0.78],
        ),
        p("Hard engineering boundary", "h2"),
        p(
            "Current permissions and evidence versions are rechecked across extraction, reports, saved conversation, acceptance and practical assessment. A cached or historic source cannot bypass revoked authority. GitHub duplicate enqueue and invitation races use project locks plus refreshed state."
        ),
        evidence(
            "docs/architecture.md",
            "API_CONTRACT.md",
            "backend/pyproject.toml",
            "frontend/package.json",
        ),
    ],
)

page(
    "Every important statement has a lineage.",
    "DATA MODEL, CITATIONS, REVIEW AND EXPLAINABLE METRICS",
    [
        screenshot("05-source-evidence.png", crop=(310, 273, 1130, 729), maxheight=244),
        p(
            "Cropped original-source modal from the live case study. Employee explanation remains identified as testimony and requires independent review.",
            "small",
        ),
        tbl(
            ["Persisted domain", "Records and invariants"],
            [
                [
                    "Identity and scope",
                    "Organisations, users, membership, sessions, invitations, demo visits and access requests. Tenant/project/source checks precede content access.",
                ],
                [
                    "Knowledge evidence",
                    "Connections, sources, versioned chunks, claims and evidence. Citation retains source ID/name/type/time/version, chunk, locator and exact quote.",
                ],
                [
                    "Investigation and change",
                    "Investigations, gaps, simulations and jobs. Current authority, source-version checkpoints and derived-evidence lineage.",
                ],
                [
                    "Transfer and audit",
                    "Transitions, transfers, exercises and audit events. Versioned report approval, actor-specific acceptance, separate assessment and historical ownership.",
                ],
                [
                    "Optional conversation",
                    "Encrypted organisation configuration, owner-only conversations, turns and expiring action previews. No private key returned.",
                ],
            ],
            [0.28, 0.72],
        ),
        p("What the dashboard numbers mean", "h2"),
        p(
            "<b>Acceptance</b> = accepted duties / required duties. <b>Validation</b> = supervisor-reviewed passing tasks / required tasks. <b>Evidence coverage</b> = current readable handover records / required records. Gaps, stale sources and unresolved issues are counts with source-backed definitions. Missing denominators yield unavailable values; these are not AI-generated competence scores."
        ),
        evidence("backend/app/models.py", "API_CONTRACT.md", "docs/architecture.md"),
    ],
)

page(
    "Reliability was exercised at the boundaries.",
    "AUTOMATED, DATABASE, CONNECTOR AND END-TO-END EVIDENCE",
    [
        metrics(),
        tbl(
            ["Recorded check", "Result", "What it establishes"],
            [
                [
                    "Latest backend suite",
                    "239 passed;<br/>0 failed/skipped",
                    "17 real PostgreSQL cases in owned loopback QA schemas. Latest run did not collect coverage; previous measured baseline 89%.",
                ],
                [
                    "Exact-three acceptance",
                    "34/34 passed",
                    "7 onboarding + 10 distinct source changes + 5 interruption positions + 12 role flows. Isolated fixtures/mocked failures.",
                ],
                [
                    "Final uncertainty guard",
                    "22 targeted passes",
                    "Boundary rerun after the final claim/assignment uncertainty change. No new full-suite coverage claim.",
                ],
                [
                    "Focused browser checks",
                    "9/9 passed",
                    "Readiness errors, cooldown, access refresh, source warnings, layout and active job completion/failure.",
                ],
                [
                    "Complete local UI journey",
                    "Passed ~203 sec",
                    "Fresh sources → review → report → ownership acceptance → separate assessment → closure. Author-operated automated QA.",
                ],
                [
                    "Real live GitHub sync",
                    "40 initial imports;<br/>0 new on resync",
                    "Own public repository, authenticated bounded sync; temporary token revoked. Not arbitrary private-repository proof.",
                ],
                [
                    "Clean installation",
                    "Passed",
                    "Fresh Git archive, frozen Python install, npm ci/build, migration, API start, 13-source fresh judge entry and deep link.",
                ],
                [
                    "CI and dependency checks",
                    "Passed",
                    "Backend lint/format/tests, frontend lint/typecheck/build, Python/Node audits and scoped secret scan.",
                ],
            ],
            [0.26, 0.20, 0.54],
        ),
        p("Failures found and corrected", "h2"),
        p(
            "Reproduced stale invitation revocation and duplicate-sync races; fixed lock/reload sequencing. Fixed mobile source-table overflow. Request-limit errors show cooldown and preserve saved work. Missing/failed readiness disables closure. Source changes and access loss require recovery rather than silently retaining success."
        ),
        p(
            link("Latest successful CI run", CI)
            + " · "
            + link("Live application commit", REPO + "/commit/" + APP_SHA),
            "small",
        ),
        evidence(
            "docs/judge-upgrade-verification.json",
            "docs/judge-upgrade-target-verification.json",
            "docs/github-live-sync-verification.json",
        ),
    ],
)

report = json.loads((ROOT / "docs/postfix-internal-first-report.json").read_text())
page(
    "Evaluation reports the misses as well.",
    "EXTRACTION QUALITY · INTERNAL FIRST RUN AND REGRESSION LIMITS",
    [
        p(
            "The latest separate first-run corpus has 60 new prose documents, different identities and systems, frozen after general fixes and before execution. It was not tuned after this run. Labels are authored internally with implementation knowledge.",
            "lead",
        ),
        field_chart(report),
        tbl(
            ["Metric", "Latest separate first run", "Submitted target"],
            [
                ["Candidate precision", "50/50 = 100%", "At least 90%"],
                [
                    "Candidate recall",
                    "50/52 = 96.2%",
                    "Reported; no promised threshold",
                ],
                ["Owner accuracy", "19/20 = 95%", "At least 85%"],
                ["Rationale accuracy", "11/12 = 91.7%", "At least 85%"],
                ["Dependency fields", "20/20 = 100%", "At least 85%"],
                [
                    "Exact quotations",
                    "50/50 = 100%",
                    "Attribution integrity; not semantic truth",
                ],
            ],
            [0.36, 0.36, 0.28],
        ),
        box(
            "Two conservative misses remain",
            "An unnamed engineer duty with a separate denial was not emitted. A definite decision with a rationale containing “may” was also missed. Missing knowledge remains unresolved; the product does not invent an owner or rationale.",
        ),
        p("Original failures remain published", "h2"),
        p(
            "A prior frozen 72-prose challenge first measured precision 95.2%, recall 71.4%, owner 65%, rationale 50% and dependencies 20%. General fixes now pass that known set at 100%; those results are <b>tuned regression</b>, not fresh accuracy. The initial submitted 60-document / 34-prose internal holdout is retained separately."
        ),
        p(
            "Scoring uses exact candidate/field identities and normalises the leading article “the” in dependency endpoints. These bounded sets do not establish independent enterprise or multilingual accuracy. Independent labels, representative documents and reviewer agreement are roadmap gates.",
            "small",
        ),
        evidence(
            "docs/postfix-internal-first-report.json",
            "docs/judge-input-first-report.json",
            "docs/judge-input-regression-report.json",
        ),
    ],
)

page(
    "The next person can find the next action.",
    "USABILITY, ACCESSIBILITY AND REAL-WORLD FIT",
    [
        screenshot(
            "08-successor-continuation.png", crop=(258, 336, 1415, 1000), maxheight=250
        ),
        p(
            "Cropped live Savinay continuation view: current duties, reviewed procedures and source inspection in the same workspace.",
            "small",
        ),
        tbl(
            ["Design decision", "How it helps a new user"],
            [
                [
                    "Visible next actor/action",
                    "The current project state computes where the coordinator or successor should go next; empty and missing states explain what is needed.",
                ],
                [
                    "Closure before action",
                    "Readiness shows acceptance, independent review, current evidence and blocker links before Close. Backend gates are authoritative.",
                ],
                [
                    "Recoverable failures",
                    "Safe retry/cooldown, preserved saved data and manual readiness/access refresh make failure and teammate updates understandable.",
                ],
                [
                    "Readable evidence",
                    "Sources, versions and locators remain inspectable. Uncertainty is explicit; role-specific reports omit restricted material.",
                ],
                [
                    "Responsive interface",
                    "390 / 768 / 1440 pixel checks; day/night themes, keyboard controls and reduced-motion support. Bounded axe checks passed.",
                ],
            ],
            [0.29, 0.71],
        ),
        box(
            "What user validation has actually occurred",
            "Automated browser journeys and author-operated live checks are recorded. No unfamiliar-user observations were supplied, so this report makes no five-person usability-study claim. The repository includes a consent-based task pack to record completion, time, help, confusion and retest outcomes.",
        ),
        p(
            "Remaining accessibility work: complete screen-reader and assistive-technology testing with users; bounded automated checks are not a full WCAG certification.",
            "small",
        ),
        evidence(
            "docs/usability-task-pack.md",
            "docs/judge-experience-verification.json",
            "docs/screenshots/capture-record.json",
        ),
    ],
)

page(
    "Permission-aware by design.",
    "PRIVACY, SECURITY AND RESPONSIBLE USE",
    [
        tbl(
            ["Trust boundary", "Implemented protection", "Practical limit"],
            [
                [
                    "Identity",
                    "Argon2 passwords; opaque hashed sessions; Secure/HttpOnly/SameSite cookies.",
                    "No verified email, reset email, SSO or MFA.",
                ],
                [
                    "Server writes",
                    "Pydantic validation, cookie/CSRF/Origin checks; parameterised ORM queries.",
                    "No independent penetration-test certification.",
                ],
                [
                    "Content disclosure",
                    "Tenant/project/source ACL plus evidence-version checks on derived views/history.",
                    "Upstream source ACL mirroring is absent; resync/revoke required.",
                ],
                [
                    "Sensitive sources",
                    "Pattern-based secret quarantine and selected contact-PII redaction before indexing.",
                    "False positives/negatives possible; no comprehensive DLP.",
                ],
                [
                    "Credentials",
                    "Fernet-encrypted provider/PAT keys; environment secrets; tokens excluded from UI/audit.",
                    "Operator must protect encryption key and assess provider agreements.",
                ],
                [
                    "Review and action",
                    "Candidates pending; correction/rejection/approval; separate successor/supervisor acts.",
                    "Human approval does not establish external operational truth.",
                ],
                [
                    "Lifecycle",
                    "Version history, derived invalidation, source deletion/purge and filtered audit.",
                    "Automated retention/legal hold/data-residency policies not implemented.",
                ],
                [
                    "Demonstration",
                    "Separate expiring visitor tenant; private credentials and conversations excluded.",
                    "Do not upload confidential production data into a public demo.",
                ],
            ],
            [0.20, 0.43, 0.37],
        ),
        p("Safe operation is explicit", "h2"),
        p(
            "INHERIA handles knowledge and responsibility transfer. It records authorised staging observations and supervisor review; it does not run production deployment, rollback or restore commands. Hypothetical risk analysis identifies assumptions. Unsupported generated content is never treated as verified organisational truth."
        ),
        p("External services and licence considerations", "h2"),
        p(
            "GitHub, Render and Neon follow their own access/usage terms. React, FastAPI and the listed ecosystem tools use their respective open-source licences; Inter and bundled Bitstream Vera have redistributable font licences. <b>PyMuPDF uses AGPL/commercial licensing</b>: review the intended distribution/deployment obligations. Model processing needs organisation opt-in and provider-retention review."
        ),
        evidence(
            "docs/architecture.md", "docs/deployment.md", "backend/pyproject.toml"
        ),
    ],
)

page(
    "Clone, install, run and verify.",
    "REPRODUCIBLE SETUP · ENVIRONMENT · API · OPTIONAL AI",
    [
        p(
            "Verified fresh installation: Python 3.13, uv, Node 24 and npm. Metadata supports Python 3.12+. Locked dependencies define the actual installed versions.",
            "body",
        ),
        box(
            "PowerShell · repository and API",
            '<font face="Courier" size="8">git clone https://github.com/Gauravwakle96/INHERIA.git<br/>cd INHERIA/backend<br/>uv sync --frozen<br/>Copy-Item .env.example .env<br/>uv run alembic upgrade head<br/>uv run uvicorn app.main:app --host 127.0.0.1 --port 8010</font>',
        ),
        p(
            "For an existing checkout, preserve the current .env. In a second terminal, from the root:",
            "small",
        ),
        box(
            "PowerShell · frontend",
            '<font face="Courier" size="8">cd frontend<br/>npm ci<br/>npm run dev -- --host 127.0.0.1 --port 5173</font><br/>Open http://127.0.0.1:5173. API docs: http://127.0.0.1:8010/docs.',
        ),
        tbl(
            ["Environment variable", "Purpose"],
            [
                [
                    "INHERIA_DATABASE_URL",
                    "SQLite local default; PostgreSQL/psycopg with TLS in production.",
                ],
                ["INHERIA_ENVIRONMENT", "Production requires PostgreSQL and HTTPS."],
                [
                    "INHERIA_TOKEN_ENCRYPTION_KEY",
                    "Stable server-side Fernet key for private connector and AI credentials.",
                ],
                [
                    "INHERIA_ALLOWED_ORIGINS",
                    "Exact permitted origins. Never wildcard private authenticated writes.",
                ],
                [
                    "INHERIA_DEMO_MODE",
                    "Shared development fixture access; false in production.",
                ],
                [
                    "INHERIA_JUDGE_DEMO_ENABLED",
                    "Separate visitor demo; four-hour expiry and forty-visit default.",
                ],
                [
                    "INHERIA_LLM_ENABLED",
                    "Optional structured extraction opt-in; disabled by default.",
                ],
            ],
            [0.43, 0.57],
        ),
        p("Optional AI: bring your organisation’s own key", "h2"),
        p(
            "Administrator → Digital successor → AI settings. Bynara uses <b>https://router.bynara.id/v1</b>, <b>agnes-2.5-flash</b> and Chat Completions; existing AgentRouter options remain. Enter the key privately in settings, enable and test. No key is supplied to judges. Provider usage can incur charges; core ingestion/review/transfer needs no AI key."
        ),
        p(
            'Verification: backend <font face="Courier">uv run pytest -q</font>; exact-three runner <font face="Courier">uv run python evaluation/run_submission_acceptance.py</font>. PostgreSQL cases require the documented owned loopback QA URL. Frontend: <font face="Courier">npm run lint</font>, <font face="Courier">npm run build</font> and configured Playwright E2E. See README for test-server configuration.',
            "small",
        ),
        evidence(
            "README.md", "backend/.env.example", "API_CONTRACT.md", "docs/deployment.md"
        ),
    ],
)

page(
    "Finished features and honest boundaries.",
    "COMPLETE FEATURE INVENTORY · WHAT REMAINS OUTSIDE THE PRODUCT",
    [
        tbl(
            ["Working feature group", "Delivered functions"],
            [
                [
                    "Accounts and access",
                    "Registration/login, project membership, expiring invites, password choice, access requests, source readers, revocation and audit.",
                ],
                [
                    "Sources",
                    "GitHub REST/PAT, five document formats, provenance/locators, incremental sync, retries/warnings, deduplication, replacement, revoke and delete.",
                ],
                [
                    "Intelligence",
                    "Project-state candidates, explicit English extraction, decisions/rationale/alternatives, dependency graph, ownership gaps, targeted text capture and risk scenarios.",
                ],
                [
                    "Human trust",
                    "Exact evidence inspection, uncertainty, independent correction/approval/rejection, history, source-change impact and resumable investigation.",
                ],
                [
                    "Transfer",
                    "Versioned report, approval, successor/backup assignment, acceptance/rejection, deployment/rollback/recovery criteria, cited observation, supervisor review and recovery gates.",
                ],
                [
                    "Continuity",
                    "Current ownership, completed/fresh demo, continuation plan, contributor/history records, next-step guidance and explainable metrics.",
                ],
                [
                    "Interface and delivery",
                    "Day/night, responsive/keyboard/reduced motion, filtered privacy/audit, migrations, Docker, free deployment, CI and reproducible tests.",
                ],
                [
                    "Additional optional AI",
                    "Private conversations, encrypted organisation key, Low/High budgets, supported model selection, citations, labelled retrieval fallback and confirmed action previews.",
                ],
            ],
            [0.27, 0.73],
        ),
        p("Known limitations that a judge may encounter", "h2"),
        p(
            "Scanned PDFs need external OCR. Prose patterns cover explicit English; shared ownership/pronouns and broad semantics remain incomplete. GitHub imports bounded recent history/selected files, not a full repository archive. No OAuth/webhooks, voice capture, general workflow builder or multi-successor split."
        ),
        p(
            "Render cold starts, Neon storage/transfer quotas, shared-IP limits and the forty-visit cap constrain capacity. Latest pre-check transfer snapshot: about 4.49 GB used of 5 GB; remaining quota is not guaranteed. Jobs run in-process; no distributed workers or scheduled retention. No SSO/MFA/reset email or enterprise governance."
        ),
        box(
            "Optional chatbot reliability",
            "Live Bynara replies are recorded, but a prior 50-question provider run returned only 9 valid replies and 41 labelled fallbacks. That is provider-limited functionality, outside the three submitted improvements. Exact citation structure does not prove semantic correctness.",
            AMBER,
        ),
        evidence(
            "docs/feature-status.md",
            "docs/verification.md",
            "docs/four-workstream-acceptance.md",
        ),
    ],
)

page(
    "A roadmap with gates, not vague promises.",
    "FUTURE DEVELOPMENT · USER BENEFIT · ORDER · MEASURABLE EXIT",
    [
        p(
            "The current source-to-continuation scope ships first. Future stages are ordered by evidence quality, access lifecycle and operational scale; they are not additional completed Round 3 commitments.",
            "lead",
        ),
        tbl(
            [
                "Stage / priority",
                "User change and implementation",
                "Exit criteria before expansion",
            ],
            [
                [
                    "<b>01 · Independent extraction evaluation</b><br/>Highest priority",
                    "Permissioned documents, independently agreed labels and frozen splits. Improve shared ownership, prose, decision conflict and dependency fields.",
                    "Publish sample sizes/category failures and misses; ≥90% candidate precision and ≥85% owner/rationale/dependency accuracy on new held-out labels.",
                ],
                [
                    "<b>02 · Verified identity and access lifecycle</b>",
                    "Verified email, reset/invite delivery, designed SSO/MFA and justified OAuth/webhooks. Add consent-based unfamiliar-user and assistive-technology sessions.",
                    "Positive/negative expiry/replay/revocation/reset tests; no forbidden content after access loss; at least 5 recorded unaided journeys and fixes for blocking confusion.",
                ],
                [
                    "<b>03 · Durable processing and governance</b>",
                    "Queue/shared limiter when workload justifies it; scheduled freshness, retention, monitoring and rehearsed test-database backup/restore.",
                    "Restart/duplicate/cancel preserves one logical result; revoked evidence never regains authority; derived purge and owned restoration pass; publish realistic load/latency scope.",
                ],
                [
                    "<b>04 · Permissioned operational depth</b><br/>After prior gates",
                    "One connector at a time, specialist reviewers, supplied staging-test artefacts and configurable domain schemas driven by real team needs.",
                    "Each connector has real auth/sync/permission-loss/E2E evidence. Staging authenticity reviewed; no production remediation without a separately designed approval system.",
                ],
            ],
            [0.24, 0.39, 0.37],
        ),
        p("Impact we can demonstrate today", "h2"),
        p(
            "A coordinator sees exactly what remains missing. A successor can inspect the source, know the owner, accept or reject transfer and continue with reviewed procedures. Changed evidence cannot silently preserve readiness. The local full UI workflow passed in ~203 seconds; this is a reproducibility observation, not proof of enterprise time savings."
        ),
        box(
            "Maintaining credibility",
            "Keep setup, API, migrations, feature status and verification current at every release. Preserve first-run failures and actual timestamps. Do not describe a roadmap item, screenshot, local toy recovery or checked box as proof of production competence.",
        ),
        evidence(
            "docs/roadmap.md", "docs/verification.md", "docs/final-product-readiness.md"
        ),
    ],
)

page(
    "Participants, provenance and submission record.",
    "TEAM JAEGERS · CONTRIBUTION ATTRIBUTION · BASELINE AND FINALISATION",
    [
        p(
            "Team and institution are transcribed from the existing Round 1 proposal: JAEGERS, MIT, Chhatrapati Sambhajinagar. These are participant names, separate from the ShopEase case-study roles.",
            "body",
        ),
        tbl(
            [
                "Participant",
                "Assigned workstream in Round 1",
                "Actual contribution evidence",
            ],
            [
                [
                    "Gaurav Wakle<br/>Team leader",
                    "Product scope/architecture, backend/AI integration and overall delivery.",
                    "Leader confirmation required for final individual contribution attribution.",
                ],
                [
                    "Pranad Bhale",
                    "Backend/data integration: GitHub, ingestion, provenance and connector tests.",
                    "Assigned role is documented; personal delivery is not independently inferred.",
                ],
                [
                    "Savinay Pathak",
                    "Frontend/UX: workspace, evidence, review, handover and workflow usability.",
                    "Assigned role is documented; final actual contribution needs team sign-off.",
                ],
                [
                    "Rudransh Jaiswal",
                    "Security/QA/documentation: permission flows, edge cases, setup and demo reliability.",
                    "Assigned role is documented; final actual contribution needs team sign-off.",
                ],
            ],
            [0.24, 0.39, 0.37],
        ),
        p("Document control and verification scope", "h2"),
        p(
            "Application and test references identify the exact evidence supporting this report. Proposed roadmap milestones remain separate from completed capabilities. Assigned workstreams are documented; actual individual delivery requires team confirmation."
        ),
        tbl(
            ["Snapshot", "Public record"],
            [
                [
                    "Verified application",
                    link(
                        "55b11e1 · input, sync and source-health hardening",
                        REPO + "/commit/" + APP_SHA,
                    ),
                ],
                [
                    "Evidence snapshot",
                    link(
                        "9ed1d05 · deployment and clean-install record",
                        REPO + "/commit/" + EVIDENCE_SHA,
                    ),
                ],
                ["Latest CI at report build", link("Run 43612957597 · success", CI)],
                [
                    "Source repository",
                    link("Public source and documentation", REPO),
                ],
            ],
            [0.29, 0.71],
        ),
        box(
            "Items the team leader must finalise",
            "Confirm individual contributions and organiser-required registration details. Publish the final PDF with judge access, test submitted links in a private window and submit once for the whole team. This report does not claim the form has been submitted or personal confirmation boxes ticked.",
        ),
        p(
            "Participant delivery and user observations require actual supplied records. ShopEase case-study identities do not establish personal team contributions. The three submitted improvements are mapped on pages 5–8.",
            "small",
        ),
    ],
)

page(
    "Evidence index and documentation map.",
    "CLICKABLE REFERENCES · REPRODUCTION · FINAL PACKAGE CHECK",
    [
        tbl(
            ["Judge question", "Primary public evidence"],
            [
                [
                    "Can I use the product?",
                    link("Live product", LIVE)
                    + " · "
                    + link("Judge guide", LIVE + "/demo")
                    + " · "
                    + link("README", BASE + "README.md"),
                ],
                [
                    "What exactly was delivered?",
                    link(
                        "Three-improvement promise map",
                        BASE + "docs/three-improvements-acceptance.md",
                    )
                    + " · "
                    + link(
                        "34-journey record", BASE + "docs/three-improvements-tests.json"
                    ),
                ],
                [
                    "How does it work?",
                    link("Architecture/trust boundaries", BASE + "docs/architecture.md")
                    + " · "
                    + link("API contract", BASE + "API_CONTRACT.md")
                    + " · "
                    + link("Models", BASE + "backend/app/models.py"),
                ],
                [
                    "Which tests were run?",
                    link("Verification timeline", BASE + "docs/verification.md")
                    + " · "
                    + link(
                        "Latest 239-test/9-browser record",
                        BASE + "docs/judge-upgrade-verification.json",
                    ),
                ],
                [
                    "Does clean install work?",
                    link(
                        "Live + clean-install evidence",
                        BASE + "docs/judge-upgrade-target-verification.json",
                    )
                    + " · "
                    + link("Deployment/setup limits", BASE + "docs/deployment.md"),
                ],
                [
                    "Was GitHub actually exercised?",
                    link(
                        "40 imports / unchanged resync / revoked token",
                        BASE + "docs/github-live-sync-verification.json",
                    ),
                ],
                [
                    "Is extraction quality measured?",
                    link(
                        "Separate 60-prose first run",
                        BASE + "docs/postfix-internal-first-report.json",
                    )
                    + " · "
                    + link(
                        "Original 72-case misses",
                        BASE + "docs/judge-input-first-report.json",
                    )
                    + " · "
                    + link(
                        "Known regression",
                        BASE + "docs/judge-input-regression-report.json",
                    ),
                ],
                [
                    "What remains incomplete?",
                    link("Feature status", BASE + "docs/feature-status.md")
                    + " · "
                    + link("Detailed roadmap", GUIDES_BASE + "docs/roadmap.md")
                    + " · "
                    + link("Usability task pack", BASE + "docs/usability-task-pack.md"),
                ],
                [
                    "Can I reproduce the evidence?",
                    link("Backend locked dependencies", BASE + "backend/uv.lock")
                    + " · "
                    + link("Frontend lockfile", BASE + "frontend/package-lock.json")
                    + " · "
                    + link("CI pipeline", BASE + ".github/workflows/ci.yml"),
                ],
            ],
            [0.35, 0.65],
        ),
        p("Where the Round 3 criteria are addressed", "h2"),
        tbl(
            ["Criterion", "Report section"],
            [
                [
                    "Completeness · 25",
                    "Pages 2–4: judge access, users and working central journey; page 16: feature inventory.",
                ],
                [
                    "Three improvements · 20",
                    "Pages 5–8: exact commitment, implemented behaviour, demonstration and acceptance evidence.",
                ],
                [
                    "Reliability · 20",
                    "Pages 11–12: database/connector/UI tests, evaluation denominators, failures and limits.",
                ],
                [
                    "Usability and fit · 20",
                    "Pages 2–3 and 13–14: next steps, permissions, evidence inspection, accessibility and responsible use.",
                ],
                [
                    "Documentation / roadmap · 15",
                    "Pages 9–10, 15, 17–23: architecture/data, setup, detailed milestones, operations, team attribution and references.",
                ],
            ],
            [0.34, 0.66],
        ),
        p("Submission package", "h2"),
        p(
            "Working product link, public source repository, this report, completed features (page 16), architecture (page 9), exact improvements (pages 5–8), testing (pages 11–12), detailed roadmap (pages 17–20) and operations (page 21). Participant attribution and final sharing confirmation remain team-owned. No video or social-media post is required."
        ),
        p(
            "Figures are original vector diagrams or dated screenshots. Crops improve readability without altering records. Links use the frozen evidence commit. This report does not award or promise a score.",
            "small",
        ),
        p(
            "Report build uses ReportLab, Pillow and PyMuPDF in an isolated tool environment. Editable source and rebuild instructions are in docs/report. Font: bundled Bitstream Vera. Evidence snapshot: 14 November 2026.",
            "small",
        ),
    ],
)


enhance(PAGES, p, tbl, box, evidence)


def render():
    c = canvas.Canvas(str(PDF), pagesize=A4, pageCompression=1)
    c.setTitle("INHERIA | Round 3 Final Product Report | Team JAEGERS")
    c.setAuthor("Team JAEGERS")
    c.setSubject(
        "Delivered source-to-continuation product, three improvements, testing, privacy, setup and roadmap"
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
        c.drawRightString(W - M, H - 38, "TEAM JAEGERS / ROUND 3")
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
        c.drawString(M, 23, "People leave. Knowledge lives on. | Evidence: 14 Nov 2026")
        c.drawRightString(W - M, 23, f"{n:02d} / {len(PAGES):02d}")
        layout.append(
            {"page": n, "title": title, "bottom": round(y, 2), "items": bounds}
        )
        c.showPage()
    c.save()
    (OUT / "layout-check.json").write_text(
        json.dumps(layout, indent=2), encoding="utf-8"
    )
    manifest = {
        "pages": len(PAGES),
        "filename": PDF.name,
        "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "application_commit": APP_SHA,
        "evidence_commit": EVIDENCE_SHA,
        "sources": "Public repository documentation/evaluation and existing authorised screenshot records.",
        "participant_status": "Round 1 roster and assigned roles; actual contributions await team confirmation.",
        "unfamiliar_user_study": "Not claimed; observations not supplied.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    target = Path("C:/documents")
    if target.exists():
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
