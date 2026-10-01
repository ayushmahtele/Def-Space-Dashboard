from fastapi import APIRouter

from app.agents.weather.service import fetch_weather
from app.models.schemas import AgentEnvelope

router = APIRouter(prefix="/agents/weather", tags=["weather"])


@router.get("", response_model=AgentEnvelope)
async def get_weather(name: str, lat: float, lon: float) -> AgentEnvelope:
    return await fetch_weather(name, lat, lon)
