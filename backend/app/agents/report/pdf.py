from __future__ import annotations

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.models.schemas import Sitrep

SEVERITY_COLOR = {"low": colors.HexColor("#2e7d32"), "medium": colors.HexColor("#e6a817"), "high": colors.HexColor("#c62828")}


def export_pdf(sitrep: Sitrep) -> str:
    filename = f"sitrep_{sitrep.generated_at.strftime('%Y%m%dT%H%M%S')}.pdf"
    path = settings.pdf_export_dir / filename

    styles = getSampleStyleSheet()
    story = [
        Paragraph("DEF-SPACE SITUATIONAL REPORT (SITREP)", styles["Title"]),
        Spacer(1, 6),
        Paragraph(f"Query: {sitrep.query}", styles["Normal"]),
        Paragraph(f"AOI: {sitrep.aoi.name if sitrep.aoi else 'n/a'}", styles["Normal"]),
        Paragraph(f"Generated: {sitrep.generated_at.isoformat()}Z", styles["Normal"]),
        Spacer(1, 10),
    ]

    sev_style = ParagraphStyle("severity", parent=styles["Heading2"], textColor=SEVERITY_COLOR.get(sitrep.severity.value, colors.black))
    story.append(Paragraph(f"SEVERITY: {sitrep.severity.value.upper()}{'  — ALERT TRIGGERED' if sitrep.alert else ''}", sev_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(sitrep.summary.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Claims &amp; Provenance", styles["Heading2"]))
    rows = [["Claim", "Source"]]
    for c in sitrep.claims:
        detail = f" ({c.source_detail})" if c.source_detail else ""
        rows.append([Paragraph(c.text, styles["Normal"]), Paragraph(f"{c.source_agent.value}{detail}", styles["Normal"])])
    table = Table(rows, colWidths=[4.3 * inch, 2.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c2530")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Agent Status", styles["Heading2"]))
    status_text = ", ".join(f"{k}: {v.value}" for k, v in sitrep.agent_statuses.items())
    story.append(Paragraph(status_text, styles["Normal"]))

    doc = SimpleDocTemplate(str(path), pagesize=LETTER)
    doc.build(story)
    return filename
