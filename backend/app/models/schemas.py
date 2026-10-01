"""Shared response contracts used by every agent, the orchestrator, and the frontend.

Keeping these in one place is what lets the orchestrator merge six independently-built
agents into a single SITREP without every pair of agents agreeing out-of-band on shapes.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    vision = "vision"
    rag = "rag"
    weather = "weather"
    news = "news"
    gis = "gis"
    translation = "translation"
    report = "report"
    predict = "predict"


class AgentStatus(str, Enum):
    ok = "ok"
    not_configured = "not_configured"  # API key missing - agent honestly reports this, never fakes data
    error = "error"
    skipped = "skipped"  # orchestrator decided this agent wasn't relevant to the query


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AOI(BaseModel):
    name: str
    lat: float
    lon: float
    radius_km: float = 25.0
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Generic envelope every agent route returns, so the orchestrator can handle
# failures uniformly ("News API rate-limited -> dashboard still shows the other 5").
# ---------------------------------------------------------------------------
class AgentEnvelope(BaseModel):
    agent: AgentName
    status: AgentStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Weather agent
# ---------------------------------------------------------------------------
class ForecastEntry(BaseModel):
    time: str
    temperature_c: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    visibility_m: Optional[float] = None
    precipitation_mm: Optional[float] = None


class WeatherResult(BaseModel):
    aoi_name: str
    latitude: float
    longitude: float
    temperature_c: float
    windspeed_kmh: float
    winddirection_deg: float
    weathercode: int
    is_day: bool
    forecast: List[ForecastEntry] = []
    operational_flag: bool
    flag_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# News agent
# ---------------------------------------------------------------------------
class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    keywords_matched: List[str] = []
    escalation_score: float = 0.0


class NewsResult(BaseModel):
    query: str
    articles: List[NewsArticle] = []
    overall_escalation: float = 0.0
    escalation_flag: bool = False


# ---------------------------------------------------------------------------
# GIS agent
# ---------------------------------------------------------------------------
class GeoFeature(BaseModel):
    id: str
    lat: float
    lon: float
    label: str
    layer: str  # "aoi" | "news" | "weather" | "reports" | "satellite_change"
    source_agent: AgentName
    severity: Optional[Severity] = None


class GeofenceStatus(BaseModel):
    feature_id: str
    inside_zone: bool
    distance_km: float


class GISResult(BaseModel):
    aoi: AOI
    features: List[GeoFeature] = []
    geofence_statuses: List[GeofenceStatus] = []


# ---------------------------------------------------------------------------
# Vision agent
# ---------------------------------------------------------------------------
class VisionResult(BaseModel):
    aoi_name: str
    tile_before_url: Optional[str] = None
    tile_after_url: Optional[str] = None
    date_before: Optional[str] = None
    date_after: Optional[str] = None
    change_detected: Optional[bool] = None
    change_percentage: Optional[float] = None
    description: Optional[str] = None
    confidence: Optional[float] = None


# ---------------------------------------------------------------------------
# RAG agent
# ---------------------------------------------------------------------------
class RagSource(BaseModel):
    document: str
    section: Optional[str] = None
    score: float


class RagResult(BaseModel):
    query: str
    answer: str
    sources: List[RagSource] = []


# ---------------------------------------------------------------------------
# Translation agent
# ---------------------------------------------------------------------------
class TranslationResult(BaseModel):
    original_text: str
    detected_language: str
    translated_text: str


# ---------------------------------------------------------------------------
# Predict agent (launch-weather go/no-go)
# ---------------------------------------------------------------------------
class FeatureContribution(BaseModel):
    feature: str
    value: float
    contribution: float  # SHAP value for this prediction; positive pushes toward GO


class PredictResult(BaseModel):
    aoi_name: str
    latitude: float
    longitude: float
    date: str
    verdict: str  # "GO" | "NO-GO"
    go_probability: float
    weather_inputs: Dict[str, float] = {}
    feature_contributions: List[FeatureContribution] = []
    caveat: str
    methodology_note: str = ""


# ---------------------------------------------------------------------------
# Predict agent — model performance / comparison (Model Performance tab)
# ---------------------------------------------------------------------------
class ClassMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int


class ModelMetrics(BaseModel):
    key: str
    display_name: str
    accuracy: float
    go: ClassMetrics
    no_go: ClassMetrics
    macro_f1: float
    confusion_matrix: List[List[int]]  # [[TN, FP], [FN, TP]]
    is_deployed: bool


class DatasetSplitInfo(BaseModel):
    total_rows: int
    train_rows: int
    test_rows: int
    train_date_start: str
    train_date_end: str
    test_date_start: str
    test_date_end: str
    train_go: int
    train_no_go: int
    test_go: int
    test_no_go: int
    split_method: str


class ModelPerformanceResponse(BaseModel):
    dataset: DatasetSplitInfo
    models: List[ModelMetrics]
    deployed_model_key: str
    selection_rule: str
    imbalance_note: str


# ---------------------------------------------------------------------------
# Report agent (fusion layer) / final SITREP
# ---------------------------------------------------------------------------
class ProvenancedClaim(BaseModel):
    text: str
    source_agent: AgentName
    source_detail: Optional[str] = None


class Sitrep(BaseModel):
    query: str
    aoi: Optional[AOI] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    severity: Severity
    summary: str
    claims: List[ProvenancedClaim] = []
    alert: bool
    agent_statuses: Dict[str, AgentStatus] = {}
    pdf_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class OrchestrateRequest(BaseModel):
    query: str
    aoi: AOI


class OrchestrateResponse(BaseModel):
    sitrep: Sitrep
    raw: Dict[str, AgentEnvelope]
