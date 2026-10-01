from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    # Gemini (2.5 Flash for text/vision/translation, gemini-embedding-001 for RAG)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    # News — set whichever one you sign up for; GNews is tried first
    gnews_api_key: str | None = None
    newsdata_api_key: str | None = None

    # Sentinel Hub is optional; NASA GIBS (used by default) needs no key at all
    sentinelhub_client_id: str | None = None
    sentinelhub_client_secret: str | None = None

    data_dir: Path = BACKEND_ROOT / "data"
    chroma_dir: Path = BACKEND_ROOT / "data" / "chroma"
    reports_raw_dir: Path = BACKEND_ROOT / "data" / "reports_raw"
    pdf_export_dir: Path = BACKEND_ROOT / "data" / "pdf_exports"
    watchlist_file: Path = BACKEND_ROOT / "data" / "watchlist" / "aois.json"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_news(self) -> bool:
        return bool(self.gnews_api_key or self.newsdata_api_key)


settings = Settings()

for _dir in (settings.data_dir, settings.chroma_dir, settings.reports_raw_dir, settings.pdf_export_dir):
    _dir.mkdir(parents=True, exist_ok=True)
settings.watchlist_file.parent.mkdir(parents=True, exist_ok=True)
