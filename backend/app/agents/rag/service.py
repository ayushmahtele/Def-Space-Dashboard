"""RAG agent — cosine-similarity retrieval over ingested gov reports, then a
Gemini answer grounded in (and citing) the retrieved chunks only."""
from __future__ import annotations

import re

from app.agents.rag.chroma_setup import get_collection
from app.core.config import settings
from app.core.gemini_client import generate_text
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, RagResult, RagSource

TOP_K = 4
_URL = re.compile(r"https?://\S+|www\.\S+")


_LIST_BULLETS = re.compile(r"[•▪●]")
_SPACED_SLUG = re.compile(r"\w+ - \w+ - \w+")  # URL slugs broken up by the PDF-to-text step


def _is_link_list(text: str) -> bool:
    """True for chunks that are mostly URLs (a document's "references" section): they match
    queries on vocabulary but contain nothing to quote or answer from."""
    urls = _URL.findall(text)
    prose = _URL.sub(" ", text)
    words = re.findall(r"[^\W\d_]{2,}", prose)
    url_chars = sum(len(u) for u in urls)
    if len(words) < 25 or url_chars > 0.5 * len(text.strip() or "x"):
        return True
    # Reference lists whose links were split up by spaces: several URLs plus bullets or slug fragments.
    return len(urls) >= 2 and (len(_LIST_BULLETS.findall(text)) >= 4 or len(_SPACED_SLUG.findall(text)) >= 2)


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
        # Fetch extra candidates so there are still TOP_K left after dropping link-only chunks.
        results = collection.query(query_texts=[query], n_results=min(TOP_K * 3, collection.count()))
    except Exception as exc:
        return AgentEnvelope(agent=AgentName.rag, status=AgentStatus.error, error=str(exc))

    candidates = list(zip(results["documents"][0], results["metadatas"][0], results["distances"][0]))
    kept = [c for c in candidates if not _is_link_list(c[0])][:TOP_K] or candidates[:TOP_K]
    docs = [c[0] for c in kept]
    metas = [c[1] for c in kept]
    distances = [c[2] for c in kept]

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
