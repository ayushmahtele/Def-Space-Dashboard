"""Keyword-based intent routing — decides which agents are worth calling for a query
instead of always firing all six. Simple and explainable beats an LLM-based router here:
a teammate can read this file and know exactly why an agent did or didn't run.
"""
from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

# langdetect is randomised by default: on mixed Hindi/English text it sometimes answers "hi"
# and sometimes "en" for the same input, so routing and translation could disagree. A fixed
# seed makes detection deterministic — the same query always gets the same answer.
DetectorFactory.seed = 0

from app.models.schemas import AgentName

# Weather, News and GIS are the baseline situational picture for any AOI query.
BASELINE_AGENTS = {AgentName.weather, AgentName.news, AgentName.gis}

VISION_KEYWORDS = [
    "satellite", "image", "imagery", "change", "construction", "built", "building",
    "base", "runway", "visual", "photo", "infrastructure", "convoy",
]
RAG_KEYWORDS = [
    "report", "policy", "document", "regulation", "treaty", "law", "press release",
    "according to", "cite", "doctrine", "government",
]
PREDICT_KEYWORDS = [
    "launch", "liftoff", "lift-off", "go/no-go", "go-no-go", "go no go",
    "mission window", "rocket", "spacecraft", "weather window",
]


def select_agents(query: str) -> set[AgentName]:
    q = query.lower()
    selected = set(BASELINE_AGENTS)

    if any(kw in q for kw in VISION_KEYWORDS):
        selected.add(AgentName.vision)
    if any(kw in q for kw in RAG_KEYWORDS):
        selected.add(AgentName.rag)
    if any(kw in q for kw in PREDICT_KEYWORDS):
        selected.add(AgentName.predict)

    try:
        if detect(query) != "en":
            selected.add(AgentName.translation)
    except LangDetectException:
        pass

    return selected
