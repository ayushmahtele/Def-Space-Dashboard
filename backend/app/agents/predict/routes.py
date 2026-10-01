from typing import Optional

from fastapi import APIRouter

from app.agents.predict.service import get_model_performance, predict_go_no_go
from app.models.schemas import AgentEnvelope, ModelPerformanceResponse

router = APIRouter(prefix="/agents/predict", tags=["predict"])


@router.get("", response_model=AgentEnvelope)
async def get_prediction(name: str, lat: float, lon: float, date: Optional[str] = None) -> AgentEnvelope:
    return await predict_go_no_go(name, lat, lon, date)


@router.get("/model-performance", response_model=ModelPerformanceResponse)
async def model_performance() -> ModelPerformanceResponse:
    return get_model_performance()
