"""Report agent — the fusion layer. Takes every other agent's AgentEnvelope for one
query and produces a single provenance-tagged SITREP with a numeric severity score.
"""
from __future__ import annotations

from app.agents.report.claims import build_claims
from app.agents.report.pdf import export_pdf
from app.agents.report.severity import score_severity
from app.core.config import settings
from app.core.gemini_client import generate_text
from app.models.schemas import AgentEnvelope, AOI, Sitrep


def _build_summary(query: str, aoi: AOI | None, claims, severity, score: float, reasons: list[str]) -> str:
    if not claims:
        return "No agents returned usable data for this query — check API key configuration and try again."

    bullet_points = "\n".join(f"- [{c.source_agent.value}] {c.text}" for c in claims)

    if settings.has_gemini:
        prompt = (
            "You are a defense analyst drafting a SITREP. Using ONLY the tagged facts below (each already "
            "attributed to the agent/source that produced it), write a 3-5 sentence situational summary for "
            f"AOI '{aoi.name if aoi else 'unspecified'}' answering the query: '{query}'. "
            "Be factual and concise, do not invent information beyond what's given, and do not repeat the "
            "source tags in your prose.\n\nFacts:\n" + bullet_points
        )
        try:
            summary = generate_text(prompt)
        except Exception:
            summary = None  # Gemini error (quota/overload/network) — use the rule-based summary below
        if summary:
            return summary.strip()

    # Deterministic fallback — still built entirely from real fetched values, just without LLM prose.
    header = f"Situational summary for {aoi.name if aoi else 'AOI'} (severity: {severity.value}, score {score})."
    reason_line = f" Elevated due to: {'; '.join(reasons)}." if reasons else ""
    return header + reason_line + "\n" + bullet_points


def fuse_sitrep(query: str, aoi: AOI | None, envelopes: dict[str, AgentEnvelope], make_pdf: bool = True) -> Sitrep:
    severity, score, reasons = score_severity(envelopes)
    claims = build_claims(envelopes)
    summary = _build_summary(query, aoi, claims, severity, score, reasons)
    agent_statuses = {name: env.status for name, env in envelopes.items()}

    sitrep = Sitrep(
        query=query,
        aoi=aoi,
        severity=severity,
        summary=summary,
        claims=claims,
        alert=severity.value == "high",
        agent_statuses=agent_statuses,
    )

    if make_pdf:
        filename = export_pdf(sitrep)
        sitrep.pdf_url = f"/static/pdf/{filename}"

    return sitrep
