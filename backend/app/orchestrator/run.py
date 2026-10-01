"""Runs the selected agents in parallel and hands their envelopes to the Report agent.

A failed or skipped agent never blocks the others — asyncio.gather with
return_exceptions=True plus a per-agent try/except means one dead upstream (e.g. a
rate-limited News API) still lets the SITREP assemble from whatever did come back.
"""
from __future__ import annotations

import asyncio

from app.agents.gis.service import fetch_gis
from app.agents.news.service import fetch_news
from app.agents.predict.service import predict_go_no_go
from app.agents.rag.service import fetch_rag
from app.agents.report.service import fuse_sitrep
from app.agents.translation.service import translate_text
from app.agents.vision.service import fetch_vision
from app.agents.weather.service import fetch_weather
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, AOI, GeoFeature, OrchestrateResponse, Severity
from app.orchestrator.intent import select_agents


def _skipped(agent: AgentName) -> AgentEnvelope:
    return AgentEnvelope(agent=agent, status=AgentStatus.skipped)


async def _safe(coro, agent: AgentName) -> AgentEnvelope:
    try:
        return await coro
    except Exception as exc:  # belt-and-braces: agent services already catch their own errors
        return AgentEnvelope(agent=agent, status=AgentStatus.error, error=str(exc))


async def orchestrate(query: str, aoi: AOI) -> OrchestrateResponse:
    selected = select_agents(query)

    search_query = query
    translation_env = _skipped(AgentName.translation)
    if AgentName.translation in selected:
        translation_env = await _safe(translate_text(query), AgentName.translation)
        if translation_env.status == AgentStatus.ok and translation_env.data:
            search_query = translation_env.data["translated_text"]

    tasks = {}
    if AgentName.weather in selected:
        tasks[AgentName.weather] = _safe(fetch_weather(aoi.name, aoi.lat, aoi.lon), AgentName.weather)
    if AgentName.news in selected:
        # News APIs expect a short keyword/region term, not the full natural-language
        # question (GNews 400s on long, comma-heavy queries) — search by AOI name.
        tasks[AgentName.news] = _safe(fetch_news(aoi.name), AgentName.news)
    if AgentName.vision in selected:
        tasks[AgentName.vision] = _safe(fetch_vision(aoi.name, aoi.lat, aoi.lon, None, None), AgentName.vision)
    if AgentName.rag in selected:
        tasks[AgentName.rag] = _safe(fetch_rag(search_query), AgentName.rag)
    if AgentName.predict in selected:
        tasks[AgentName.predict] = _safe(predict_go_no_go(aoi.name, aoi.lat, aoi.lon), AgentName.predict)

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values())))

    envelopes: dict[str, AgentEnvelope] = {}
    for agent in (AgentName.weather, AgentName.news, AgentName.vision, AgentName.rag, AgentName.predict):
        envelopes[agent.value] = results.get(agent, _skipped(agent))
    envelopes[AgentName.translation.value] = translation_env

    # GIS runs last: it plots AOI-level severity pins built from what vision/news actually found.
    # Free-tier news APIs don't return per-article coordinates, so we don't fabricate pins for
    # individual articles — only real, derivable coordinates (the AOI center itself) are plotted.
    gis_features: list[GeoFeature] = []
    vision_env = envelopes[AgentName.vision.value]
    if vision_env.status == AgentStatus.ok and vision_env.data and vision_env.data.get("change_detected"):
        gis_features.append(
            GeoFeature(
                id="vision-change",
                lat=aoi.lat,
                lon=aoi.lon,
                label=f"Satellite change {vision_env.data['change_percentage']}%",
                layer="satellite_change",
                source_agent=AgentName.vision,
                severity=Severity.medium,
            )
        )
    news_env = envelopes[AgentName.news.value]
    if news_env.status == AgentStatus.ok and news_env.data and news_env.data.get("escalation_flag"):
        gis_features.append(
            GeoFeature(
                id="news-escalation",
                lat=aoi.lat,
                lon=aoi.lon,
                label=f"News escalation score {news_env.data['overall_escalation']}",
                layer="news",
                source_agent=AgentName.news,
                severity=Severity.high,
            )
        )

    if AgentName.gis in selected:
        envelopes[AgentName.gis.value] = await _safe(fetch_gis(aoi, gis_features), AgentName.gis)
    else:
        envelopes[AgentName.gis.value] = _skipped(AgentName.gis)

    sitrep = fuse_sitrep(query, aoi, envelopes)
    return OrchestrateResponse(sitrep=sitrep, raw=envelopes)
