"""Vision agent — NASA GIBS satellite tiles (no API key) + OpenCV change detection,
with an optional Gemini vision pass for a natural-language description once a key is set.

The OpenCV change detection never depends on Gemini: if Gemini is out of quota or down,
the agent still returns the measured change percentage, just without the prose description.
Note on scale: these are MODIS/VIIRS daily tiles (~250-375 m per pixel), so they show
large-area change (cloud, floods, burn scars, vegetation), not individual buildings.
"""
from __future__ import annotations

import asyncio
import math
from datetime import date, timedelta

import cv2
import numpy as np

from app.core.config import settings
from app.core.gemini_client import generate_vision
from app.core.http_client import new_client
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, VisionResult

# Tried in order. MODIS Terra is the original source, but Terra is an ageing satellite;
# VIIRS (Suomi-NPP, NOAA-20) gives the same kind of daily true-colour imagery.
GIBS_LAYERS = [
    "MODIS_Terra_CorrectedReflectance_TrueColor",
    "VIIRS_SNPP_CorrectedReflectance_TrueColor",
    "VIIRS_NOAA20_CorrectedReflectance_TrueColor",
]
GIBS_MATRIX_SET = "GoogleMapsCompatible_Level9"
ZOOM = 7
CHANGE_THRESHOLD = 25  # pixel intensity delta (0-255) counted as "changed"
BLANK_STDDEV = 3.0  # a tile this uniform is a "no data" placeholder, not real imagery


def _latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    n = 2**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def _tile_url(layer: str, day: date, xtile: int, ytile: int) -> str:
    return (
        f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/"
        f"{day.isoformat()}/{GIBS_MATRIX_SET}/{ZOOM}/{ytile}/{xtile}.jpg"
    )


def _decode(data: bytes):
    """Grayscale image, or None if the bytes aren't an image or the tile is blank (no data)."""
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None or float(img.std()) < BLANK_STDDEV:
        return None
    return img


async def _fetch_tile(client, url: str):
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.content, _decode(resp.content)


async def fetch_vision(aoi_name: str, lat: float, lon: float, date_before: str | None, date_after: str | None) -> AgentEnvelope:
    today = date.today()
    d_after = date.fromisoformat(date_after) if date_after else today - timedelta(days=2)
    d_before = date.fromisoformat(date_before) if date_before else today - timedelta(days=32)
    xtile, ytile = _latlon_to_tile(lat, lon, ZOOM)

    # Use the first layer that has real (non-blank) imagery for BOTH dates.
    chosen = None
    errors: list[str] = []
    async with new_client() as client:
        for layer in GIBS_LAYERS:
            url_before = _tile_url(layer, d_before, xtile, ytile)
            url_after = _tile_url(layer, d_after, xtile, ytile)
            try:
                bytes_before, img_before = await _fetch_tile(client, url_before)
                bytes_after, img_after = await _fetch_tile(client, url_after)
            except Exception as exc:
                errors.append(f"{layer}: {type(exc).__name__}")
                continue
            if img_before is None or img_after is None:
                errors.append(f"{layer}: no imagery for these dates")
                continue
            chosen = (layer, url_before, url_after, bytes_before, bytes_after, img_before, img_after)
            break

    if chosen is None:
        return AgentEnvelope(
            agent=AgentName.vision,
            status=AgentStatus.error,
            error="No usable NASA GIBS imagery — " + "; ".join(errors),
        )
    layer, url_before, url_after, bytes_before, bytes_after, img_before, img_after = chosen

    if img_before.shape != img_after.shape:
        img_after = cv2.resize(img_after, (img_before.shape[1], img_before.shape[0]))
    diff = cv2.absdiff(img_before, img_after)
    changed_pixels = int(np.count_nonzero(diff > CHANGE_THRESHOLD))
    change_percentage = round(100.0 * changed_pixels / diff.size, 2)
    change_detected = change_percentage >= 5.0

    description = None
    if settings.has_gemini:
        prompt = (
            f"You are a defense imagery analyst. The two images are true-color satellite tiles "
            f"({layer.split('_')[0]}, roughly 250-375 m per pixel) of the same area around {aoi_name} "
            f"(lat {lat}, lon {lon}): the FIRST is from {d_before.isoformat()}, the SECOND from "
            f"{d_after.isoformat()}. OpenCV measured {change_percentage}% of pixels as changed. "
            f"Describe visible large-area changes (cloud cover, water, vegetation, burn scars, urban extent) "
            f"in 2-3 concise sentences for a situational report. At this resolution individual buildings "
            f"are not visible, so do not claim specific construction. If no material change is visible, say so."
        )
        try:
            # The Gemini SDK call is blocking — run it in a thread so other agents keep running.
            description = await asyncio.to_thread(
                generate_vision, prompt, bytes_before, "image/jpeg", [bytes_after]
            )
        except Exception:
            description = None  # quota/overload/network — keep the OpenCV result regardless

    confidence = 0.7 if description else min(0.6, change_percentage / 100.0 + 0.2)  # heuristic-only

    result = VisionResult(
        aoi_name=aoi_name,
        tile_before_url=url_before,
        tile_after_url=url_after,
        date_before=d_before.isoformat(),
        date_after=d_after.isoformat(),
        change_detected=change_detected,
        change_percentage=change_percentage,
        description=description,
        confidence=confidence,
    )
    return AgentEnvelope(agent=AgentName.vision, status=AgentStatus.ok, data=result.model_dump())
