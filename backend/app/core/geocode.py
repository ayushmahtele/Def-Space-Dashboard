"""Reverse geocoding via Nominatim (OpenStreetMap) — free, no key, ~1 request/second.

Used by the News agent so a search for an AOI is pinned to the right place: an AOI named
"Kota" at 25.15, 75.85 becomes Kota + Rajasthan + India, instead of matching every place
called Kota (e.g. Kota Tinggi in Malaysia).
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.weather_sources import APP_USER_AGENT

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


@dataclass(frozen=True)
class PlaceInfo:
    place: str | None  # city / town / village
    district: str | None
    state: str | None
    country: str | None
    country_code: str | None  # ISO 3166-1 alpha-2, lowercase (e.g. "in")


# Results never change for a given point, so cache them — also keeps us well inside
# Nominatim's usage policy when the same AOI is queried repeatedly.
_cache: dict[tuple[float, float], PlaceInfo] = {}


async def reverse_geocode(lat: float, lon: float) -> PlaceInfo | None:
    key = (round(lat, 3), round(lon, 3))
    if key in _cache:
        return _cache[key]

    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": 10,  # city level
        "addressdetails": 1,
        "accept-language": "en",
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0), headers={"User-Agent": APP_USER_AGENT}) as client:
            resp = await client.get(NOMINATIM_URL, params=params)
            resp.raise_for_status()
            address = resp.json().get("address", {})
    except Exception:
        return None  # geocoding is a nice-to-have; callers fall back to the AOI name alone

    info = PlaceInfo(
        place=address.get("city") or address.get("town") or address.get("village") or address.get("municipality"),
        district=address.get("state_district") or address.get("county"),
        state=address.get("state"),
        country=address.get("country"),
        country_code=(address.get("country_code") or "").lower() or None,
    )
    _cache[key] = info
    return info
