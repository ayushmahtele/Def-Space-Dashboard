from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agents.gis.routes import router as gis_router
from app.agents.news.routes import router as news_router
from app.agents.predict.routes import router as predict_router
from app.agents.rag.routes import router as rag_router
from app.agents.report.routes import router as report_router
from app.agents.translation.routes import router as translation_router
from app.agents.vision.routes import router as vision_router
from app.agents.weather.routes import router as weather_router
from app.core.config import settings
from app.orchestrator.routes import router as orchestrator_router
from app.watchlist import router as watchlist_router

app = FastAPI(
    title="Def-Space Multi-Agent Intelligence Dashboard API",
    description="Fuses satellite imagery, weather, news, maps, and government reports into on-demand AOI SITREPs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Vite falls back to 5174, 5175, etc. whenever 5173 is already taken by a stale dev
    # server from an earlier session — allow any localhost/127.0.0.1 port in dev instead
    # of hardcoding one, so the frontend doesn't silently lose backend access whenever
    # that happens (this is local-dev-only; not used for a deployed origin allowlist).
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/pdf", StaticFiles(directory=str(settings.pdf_export_dir)), name="pdf")

for router in (
    weather_router,
    news_router,
    gis_router,
    vision_router,
    rag_router,
    translation_router,
    predict_router,
    report_router,
    orchestrator_router,
    watchlist_router,
):
    app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "gemini_configured": settings.has_gemini,
        "news_configured": settings.has_news,
    }
