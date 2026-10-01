from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.models.schemas import Sitrep

# Helvetica (the PDF default) has no Hindi/Marathi glyphs, so Devanagari text came out as
# black boxes. Paragraphs containing Devanagari are drawn with Noto Sans (Latin) plus
# Noto Sans Devanagari for the Hindi runs — both SIL Open Font License, bundled in
# app/assets/fonts. ReportLab only shapes text (joins conjuncts like क्ष, places vowel
# signs) when the paragraph's base font is a TrueType font and `uharfbuzz` is installed,
# which is why those paragraphs switch base font instead of staying on Helvetica.
_FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
_LATIN_FONT = "NotoSans"
_DEVANAGARI_FONT = "NotoSansDevanagari"
_DEVANAGARI_CHARS = "\u0900-\u097F\uA8E0-\uA8FF\u200C\u200D"
_HAS_DEVANAGARI = re.compile(f"[{_DEVANAGARI_CHARS}]")
# A Devanagari run, plus any punctuation right after it: drawing that punctuation in the same
# shaped run keeps it from overlapping the last Hindi letter (e.g. "दिखाओ," ).
_DEVANAGARI_RUN = re.compile(
    f"[{_DEVANAGARI_CHARS}]+(?:[\\s\u0964\u0965]+[{_DEVANAGARI_CHARS}]+)*[,.;:!?\u0964\u0965]*"
)
_fonts_ready: bool | None = None
_latin_coverage: set[int] = set()


def _register_fonts() -> bool:
    global _fonts_ready
    if _fonts_ready is None:
        try:
            pdfmetrics.registerFont(TTFont(_LATIN_FONT, str(_FONT_DIR / "NotoSans-Regular.ttf")))
            pdfmetrics.registerFont(TTFont(_DEVANAGARI_FONT, str(_FONT_DIR / "NotoSansDevanagari-Regular.ttf")))
            _latin_coverage.update(pdfmetrics.getFont(_LATIN_FONT).face.charToGlyph)
            _fonts_ready = True
        except Exception:
            _fonts_ready = False  # font files missing — PDF still builds, Hindi shows as boxes
    return _fonts_ready


def _para(text: str, style: ParagraphStyle, line_breaks: bool = False) -> Paragraph:
    """Paragraph with escaped text (a stray "&" or "<" in a query or headline used to break
    the PDF), switching to the Devanagari-capable, shaped fonts only when needed."""
    safe = escape(text)
    if line_breaks:
        safe = safe.replace("\n", "<br/>")
    if _HAS_DEVANAGARI.search(text) and _register_fonts():
        # Characters Noto Sans lacks (e.g. "→") go back to Helvetica, which has them.
        safe = "".join(
            ch if ord(ch) in _latin_coverage or _HAS_DEVANAGARI.match(ch) or ch in "\n"
            else f'<font name="Helvetica">{ch}</font>'
            for ch in safe
        )
        safe = _DEVANAGARI_RUN.sub(lambda m: f'<font name="{_DEVANAGARI_FONT}">{m.group(0)}</font>', safe)
        style = ParagraphStyle(f"{style.name}-deva", parent=style, fontName=_LATIN_FONT, shaping=1)
    return Paragraph(safe, style)


SEVERITY_COLOR = {"low": colors.HexColor("#2e7d32"), "medium": colors.HexColor("#e6a817"), "high": colors.HexColor("#c62828")}


def export_pdf(sitrep: Sitrep) -> str:
    filename = f"sitrep_{sitrep.generated_at.strftime('%Y%m%dT%H%M%S')}.pdf"
    path = settings.pdf_export_dir / filename

    styles = getSampleStyleSheet()
    story = [
        Paragraph("DEF-SPACE SITUATIONAL REPORT (SITREP)", styles["Title"]),
        Spacer(1, 6),
        _para(f"Query: {sitrep.query}", styles["Normal"]),
        _para(f"AOI: {sitrep.aoi.name if sitrep.aoi else 'n/a'}", styles["Normal"]),
        Paragraph(f"Generated: {sitrep.generated_at.isoformat()}Z", styles["Normal"]),
        Spacer(1, 10),
    ]

    sev_style = ParagraphStyle("severity", parent=styles["Heading2"], textColor=SEVERITY_COLOR.get(sitrep.severity.value, colors.black))
    story.append(Paragraph(f"SEVERITY: {sitrep.severity.value.upper()}{'  — ALERT TRIGGERED' if sitrep.alert else ''}", sev_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(_para(sitrep.summary, styles["Normal"], line_breaks=True))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Claims &amp; Provenance", styles["Heading2"]))
    rows = [["Claim", "Source"]]
    for c in sitrep.claims:
        detail = f" ({c.source_detail})" if c.source_detail else ""
        rows.append([_para(c.text, styles["Normal"]), _para(f"{c.source_agent.value}{detail}", styles["Normal"])])
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
