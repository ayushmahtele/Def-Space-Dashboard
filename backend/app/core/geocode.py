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


PHOTON_URL = "https://photon.komoot.io/reverse"  # second free OSM-based geocoder, no key


async def _nominatim(client: httpx.AsyncClient, lat: float, lon: float) -> PlaceInfo:
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": 10,  # city level
        "addressdetails": 1,
        "accept-language": "en",
    }
    resp = await client.get(NOMINATIM_URL, params=params)
    resp.raise_for_status()
    address = resp.json().get("address", {})
    if not address:
        raise ValueError("Nominatim returned no address (e.g. open ocean)")
    return PlaceInfo(
        place=address.get("city") or address.get("town") or address.get("village") or address.get("municipality"),
        district=address.get("state_district") or address.get("county"),
        state=address.get("state"),
        country=address.get("country"),
        country_code=(address.get("country_code") or "").lower() or None,
    )


async def _photon(client: httpx.AsyncClient, lat: float, lon: float) -> PlaceInfo:
    resp = await client.get(PHOTON_URL, params={"lat": lat, "lon": lon, "lang": "en"})
    resp.raise_for_status()
    features = resp.json().get("features") or []
    if not features:
        raise ValueError("Photon returned no place")
    p = features[0].get("properties", {})
    is_settlement = p.get("type") in {"city", "town", "village"} or p.get("osm_value") in {"city", "town", "village"}
    return PlaceInfo(
        place=p.get("city") or (p.get("name") if is_settlement else None),
        district=p.get("county") or p.get("district"),
        state=p.get("state"),
        country=p.get("country"),
        country_code=(p.get("countrycode") or "").lower() or None,
    )


async def reverse_geocode(lat: float, lon: float) -> PlaceInfo | None:
    """Nominatim first, Photon if Nominatim is rate-limiting or down. None if both fail."""
    key = (round(lat, 3), round(lon, 3))
    if key in _cache:
        return _cache[key]

    info = None
    async with httpx.AsyncClient(timeout=httpx.Timeout(8.0), headers={"User-Agent": APP_USER_AGENT}) as client:
        for source in (_nominatim, _photon):
            try:
                info = await source(client, lat, lon)
                break
            except Exception:
                continue  # geocoding is a nice-to-have; callers fall back to coordinates
    if info is not None:
        _cache[key] = info
    return info


def display_name(info: PlaceInfo | None, lat: float, lon: float) -> str:
    """Short human name for an AOI picked on the map, e.g. "Kanpur"."""
    if info:
        for candidate in (info.place, info.district, info.state, info.country):
            if candidate:
                return candidate
    return f"{lat:.3f}, {lon:.3f}"
