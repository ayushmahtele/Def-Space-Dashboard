from fastapi import APIRouter

from app.agents.vision.service import fetch_vision
from app.models.schemas import AgentEnvelope

router = APIRouter(prefix="/agents/vision", tags=["vision"])


@router.get("", response_model=AgentEnvelope)
async def get_vision(
    name: str, lat: float, lon: float, date_before: str | None = None, date_after: str | None = None
) -> AgentEnvelope:
    return await fetch_vision(name, lat, lon, date_before, date_after)
