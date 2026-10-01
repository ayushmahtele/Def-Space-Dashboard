"""Vision agent — NASA GIBS satellite tiles (no API key) + OpenCV change detection,
with an optional Gemini vision pass for a natural-language description once a key is set.

Cloud handling: a raw pixel difference between two daily satellite images is dominated by
clouds (a monsoon-season tile vs a clear one reads as "90% change"). So the agent
  1. tries several dates around each target date and keeps the least cloudy tile,
  2. masks cloud (bright, colourless) and no-data (black swath-gap) pixels in both images,
  3. evens out overall brightness between the two dates and compares in colour, and
  4. measures change only on pixels that are clear on BOTH dates — or reports the
     comparison as inconclusive when too little of the area is clear.

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
CHANGE_THRESHOLD = 30  # largest per-channel colour delta (0-255) counted as "changed"
BLANK_STDDEV = 3.0  # a tile this uniform is a "no data" placeholder, not real imagery

CLOUD_MIN_CHANNEL = 185  # cloud: every colour channel very bright (bright sand/concrete stays below)...
CLOUD_MAX_SPREAD = 40  # ...and nearly colourless (white/grey)
NO_DATA_MAX_CHANNEL = 12  # near-black pixels are gaps between satellite passes
MIN_CLEAR_OVERLAP = 0.25  # need at least 25% of the tile clear on both dates to compare
GOOD_ENOUGH_CLEAR = 0.9  # stop searching dates once a tile is this clear
AFTER_DAYS_AGO = (1, 2, 3, 5, 7)  # candidate dates for the "recent" image
BEFORE_DAYS_AGO = (30, 33, 36, 40)  # candidate dates for the "month earlier" image


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
    """Colour (BGR) image, or None if the bytes aren't an image or the tile is blank (no data)."""
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None or float(img.std()) < BLANK_STDDEV:
        return None
    return img


def _clear_mask(bgr: np.ndarray) -> np.ndarray:
    """True where the ground is visible: not cloud, not a no-data gap."""
    channels = bgr.astype(np.int16)
    lo, hi = channels.min(axis=2), channels.max(axis=2)
    cloud = (lo >= CLOUD_MIN_CHANNEL) & (hi - lo <= CLOUD_MAX_SPREAD)
    no_data = hi <= NO_DATA_MAX_CHANNEL
    return ~(cloud | no_data)


async def _best_tile(client, layer: str, days: list[date], xtile: int, ytile: int):
    """Least cloudy usable tile among the candidate dates: (date, url, bytes, image, clear_mask)."""
    best = None
    for day in days:
        url = _tile_url(layer, day, xtile, ytile)
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            continue
        img = _decode(resp.content)
        if img is None:
            continue
        clear = _clear_mask(img)
        if best is None or clear.mean() > best[4].mean():
            best = (day, url, resp.content, img, clear)
        if clear.mean() >= GOOD_ENOUGH_CLEAR:
            break
    return best


async def fetch_vision(aoi_name: str, lat: float, lon: float, date_before: str | None, date_after: str | None) -> AgentEnvelope:
    today = date.today()
    # Explicit dates are used as given; otherwise search a few nearby dates for the clearest tile.
    after_days = [date.fromisoformat(date_after)] if date_after else [today - timedelta(days=d) for d in AFTER_DAYS_AGO]
    before_days = [date.fromisoformat(date_before)] if date_before else [today - timedelta(days=d) for d in BEFORE_DAYS_AGO]
    xtile, ytile = _latlon_to_tile(lat, lon, ZOOM)

    # Use the first satellite layer that has real (non-blank) imagery for both periods.
    chosen = None
    errors: list[str] = []
    async with new_client() as client:
        for layer in GIBS_LAYERS:
            after = await _best_tile(client, layer, after_days, xtile, ytile)
            before = await _best_tile(client, layer, before_days, xtile, ytile) if after else None
            if after and before:
                chosen = (layer, before, after)
                break
            errors.append(f"{layer}: no imagery for these dates")

    if chosen is None:
        return AgentEnvelope(
            agent=AgentName.vision,
            status=AgentStatus.error,
            error="No usable NASA GIBS imagery — " + "; ".join(errors),
        )
    layer, (d_before, url_before, bytes_before, img_before, clear_before), (d_after, url_after, bytes_after, img_after, clear_after) = chosen

    if img_before.shape != img_after.shape:
        size = (img_before.shape[1], img_before.shape[0])
        img_after = cv2.resize(img_after, size)
        clear_after = cv2.resize(clear_after.astype(np.uint8), size, interpolation=cv2.INTER_NEAREST).astype(bool)

    cloud_before_pct = round(100.0 * (1 - clear_before.mean()), 1)
    cloud_after_pct = round(100.0 * (1 - clear_after.mean()), 1)
    overlap = clear_before & clear_after
    clear_overlap_pct = round(100.0 * overlap.mean(), 1)

    change_percentage = None
    change_detected = None
    note = None
    if overlap.mean() < MIN_CLEAR_OVERLAP:
        note = (
            f"Too cloudy to compare: only {clear_overlap_pct}% of the area is clear on both "
            f"{d_before.isoformat()} and {d_after.isoformat()} (cloud cover {cloud_before_pct}% → {cloud_after_pct}%)."
        )
    else:
        # Compare in colour, not grayscale: green vegetation turning into brown cleared land can
        # have the same brightness, so a grayscale difference would miss it.
        before_f = img_before.astype(np.float32)
        after_f = img_after.astype(np.float32)
        # Even out overall brightness per channel (sun angle, haze) so it isn't counted as change.
        for c in range(3):
            mean_after = float(after_f[..., c][overlap].mean())
            if mean_after > 0:
                after_f[..., c] *= float(before_f[..., c][overlap].mean()) / mean_after
        diff = np.abs(before_f - after_f).max(axis=2)
        changed_pixels = int(np.count_nonzero((diff > CHANGE_THRESHOLD) & overlap))
        change_percentage = round(100.0 * changed_pixels / int(overlap.sum()), 2)
        change_detected = change_percentage >= 5.0

    description = None
    if settings.has_gemini:
        prompt = (
            f"You are a defense imagery analyst. The two images are true-color satellite tiles "
            f"({layer.split('_')[0]}, roughly 250-375 m per pixel) of the same area around {aoi_name} "
            f"(lat {lat}, lon {lon}): the FIRST is from {d_before.isoformat()}, the SECOND from "
            f"{d_after.isoformat()}. Cloud cover was {cloud_before_pct}% and {cloud_after_pct}%; on the "
            f"{clear_overlap_pct}% of the area clear in both, OpenCV measured "
            f"{change_percentage if change_percentage is not None else 'no reliable'}% change. "
            f"Do not describe cloud differences as ground change. "
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

    if description:
        confidence = 0.7
    elif change_percentage is not None:
        # heuristic-only; scaled down when little of the area could actually be compared
        confidence = round(min(0.6, change_percentage / 100.0 + 0.2) * min(1.0, overlap.mean() / 0.5), 2)
    else:
        confidence = None

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
        cloud_cover_before_pct=cloud_before_pct,
        cloud_cover_after_pct=cloud_after_pct,
        clear_overlap_pct=clear_overlap_pct,
        note=note,
    )
    return AgentEnvelope(agent=AgentName.vision, status=AgentStatus.ok, data=result.model_dump())
