"""Weather agent — Open-Meteo, no API key required, no rate limit on the free tier."""
from __future__ import annotations

from app.core.http_client import new_client
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, ForecastEntry, WeatherResult

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

LOW_VISIBILITY_CLOUD_PCT = 80.0  # heavy overcast — degrades EO/IR sensor and visual recon
HIGH_WIND_KMH = 40.0


async def fetch_weather(aoi_name: str, lat: float, lon: float) -> AgentEnvelope:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "cloud_cover,visibility,precipitation",
        "forecast_days": 2,
        "timezone": "UTC",
    }
    try:
        async with new_client() as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:  # network/upstream failure — orchestrator degrades gracefully
        return AgentEnvelope(agent=AgentName.weather, status=AgentStatus.error, error=str(exc))

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

    flag_reasons = []
    next_hours_cloud = [c for c in clouds[:6] if c is not None]
    if next_hours_cloud and max(next_hours_cloud) >= LOW_VISIBILITY_CLOUD_PCT:
        flag_reasons.append(f"cloud cover reaching {max(next_hours_cloud):.0f}% in next 6h — degraded EO imaging")
    if current["windspeed"] >= HIGH_WIND_KMH:
        flag_reasons.append(f"sustained wind {current['windspeed']:.0f} km/h — UAV/airdrop ops risk")

    result = WeatherResult(
        aoi_name=aoi_name,
        latitude=lat,
        longitude=lon,
        temperature_c=current["temperature"],
        windspeed_kmh=current["windspeed"],
        winddirection_deg=current["winddirection"],
        weathercode=current["weathercode"],
        is_day=bool(current["is_day"]),
        forecast=forecast,
        operational_flag=bool(flag_reasons),
        flag_reason="; ".join(flag_reasons) if flag_reasons else None,
    )
    return AgentEnvelope(agent=AgentName.weather, status=AgentStatus.ok, data=result.model_dump())
