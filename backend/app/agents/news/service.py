"""News agent — GNews (primary) or NewsData.io (fallback) free tiers.

Both require a free API key (~100-200 req/day). Without one, this agent reports
AgentStatus.not_configured rather than inventing headlines — the orchestrator then
still assembles a SITREP from whichever other agents did run.
"""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.core.config import settings
from app.core.http_client import new_client
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, NewsArticle, NewsResult

GNEWS_URL = "https://gnews.io/api/v4/search"
NEWSDATA_URL = "https://newsdata.io/api/1/latest"

OSINT_KEYWORDS = {
    "border": 1.0,
    "ceasefire": 1.5,
    "troop movement": 2.0,
    "troops": 1.0,
    "incursion": 2.0,
    "skirmish": 1.5,
    "missile": 2.0,
    "airstrike": 2.0,
    "air strike": 2.0,
    "mobilization": 1.5,
    "sanction": 1.0,
    "drone strike": 2.0,
    "casualties": 1.5,
    "evacuation": 1.0,
    "conflict": 1.0,
    "invasion": 2.5,
    "blockade": 1.5,
    "militant": 1.0,
    "insurgent": 1.0,
    "standoff": 1.0,
}

ESCALATION_FLAG_THRESHOLD = 3.0

_sentiment = SentimentIntensityAnalyzer()


def _score_article(title: str, snippet: str) -> tuple[list[str], float]:
    text = f"{title} {snippet}".lower()
    matched = [kw for kw in OSINT_KEYWORDS if kw in text]
    keyword_score = sum(OSINT_KEYWORDS[kw] for kw in matched)
    negativity = max(0.0, -_sentiment.polarity_scores(text)["compound"])  # 0..1, only the negative side
    return matched, round(keyword_score + negativity * 2, 2)


async def _fetch_gnews(client, query: str) -> list[dict]:
    params = {"q": query, "token": settings.gnews_api_key, "lang": "en", "max": 15, "sortby": "publishedAt"}
    resp = await client.get(GNEWS_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": a["title"],
            "url": a["url"],
            "source": a.get("source", {}).get("name", "unknown"),
            "published_at": a.get("publishedAt"),
            "snippet": a.get("description") or "",
        }
        for a in data.get("articles", [])
    ]


async def _fetch_newsdata(client, query: str) -> list[dict]:
    params = {"apikey": settings.newsdata_api_key, "q": query, "language": "en"}
    resp = await client.get(NEWSDATA_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": a["title"],
            "url": a["link"],
            "source": a.get("source_id", "unknown"),
            "published_at": a.get("pubDate"),
            "snippet": a.get("description") or "",
        }
        for a in data.get("results", [])
    ]


async def fetch_news(query: str) -> AgentEnvelope:
    if not settings.has_news:
        return AgentEnvelope(
            agent=AgentName.news,
            status=AgentStatus.not_configured,
            error="No GNEWS_API_KEY or NEWSDATA_API_KEY set — sign up free at gnews.io or newsdata.io",
        )

    try:
        async with new_client() as client:
            if settings.gnews_api_key:
                raw = await _fetch_gnews(client, query)
            else:
                raw = await _fetch_newsdata(client, query)
    except Exception as exc:
        return AgentEnvelope(agent=AgentName.news, status=AgentStatus.error, error=str(exc))

    articles = []
    for a in raw:
        matched, score = _score_article(a["title"], a["snippet"])
        articles.append(NewsArticle(**a, keywords_matched=matched, escalation_score=score))

    overall = round(sum(a.escalation_score for a in articles) / len(articles), 2) if articles else 0.0
    result = NewsResult(
        query=query,
        articles=sorted(articles, key=lambda a: a.escalation_score, reverse=True),
        overall_escalation=overall,
        escalation_flag=overall >= ESCALATION_FLAG_THRESHOLD,
    )
    return AgentEnvelope(agent=AgentName.news, status=AgentStatus.ok, data=result.model_dump())
