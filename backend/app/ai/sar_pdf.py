"""Render a SarReport as a professional PDF document (reportlab)."""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

GOLD = colors.HexColor("#9A7A16")
INK = colors.HexColor("#1a1a1e")
MUTED = colors.HexColor("#6b6b72")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "SarTitle", parent=base["Title"], fontSize=18, textColor=INK,
            spaceAfter=2,
        ),
        "ref": ParagraphStyle(
            "SarRef", parent=base["Normal"], fontSize=9, textColor=MUTED,
        ),
        "h2": ParagraphStyle(
            "SarH2", parent=base["Heading2"], fontSize=12, textColor=GOLD,
            spaceBefore=14, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "SarBody", parent=base["Normal"], fontSize=10, leading=15,
            textColor=INK, alignment=TA_JUSTIFY,
        ),
        "mono": ParagraphStyle(
            "SarMono", parent=base["Normal"], fontName="Courier", fontSize=9,
            leading=13, textColor=INK,
        ),
        "footer": ParagraphStyle(
            "SarFooter", parent=base["Normal"], fontSize=8, textColor=MUTED,
        ),
    }


def _p(text: str, style) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def build_sar_pdf(sar) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        title=f"SAR {sar.reference}",
    )
    s = _styles()
    story: list = []

    story.append(_p("Suspicious Activity Report", s["title"]))
    story.append(
        _p(
            f"{sar.reference} &nbsp;·&nbsp; Generated "
            f"{sar.generated_at:%Y-%m-%d %H:%M UTC} &nbsp;·&nbsp; "
            f"Finensic Vision (synthetic demo data)",
            s["ref"],
        )
    )
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=GOLD))

    def section(title: str, body):
        story.append(_p(title, s["h2"]))
        if isinstance(body, list):
            story.extend(body)
        else:
            story.append(body)

    section("1. Summary", _p(sar.summary, s["body"]))
    section("2. Customer", _p(sar.customer_section, s["mono"]))
    section("3. Reason for Suspicion", _p(sar.reason, s["body"]))

    # 4. Evidence & Citations — the numbered catalog that the narrative's
    # inline [R#]/[T#] markers reference, so every claim is auditable.
    citations = getattr(sar, "citations", None) or []
    if citations:
        cite_items = []
        for c in citations:
            cid = escape(str(c.get("id", "")))
            label = escape(str(c.get("label", "")))
            detail = escape(str(c.get("detail", "")))
            kind = "Rule" if c.get("kind") == "rule" else "Transaction"
            text = f"<b>[{cid}]</b> &nbsp;{kind}: <b>{label}</b> — {detail}"
            cite_items.append(ListItem(Paragraph(text, s["body"]), leftIndent=6))
        section(
            "4. Evidence &amp; Citations",
            ListFlowable(cite_items, bulletType="bullet", leftIndent=14),
        )
    else:
        evidence_items = []
        for e in sar.evidence:
            tag = e.get("rule") or e.get("transaction") or e.get("finding") or ""
            detail = e.get("detail", "")
            text = (
                f"<b>{escape(str(tag))}</b> — {escape(str(detail))}"
                if tag
                else escape(str(detail))
            )
            evidence_items.append(ListItem(Paragraph(text, s["body"]), leftIndent=6))
        section(
            "4. Evidence",
            ListFlowable(evidence_items, bulletType="1", leftIndent=14)
            if evidence_items
            else _p("None recorded.", s["body"]),
        )

    timeline_items = [
        ListItem(
            _p(f"{ev.get('timestamp', '')} — {ev.get('event', '')}", s["body"]),
            leftIndent=6,
        )
        for ev in sar.timeline
    ]
    section(
        "5. Timeline",
        ListFlowable(timeline_items, bulletType="bullet", leftIndent=14)
        if timeline_items
        else _p("No events.", s["body"]),
    )

    section("6. Recommendation", _p(sar.recommendation, s["body"]))
    if sar.analyst_notes:
        section("7. Analyst Notes", _p(sar.analyst_notes, s["body"]))

    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 4))
    story.append(
        _p(
            "Finensic Vision — demonstration prototype. This report is generated "
            "from entirely synthetic data and is not a real regulatory filing.",
            s["footer"],
        )
    )

    doc.build(story)
    return buf.getvalue()
