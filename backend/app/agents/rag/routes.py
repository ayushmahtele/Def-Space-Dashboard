from fastapi import APIRouter

from app.agents.rag.ingest import ingest_reports_dir
from app.agents.rag.service import fetch_rag
from app.models.schemas import AgentEnvelope

router = APIRouter(prefix="/agents/rag", tags=["rag"])


@router.get("", response_model=AgentEnvelope)
async def get_rag(query: str) -> AgentEnvelope:
    return await fetch_rag(query)


@router.post("/ingest")
async def ingest() -> dict:
    return ingest_reports_dir()
