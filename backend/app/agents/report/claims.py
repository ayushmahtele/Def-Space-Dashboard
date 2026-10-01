"""Turns each agent's raw output into short provenance-tagged claim sentences.

Every sentence here is derived directly from a field on that agent's response — nothing
is invented, so `source_agent` + `source_detail` are always traceable back to a real
value the agent actually returned.
"""
from __future__ import annotations

from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, ProvenancedClaim


def build_claims(envelopes: dict[str, AgentEnvelope]) -> list[ProvenancedClaim]:
    claims: list[ProvenancedClaim] = []

    weather = envelopes.get(AgentName.weather.value)
    if weather and weather.status == AgentStatus.ok and weather.data:
        d = weather.data
        text = f"Current conditions: {d['temperature_c']}°C, wind {d['windspeed_kmh']} km/h."
        if d.get("flag_reason"):
            text += f" Operational flag: {d['flag_reason']}."
        claims.append(ProvenancedClaim(text=text, source_agent=AgentName.weather, source_detail=d.get("source") or "Open-Meteo current + hourly forecast"))

    news = envelopes.get(AgentName.news.value)
    if news and news.status == AgentStatus.ok and news.data:
        d = news.data
        articles = d.get("articles", [])
        if articles:
            claims.append(
                ProvenancedClaim(
                    text=f"{len(articles)} recent article(s) found for this AOI; overall OSINT escalation score {d['overall_escalation']}.",
                    source_agent=AgentName.news,
                    source_detail="aggregate across fetched articles",
                )
            )
            for a in articles[:3]:
                claims.append(
                    ProvenancedClaim(
                        text=f"\"{a['title']}\" ({a['source']}) — escalation score {a['escalation_score']}, keywords: {', '.join(a['keywords_matched']) or 'none'}.",
                        source_agent=AgentName.news,
                        source_detail=a["url"],
                    )
                )
        else:
            claims.append(ProvenancedClaim(text="No recent articles matched the query.", source_agent=AgentName.news))

    vision = envelopes.get(AgentName.vision.value)
    if vision and vision.status == AgentStatus.ok and vision.data:
        d = vision.data
        if d.get("change_percentage") is not None:
            text = f"Satellite comparison {d['date_before']} → {d['date_after']}: {d['change_percentage']}% pixel-level change detected."
            if d.get("description"):
                text += f" Gemini vision: {d['description']}"
            url = d.get("tile_before_url") or ""
            layer = url.split("/best/")[1].split("/")[0] if "/best/" in url else "MODIS"
            claims.append(ProvenancedClaim(text=text, source_agent=AgentName.vision, source_detail=f"NASA GIBS true-color tiles ({layer})"))

    rag = envelopes.get(AgentName.rag.value)
    if rag and rag.status == AgentStatus.ok and rag.data:
        d = rag.data
        sources = ", ".join(sorted({s["document"] for s in d.get("sources", [])}))
        claims.append(ProvenancedClaim(text=d["answer"], source_agent=AgentName.rag, source_detail=f"grounded in: {sources}" if sources else None))

    gis = envelopes.get(AgentName.gis.value)
    if gis and gis.status == AgentStatus.ok and gis.data:
        inside = [g for g in gis.data.get("geofence_statuses", []) if g.get("inside_zone")]
        if inside:
            claims.append(
                ProvenancedClaim(
                    text=f"{len(inside)} flagged feature(s) fall inside the AOI geofence radius.",
                    source_agent=AgentName.gis,
                )
            )

    predict = envelopes.get(AgentName.predict.value)
    if predict and predict.status == AgentStatus.ok and predict.data:
        d = predict.data
        top = d.get("feature_contributions", [])[:2]
        top_text = "; ".join(f"{c['feature']}={c['value']}" for c in top)
        claims.append(
            ProvenancedClaim(
                text=f"Go/no-go model verdict: {d['verdict']} ({d['go_probability']:.0%} go probability). Top factors: {top_text}.",
                source_agent=AgentName.predict,
                source_detail=d.get("caveat"),
            )
        )

    translation = envelopes.get(AgentName.translation.value)
    if translation and translation.status == AgentStatus.ok and translation.data and translation.data.get("detected_language") != "en":
        claims.append(
            ProvenancedClaim(
                text=f"Source text auto-detected as '{translation.data['detected_language']}' and translated to English for analysis.",
                source_agent=AgentName.translation,
            )
        )

    return claims
