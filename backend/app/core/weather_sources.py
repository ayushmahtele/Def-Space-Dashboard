"""Shared weather sources: Open-Meteo first (with retries), MET Norway as a fallback.

Why a fallback at all: Render's free tier sends outgoing traffic from IP addresses shared
with many other apps. Open-Meteo rate-limits per IP, so on Render its limit can already be
used up by someone else before our first call (works on localhost, fails when deployed).
MET Norway (api.met.no) is a second free, no-key source with global coverage.
"""
from __future__ import annotations

import asyncio

import httpx

from app.core.http_client import DEFAULT_TIMEOUT, new_client

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"

# MET Norway's terms of service require a User-Agent that identifies the app and a contact
# point; requests with a generic User-Agent get 403 Forbidden.
APP_USER_AGENT = "def-space-dashboard/1.0 (+https://github.com/ayushmahtele/Def-Space-Dashboard)"

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def get_open_meteo(params: dict, attempts: int = 3) -> dict:
    """GET Open-Meteo, retrying rate-limit / server errors / timeouts with a short backoff.
    Non-retryable errors (e.g. 400 for bad params) are raised immediately."""
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            async with new_client() as client:
                resp = await client.get(OPEN_METEO_URL, params=params)
            if resp.status_code in _RETRYABLE_STATUS:
                last_exc = httpx.HTTPStatusError(
                    f"Open-Meteo returned HTTP {resp.status_code}", request=resp.request, response=resp
                )
            else:
                resp.raise_for_status()
                return resp.json()
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc
        if attempt < attempts - 1:
            await asyncio.sleep(1.0 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


async def get_met_norway_timeseries(lat: float, lon: float) -> list[dict]:
    """Hourly (then 6-hourly) forecast timeseries from MET Norway, starting at the current hour."""
    # MET Norway asks clients to send at most 4 decimals so its cache works.
    params = {"lat": round(lat, 4), "lon": round(lon, 4)}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers={"User-Agent": APP_USER_AGENT}) as client:
        resp = await client.get(MET_NORWAY_URL, params=params)
        resp.raise_for_status()
        return resp.json()["properties"]["timeseries"]


def met_symbol(entry: dict) -> str | None:
    data = entry.get("data", {})
    for window in ("next_1_hours", "next_6_hours", "next_12_hours"):
        code = data.get(window, {}).get("summary", {}).get("symbol_code")
        if code:
            return code
    return None


def met_precipitation(entry: dict) -> float | None:
    data = entry.get("data", {})
    for window in ("next_1_hours", "next_6_hours"):
        amount = data.get(window, {}).get("details", {}).get("precipitation_amount")
        if amount is not None:
            return amount
    return None


def met_symbol_to_wmo(symbol: str | None) -> int:
    """Map MET Norway symbol codes to the WMO weather codes the rest of the app uses."""
    if not symbol:
        return 0
    s = symbol.split("_")[0]  # drop the _day / _night / _polartwilight suffix
    if "thunder" in s:
        return 95
    if "snow" in s or "sleet" in s:
        return 71
    if s.startswith("heavyrain"):
        return 65
    if s.startswith("lightrain"):
        return 61
    if "rain" in s:
        return 63
    if s == "fog":
        return 45
    if s == "partlycloudy":
        return 2
    if s == "cloudy":
        return 3
    if s == "fair":
        return 1
    return 0  # clearsky and anything unrecognised
