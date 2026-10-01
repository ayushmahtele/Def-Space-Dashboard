"""Weather agent — Open-Meteo (primary) with MET Norway as a fallback. Neither needs an API key.

On Render's free tier Open-Meteo is sometimes rate-limited because the server's outgoing IP
is shared with other apps (see app/core/weather_sources.py), so a second source keeps the
Weather agent working in deployment instead of reporting an error.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.weather_sources import (
    get_met_norway_timeseries,
    get_open_meteo,
    met_precipitation,
    met_symbol,
    met_symbol_to_wmo,
)
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, ForecastEntry, WeatherResult

LOW_VISIBILITY_CLOUD_PCT = 80.0  # heavy overcast — degrades EO/IR sensor and visual recon
HIGH_WIND_KMH = 40.0


def _flags(windspeed_kmh: float, clouds_next_6h: list[float | None]) -> list[str]:
    reasons = []
    clouds = [c for c in clouds_next_6h if c is not None]
    if clouds and max(clouds) >= LOW_VISIBILITY_CLOUD_PCT:
        reasons.append(f"cloud cover reaching {max(clouds):.0f}% in next 6h — degraded EO imaging")
    if windspeed_kmh >= HIGH_WIND_KMH:
        reasons.append(f"sustained wind {windspeed_kmh:.0f} km/h — UAV/airdrop ops risk")
    return reasons


def _from_open_meteo(aoi_name: str, lat: float, lon: float, payload: dict) -> WeatherResult:
    current = payload["current_weather"]
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    clouds = hourly.get("cloud_cover", [])
    visibility = hourly.get("visibility", [])
    precip = hourly.get("precipitation", [])

    forecast = [
        ForecastEntry(
            time=t,
            cloud_cover_pct=clouds[i] if i < len(clouds) else None,
            visibility_m=visibility[i] if i < len(visibility) else None,
            precipitation_mm=precip[i] if i < len(precip) else None,
        )
        for i, t in enumerate(times[:12])  # next 12 hours
    ]
    reasons = _flags(current["windspeed"], clouds[:6])
    return WeatherResult(
        aoi_name=aoi_name,
        latitude=lat,
        longitude=lon,
        temperature_c=current["temperature"],
        windspeed_kmh=current["windspeed"],
        winddirection_deg=current["winddirection"],
        weathercode=current["weathercode"],
        is_day=bool(current["is_day"]),
        forecast=forecast,
        operational_flag=bool(reasons),
        flag_reason="; ".join(reasons) if reasons else None,
        source="Open-Meteo current + hourly forecast",
    )


def _is_day_fallback(lon: float) -> bool:
    """Rough local solar time from longitude — only used if MET gives no day/night symbol."""
    utc_hour = datetime.now(timezone.utc).hour + datetime.now(timezone.utc).minute / 60
    local_hour = (utc_hour + lon / 15.0) % 24
    return 6 <= local_hour < 18


def _from_met_norway(aoi_name: str, lat: float, lon: float, series: list[dict]) -> WeatherResult:
    if not series:
        raise ValueError("MET Norway returned an empty forecast")
    now = series[0]["data"]["instant"]["details"]
    windspeed_kmh = round(now.get("wind_speed", 0.0) * 3.6, 1)  # MET reports m/s
    symbol = met_symbol(series[0])
    is_day = not symbol.endswith("_night") if symbol else _is_day_fallback(lon)

    next_12 = series[:12]
    forecast = [
        ForecastEntry(
            time=entry["time"],
            temperature_c=entry["data"]["instant"]["details"].get("air_temperature"),
            cloud_cover_pct=entry["data"]["instant"]["details"].get("cloud_area_fraction"),
            visibility_m=None,  # MET Norway's forecast has no visibility field
            precipitation_mm=met_precipitation(entry),
        )
        for entry in next_12
    ]
    reasons = _flags(windspeed_kmh, [f.cloud_cover_pct for f in forecast[:6]])
    return WeatherResult(
        aoi_name=aoi_name,
        latitude=lat,
        longitude=lon,
        temperature_c=now["air_temperature"],
        windspeed_kmh=windspeed_kmh,
        winddirection_deg=now.get("wind_from_direction", 0.0),
        weathercode=met_symbol_to_wmo(symbol),
        is_day=is_day,
        forecast=forecast,
        operational_flag=bool(reasons),
        flag_reason="; ".join(reasons) if reasons else None,
        source="MET Norway locationforecast (Open-Meteo unavailable)",
    )


async def fetch_weather(aoi_name: str, lat: float, lon: float) -> AgentEnvelope:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "cloud_cover,visibility,precipitation",
        "forecast_days": 2,
        "timezone": "UTC",
    }
    errors: list[str] = []
    try:
        result = _from_open_meteo(aoi_name, lat, lon, await get_open_meteo(params))
    except Exception as exc:
        errors.append(f"Open-Meteo: {exc}")
        try:
            result = _from_met_norway(aoi_name, lat, lon, await get_met_norway_timeseries(lat, lon))
        except Exception as exc2:  # both sources down — orchestrator degrades gracefully
            errors.append(f"MET Norway: {exc2}")
            return AgentEnvelope(agent=AgentName.weather, status=AgentStatus.error, error="; ".join(errors))
    return AgentEnvelope(agent=AgentName.weather, status=AgentStatus.ok, data=result.model_dump())
