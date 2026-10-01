from fastapi import APIRouter

from app.agents.news.service import fetch_news
from app.models.schemas import AgentEnvelope

router = APIRouter(prefix="/agents/news", tags=["news"])


@router.get("", response_model=AgentEnvelope)
async def get_news(query: str) -> AgentEnvelope:
    return await fetch_news(query)
