"""Chroma vector store wiring for the RAG agent, embedding with gemini-embedding-001."""
from __future__ import annotations

import chromadb
from chromadb.api.types import EmbeddingFunction

from app.core.config import settings
from app.core.gemini_client import embed_texts

COLLECTION_NAME = "gov_reports"


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self) -> None:
        pass

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = embed_texts(list(input))
        if embeddings is None:
            raise RuntimeError("GEMINI_API_KEY not configured — cannot embed documents")
        return embeddings

    @staticmethod
    def name() -> str:
        return "gemini-embedding-001"

    def get_config(self) -> dict:
        return {}

    @staticmethod
    def build_from_config(config: dict) -> "GeminiEmbeddingFunction":
        return GeminiEmbeddingFunction()


_chroma_client = None


def get_collection():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return _chroma_client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=GeminiEmbeddingFunction())
