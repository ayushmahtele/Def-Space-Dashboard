"""Vision agent — NASA GIBS satellite tiles (no API key) + OpenCV change detection,
with an optional Gemini vision pass for a natural-language description once a key is set.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import cv2
import numpy as np

from app.core.config import settings
from app.core.gemini_client import generate_vision
from app.core.http_client import new_client
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, VisionResult

GIBS_LAYER = "MODIS_Terra_CorrectedReflectance_TrueColor"
GIBS_MATRIX_SET = "GoogleMapsCompatible_Level9"
ZOOM = 7
CHANGE_THRESHOLD = 25  # pixel intensity delta (0-255) counted as "changed"


def _latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    n = 2**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def _tile_url(day: date, xtile: int, ytile: int) -> str:
    return (
        f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{GIBS_LAYER}/default/"
        f"{day.isoformat()}/{GIBS_MATRIX_SET}/{ZOOM}/{ytile}/{xtile}.jpg"
    )


async def _fetch_tile_bytes(client, url: str) -> bytes:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.content


async def fetch_vision(aoi_name: str, lat: float, lon: float, date_before: str | None, date_after: str | None) -> AgentEnvelope:
    today = date.today()
    d_after = date.fromisoformat(date_after) if date_after else today - timedelta(days=2)
    d_before = date.fromisoformat(date_before) if date_before else today - timedelta(days=32)

    xtile, ytile = _latlon_to_tile(lat, lon, ZOOM)
    url_before = _tile_url(d_before, xtile, ytile)
    url_after = _tile_url(d_after, xtile, ytile)

    try:
        async with new_client() as client:
            bytes_before = await _fetch_tile_bytes(client, url_before)
            bytes_after = await _fetch_tile_bytes(client, url_after)
    except Exception as exc:
        return AgentEnvelope(agent=AgentName.vision, status=AgentStatus.error, error=str(exc))

    img_before = cv2.imdecode(np.frombuffer(bytes_before, np.uint8), cv2.IMREAD_GRAYSCALE)
    img_after = cv2.imdecode(np.frombuffer(bytes_after, np.uint8), cv2.IMREAD_GRAYSCALE)

    change_percentage = None
    change_detected = None
    if img_before is not None and img_after is not None:
        if img_before.shape != img_after.shape:
            img_after = cv2.resize(img_after, (img_before.shape[1], img_before.shape[0]))
        diff = cv2.absdiff(img_before, img_after)
        changed_pixels = int(np.count_nonzero(diff > CHANGE_THRESHOLD))
        change_percentage = round(100.0 * changed_pixels / diff.size, 2)
        change_detected = change_percentage >= 5.0

    description = None
    confidence = None
    if settings.has_gemini and img_after is not None:
        prompt = (
            f"You are a defense imagery analyst. These are two true-color satellite tiles of the same "
            f"location ({aoi_name}, lat {lat}, lon {lon}), dated {d_before.isoformat()} and {d_after.isoformat()}. "
            f"Describe any visible changes (construction, vegetation, water, cloud cover, infrastructure) "
            f"in 2-3 concise sentences suitable for a military situational report. If no material change "
            f"is visible, say so plainly."
        )
        description = generate_vision(prompt, bytes_after, "image/jpeg")
        confidence = 0.7 if description else None
    elif change_percentage is not None:
        confidence = min(0.6, change_percentage / 100.0 + 0.2)  # heuristic-only, no LLM in the loop

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
