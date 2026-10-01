"""RAG agent — cosine-similarity retrieval over ingested gov reports, then a
Gemini answer grounded in (and citing) the retrieved chunks only."""
from __future__ import annotations

from app.agents.rag.chroma_setup import get_collection
from app.core.config import settings
from app.core.gemini_client import generate_text
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, RagResult, RagSource

TOP_K = 4


async def fetch_rag(query: str) -> AgentEnvelope:
    if not settings.has_gemini:
        return AgentEnvelope(
            agent=AgentName.rag,
            status=AgentStatus.not_configured,
            error="No GEMINI_API_KEY set — needed for both embeddings and grounded answers",
        )

    collection = get_collection()
    if collection.count() == 0:
        return AgentEnvelope(
            agent=AgentName.rag,
            status=AgentStatus.error,
            error="No documents ingested yet — POST /agents/rag/ingest after adding .txt files to backend/data/reports_raw/",
        )

    try:
        results = collection.query(query_texts=[query], n_results=min(TOP_K, collection.count()))
    except Exception as exc:
        return AgentEnvelope(agent=AgentName.rag, status=AgentStatus.error, error=str(exc))

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    sources = [
        RagSource(document=m["document"], section=m.get("section"), score=round(1 - d, 3))
        for m, d in zip(metas, distances)
    ]

    context = "\n\n".join(f"[{m['document']} — {m.get('section', '')}]\n{doc}" for doc, m in zip(docs, metas))
    prompt = (
        "You are a defense analyst assistant. Answer the question ONLY using the excerpts below. "
        "If the excerpts don't contain the answer, say so explicitly — do not use outside knowledge. "
        f"Cite the document name for every claim.\n\nExcerpts:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    )
    try:
        answer = generate_text(prompt)
    except Exception:  # Gemini quota/overload/network — still return what retrieval found
        answer = None
    if not answer:
        top_doc, top_meta = docs[0], metas[0]
        excerpt = " ".join(top_doc.split())[:400]
        answer = (
            "Gemini is unavailable right now (quota or network), so no synthesized answer. "
            f"Most relevant excerpt — {top_meta['document']}: \"{excerpt}...\""
        )

    result = RagResult(query=query, answer=answer, sources=sources)
    return AgentEnvelope(agent=AgentName.rag, status=AgentStatus.ok, data=result.model_dump())
