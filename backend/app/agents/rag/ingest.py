"""Chunk + embed .txt files dropped in backend/data/reports_raw/ into the Chroma store.

Drop real government reports / PIB press releases there as plain .txt files (one per
document, first line treated as the document title) and call ingest_reports_dir().
"""
from __future__ import annotations

from pathlib import Path

from app.agents.rag.chroma_setup import get_collection
from app.core.config import settings

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _chunk(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


def ingest_reports_dir() -> dict:
    files = sorted(settings.reports_raw_dir.glob("*.txt"))
    if not files:
        return {"documents_ingested": 0, "chunks_ingested": 0, "message": f"No .txt files found in {settings.reports_raw_dir}"}

    collection = get_collection()
    total_chunks = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        title = text.splitlines()[0].strip() if text.strip() else path.stem
        chunks = _chunk(text)
        if not chunks:
            continue
        ids = [f"{path.stem}::chunk-{i}" for i in range(len(chunks))]
        metadatas = [{"document": title, "section": f"chunk {i+1}/{len(chunks)}", "source_file": path.name} for i in range(len(chunks))]
        collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)

    return {"documents_ingested": len(files), "chunks_ingested": total_chunks}
