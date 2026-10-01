"""Deterministic severity scoring from the other agents' real outputs.

Numeric, not vibes-based, so the same inputs always produce the same severity and a
grader/teammate can reconstruct why a SITREP was flagged high without re-running an LLM.
"""
from __future__ import annotations

from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, Severity

HIGH_THRESHOLD = 6.0
MEDIUM_THRESHOLD = 2.5


def score_severity(envelopes: dict[str, AgentEnvelope]) -> tuple[Severity, float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    news = envelopes.get(AgentName.news.value)
    if news and news.status == AgentStatus.ok and news.data:
        overall = news.data.get("overall_escalation", 0.0)
        score += overall
        if news.data.get("escalation_flag"):
            reasons.append(f"news escalation score {overall}")

    weather = envelopes.get(AgentName.weather.value)
    if weather and weather.status == AgentStatus.ok and weather.data:
        if weather.data.get("operational_flag"):
            score += 1.5
            reasons.append("weather operational flag raised")

    vision = envelopes.get(AgentName.vision.value)
    if vision and vision.status == AgentStatus.ok and vision.data:
        pct = vision.data.get("change_percentage")
        if pct is not None and vision.data.get("change_detected"):
            weight = min(4.0, pct / 10.0)
            score += weight
            reasons.append(f"satellite change detection {pct}%")

    gis = envelopes.get(AgentName.gis.value)
    if gis and gis.status == AgentStatus.ok and gis.data:
        inside = [g for g in gis.data.get("geofence_statuses", []) if g.get("inside_zone")]
        if inside:
            score += min(3.0, 0.75 * len(inside))
            reasons.append(f"{len(inside)} flagged feature(s) inside AOI geofence")

    predict = envelopes.get(AgentName.predict.value)
    if predict and predict.status == AgentStatus.ok and predict.data:
        if predict.data.get("verdict") == "NO-GO":
            score += 1.5
            reasons.append(f"go/no-go model returned NO-GO ({predict.data.get('go_probability', 0):.0%} go probability)")

    if score >= HIGH_THRESHOLD:
        severity = Severity.high
    elif score >= MEDIUM_THRESHOLD:
        severity = Severity.medium
    else:
        severity = Severity.low

    return severity, round(score, 2), reasons
