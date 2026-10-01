from fastapi import APIRouter

from app.agents.gis.service import fetch_gis
from app.models.schemas import AgentEnvelope, AOI

router = APIRouter(prefix="/agents/gis", tags=["gis"])


@router.get("", response_model=AgentEnvelope)
async def get_gis(name: str, lat: float, lon: float, radius_km: float = 25.0) -> AgentEnvelope:
    aoi = AOI(name=name, lat=lat, lon=lon, radius_km=radius_km)
    return await fetch_gis(aoi)
