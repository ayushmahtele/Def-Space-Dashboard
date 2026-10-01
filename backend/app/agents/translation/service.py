"""Translation agent — langdetect runs fully offline (no key); translation itself
needs Gemini. News/RAG agents route non-English source text through this agent
before processing so provenance always keeps the original alongside the translation.
"""
from __future__ import annotations

from langdetect import LangDetectException, detect

from app.core.config import settings
from app.core.gemini_client import generate_text
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, TranslationResult


async def translate_text(text: str) -> AgentEnvelope:
    try:
        detected = detect(text)
    except LangDetectException:
        detected = "unknown"

    if detected == "en":
        result = TranslationResult(original_text=text, detected_language="en", translated_text=text)
        return AgentEnvelope(agent=AgentName.translation, status=AgentStatus.ok, data=result.model_dump())

    if not settings.has_gemini:
        return AgentEnvelope(
            agent=AgentName.translation,
            status=AgentStatus.not_configured,
            error=f"Detected language '{detected}' but no GEMINI_API_KEY set to translate it",
        )

    prompt = (
        f"Translate the following text (detected language: {detected}) to English. "
        f"Return ONLY the translation, no commentary:\n\n{text}"
    )
    translated = generate_text(prompt) or text
    result = TranslationResult(original_text=text, detected_language=detected, translated_text=translated.strip())
    return AgentEnvelope(agent=AgentName.translation, status=AgentStatus.ok, data=result.model_dump())
