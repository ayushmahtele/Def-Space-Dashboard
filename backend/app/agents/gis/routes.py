from fastapi import APIRouter

from app.agents.gis.service import fetch_gis
from app.core.geocode import display_name, reverse_geocode
from app.models.schemas import AgentEnvelope, AOI

router = APIRouter(prefix="/agents/gis", tags=["gis"])


@router.get("", response_model=AgentEnvelope)
async def get_gis(name: str, lat: float, lon: float, radius_km: float = 25.0) -> AgentEnvelope:
    aoi = AOI(name=name, lat=lat, lon=lon, radius_km=radius_km)
    return await fetch_gis(aoi)


@router.get("/reverse-geocode")
async def get_reverse_geocode(lat: float, lon: float) -> dict:
    """Place name for a map click. Done server-side (not in the browser) so it isn't hit by
    browser CORS / rate-limit / network-certificate problems, and results are cached."""
    info = await reverse_geocode(lat, lon)
    return {
        "name": display_name(info, lat, lon),
        "state": info.state if info else None,
        "country": info.country if info else None,
    }
