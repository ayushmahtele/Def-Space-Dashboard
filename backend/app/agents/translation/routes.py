from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.translation.service import translate_text
from app.models.schemas import AgentEnvelope

router = APIRouter(prefix="/agents/translation", tags=["translation"])


class TranslationRequest(BaseModel):
    text: str


@router.post("", response_model=AgentEnvelope)
async def post_translation(body: TranslationRequest) -> AgentEnvelope:
    return await translate_text(body.text)
