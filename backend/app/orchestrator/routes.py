from fastapi import APIRouter

from app.models.schemas import OrchestrateRequest, OrchestrateResponse
from app.orchestrator.run import orchestrate

router = APIRouter(prefix="/orchestrate", tags=["orchestrator"])


@router.post("", response_model=OrchestrateResponse)
async def post_orchestrate(body: OrchestrateRequest) -> OrchestrateResponse:
    return await orchestrate(body.query, body.aoi)
