"""Thin wrapper around the google-genai SDK.

Every function here returns None (rather than raising) when no API key is configured,
so callers can fall back to a real, rule-based result instead of crashing or faking
an LLM response. Get a free key at https://aistudio.google.com/apikey and put it in
backend/.env as GEMINI_API_KEY=... — nothing else needs to change once it's set.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.core.config import settings


@lru_cache(maxsize=1)
def _client():
    if not settings.has_gemini:
        return None
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def generate_text(prompt: str) -> Optional[str]:
    client = _client()
    if client is None:
        return None
    response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
    return response.text


def generate_vision(prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> Optional[str]:
    client = _client()
    if client is None:
        return None
    from google.genai import types

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
    )
    return response.text


def embed_texts(texts: list[str]) -> Optional[list[list[float]]]:
    client = _client()
    if client is None:
        return None
    result = client.models.embed_content(model=settings.gemini_embedding_model, contents=texts)
    return [e.values for e in result.embeddings]
