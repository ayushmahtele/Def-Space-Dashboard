"""News agent — GNews (primary) or NewsData.io (fallback) free tiers.

Both require a free API key (~100-200 req/day). Without one, this agent reports
AgentStatus.not_configured rather than inventing headlines — the orchestrator then
still assembles a SITREP from whichever other agents did run.
"""
from __future__ import annotations

import re

import httpx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.core.config import settings
from app.core.geocode import PlaceInfo, reverse_geocode
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


# Country codes GNews accepts for its `country` filter; anything else is searched worldwide.
GNEWS_COUNTRIES = {
    "au", "br", "ca", "cn", "eg", "fr", "de", "gr", "hk", "in", "ie", "il", "it", "jp", "nl", "no",
    "pk", "pe", "ph", "pt", "ro", "ru", "sg", "es", "se", "ch", "tw", "ua", "gb", "us",
}

# Administrative suffixes from map-click names ("Pipalda Tehsil", "Kakinada Rural") that news
# articles almost never include — searching with them returns nothing.
_ADMIN_SUFFIXES = {"tehsil", "rural", "urban", "district", "taluk", "taluka", "mandal", "block", "subdivision"}
_COORD_NAME = re.compile(r"^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$")
MAX_QUERY_ATTEMPTS = 3  # each attempt is one API request; free tiers allow ~100-200/day


def _clean_place_name(name: str) -> str:
    words = name.replace(",", " ").split()
    while len(words) > 1 and words[-1].lower() in _ADMIN_SUFFIXES:
        words.pop()
    return " ".join(words)


def build_queries(aoi_name: str, place: PlaceInfo | None) -> list[str]:
    """Most specific search first, broadening only if it finds nothing. With location info,
    "Kota" at 25.15, 75.85 becomes '"Kota" AND Rajasthan' (Indian sources only), so it no
    longer matches Kota Tinggi in Malaysia."""
    is_coords = bool(_COORD_NAME.match(aoi_name))
    name = None if is_coords else _clean_place_name(aoi_name)
    if place:
        name = name or place.place or place.district
    queries: list[str] = []
    if name and place and place.state and place.state.lower() != name.lower():
        queries.append(f'"{name}" AND "{place.state}"')
    if name:
        queries.append(f'"{name}"')
    if place and place.district and (not name or place.district.lower() != name.lower()):
        queries.append(f'"{place.district}"')
    if place and place.state:
        queries.append(f'"{place.state}"')
    if not queries:  # raw coordinates and geocoding failed — nothing better to search for
        queries.append(aoi_name)
    seen: set[str] = set()
    return [q for q in queries if not (q in seen or seen.add(q))]


def _safe_error(exc: Exception) -> str:
    """httpx error messages include the full request URL — which contains the API key as a
    query parameter. Never let that reach the SITREP / PDF / browser."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"news API returned HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return "news API timed out"
    return type(exc).__name__


async def _fetch_gnews(client, query: str, country: str | None = None) -> list[dict]:
    params = {"q": query, "token": settings.gnews_api_key, "lang": "en", "max": 15, "sortby": "publishedAt"}
    if country in GNEWS_COUNTRIES:
        params["country"] = country
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


async def _fetch_newsdata(client, query: str, country: str | None = None) -> list[dict]:
    params = {"apikey": settings.newsdata_api_key, "q": query, "language": "en"}
    if country:
        params["country"] = country
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


async def fetch_news(query: str, lat: float | None = None, lon: float | None = None) -> AgentEnvelope:
    """`query` is the AOI name. When the AOI's coordinates are given, the search is pinned to
    that location (place + state, filtered to the country's news sources)."""
    if not settings.has_news:
        return AgentEnvelope(
            agent=AgentName.news,
            status=AgentStatus.not_configured,
            error="No GNEWS_API_KEY or NEWSDATA_API_KEY set — sign up free at gnews.io or newsdata.io",
        )

    place = await reverse_geocode(lat, lon) if lat is not None and lon is not None else None
    country = place.country_code if place else None
    fetch = _fetch_gnews if settings.gnews_api_key else _fetch_newsdata

    raw: list[dict] = []
    used_query: str | None = None
    last_error: Exception | None = None
    async with new_client() as client:
        for candidate in build_queries(query, place)[:MAX_QUERY_ATTEMPTS]:
            try:
                raw = await fetch(client, candidate, country)
            except Exception as exc:  # e.g. a 400 on an unusual query — try the next, broader one
                last_error = exc
                continue
            used_query = candidate
            if raw:
                break
    if used_query is None:  # every attempt failed (bad key, rate limit, network)
        return AgentEnvelope(agent=AgentName.news, status=AgentStatus.error, error=_safe_error(last_error))

    country_filtered = country and (country in GNEWS_COUNTRIES or not settings.gnews_api_key)
    if country_filtered and place and place.country:
        used_query = f"{used_query} ({place.country} sources)"

    articles = []
    for a in raw:
        matched, score = _score_article(a["title"], a["snippet"])
        articles.append(NewsArticle(**a, keywords_matched=matched, escalation_score=score))

    overall = round(sum(a.escalation_score for a in articles) / len(articles), 2) if articles else 0.0
    result = NewsResult(
        query=used_query,
        articles=sorted(articles, key=lambda a: a.escalation_score, reverse=True),
        overall_escalation=overall,
        escalation_flag=overall >= ESCALATION_FLAG_THRESHOLD,
    )
    return AgentEnvelope(agent=AgentName.news, status=AgentStatus.ok, data=result.model_dump())
