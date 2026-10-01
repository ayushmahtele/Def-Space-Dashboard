"""Predict agent — launch-weather go/no-go classifier.

Trained on real data (see backend/data/launch_weather/PROVENANCE.md): a RandomForest
over real historical weather features, labeled with the launch provider's own published
pre-launch weather-go probability. At query time this agent fetches real *current/
forecast* weather for the requested AOI from Open-Meteo (the same free, no-key source
used by the Weather agent) and reuses the trained model to produce a verdict plus a
per-prediction SHAP feature-contribution breakdown, so the Report agent can explain why.
"""
from __future__ import annotations

import json
from datetime import date as date_cls
from functools import lru_cache
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
import shap

from app.core.http_client import new_client
from app.models.schemas import (
    AgentEnvelope,
    AgentName,
    AgentStatus,
    FeatureContribution,
    ModelPerformanceResponse,
    PredictResult,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "launch_weather"
MODEL_PATH = DATA_DIR / "model.joblib"
BACKGROUND_PATH = DATA_DIR / "background.joblib"
COMPARISON_PATH = DATA_DIR / "comparison_metrics.json"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CAVEAT = (
    "Trained on ~469 real historical SpaceX Falcon 9 launches (2016-2023 train / "
    "2024-2026 test, temporal split). The label reproduces the launch provider's own "
    "published pre-launch weather-go call (thresholded at 50%), not a reconstructed "
    "scrub history — public launch records don't expose that. NO-GO calls are rare in "
    "the training data (~5%), so treat a NO-GO verdict as a signal to double-check "
    "conditions, not a certainty. See the Model Performance tab and PROVENANCE.md for detail."
)

METHODOLOGY_NOTE = (
    "This model learned weather-risk patterns from historical launches at fixed SpaceX "
    "pads — it does not have historical launch data for this specific AOI. What it's "
    "doing here is applying those learned patterns to this AOI's real current/forecast "
    "weather, fetched live for these exact coordinates."
)


@lru_cache(maxsize=1)
def _load_model():
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["feature_columns"]


@lru_cache(maxsize=1)
def _load_background() -> pd.DataFrame:
    # A small real sample of training rows used as the reference distribution for SHAP.
    # Using the model-agnostic Explainer (rather than TreeExplainer) so this keeps working
    # regardless of which of the 4 compared model types (tree-based or linear) ends up
    # deployed — see train.py's select_deployed_model.
    return joblib.load(BACKGROUND_PATH)


async def predict_go_no_go(aoi_name: str, lat: float, lon: float, target_date: Optional[str] = None) -> AgentEnvelope:
    try:
        model, feature_columns = _load_model()
    except FileNotFoundError:
        return AgentEnvelope(
            agent=AgentName.predict,
            status=AgentStatus.not_configured,
            error="Model not trained yet — run `python -m app.agents.predict.train` in backend/.",
        )

    day = target_date or date_cls.today().isoformat()
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,windgusts_10m_max,cloudcover_mean",
        "start_date": day,
        "end_date": day,
        "timezone": "UTC",
    }
    try:
        async with new_client() as client:
            resp = await client.get(OPEN_METEO_FORECAST_URL, params=params)
            resp.raise_for_status()
            payload = resp.json()
        daily = payload["daily"]
        weather_inputs = {
            "temp_max_c": daily["temperature_2m_max"][0],
            "temp_min_c": daily["temperature_2m_min"][0],
            "precipitation_mm": daily["precipitation_sum"][0],
            "windspeed_max_kmh": daily["windspeed_10m_max"][0],
            "windgusts_max_kmh": daily["windgusts_10m_max"][0],
            "cloudcover_mean_pct": daily["cloudcover_mean"][0],
        }
    except Exception as exc:  # network/upstream failure — orchestrator degrades gracefully
        return AgentEnvelope(agent=AgentName.predict, status=AgentStatus.error, error=str(exc))

    row = pd.DataFrame([[weather_inputs[col] for col in feature_columns]], columns=feature_columns)
    go_probability = float(model.predict_proba(row)[0][1])
    verdict = "GO" if go_probability >= 0.5 else "NO-GO"

    # Model-agnostic explainer (wraps predict_proba directly) rather than TreeExplainer —
    # the deployed model is auto-selected in train.py from 4 candidates (tree-based and
    # linear), so this has to work regardless of which one is currently live.
    background = _load_background()
    explainer = shap.Explainer(model.predict_proba, background)
    shap_values = explainer(row)
    values = shap_values.values
    go_contribs = values[0][:, 1] if values.ndim == 3 else values[0]

    contributions = [
        FeatureContribution(feature=col, value=weather_inputs[col], contribution=float(go_contribs[i]))
        for i, col in enumerate(feature_columns)
    ]
    contributions.sort(key=lambda c: abs(c.contribution), reverse=True)

    result = PredictResult(
        aoi_name=aoi_name,
        latitude=lat,
        longitude=lon,
        date=day,
        verdict=verdict,
        go_probability=go_probability,
        weather_inputs=weather_inputs,
        feature_contributions=contributions,
        caveat=CAVEAT,
        methodology_note=METHODOLOGY_NOTE,
    )
    return AgentEnvelope(agent=AgentName.predict, status=AgentStatus.ok, data=result.model_dump())


def get_model_performance() -> ModelPerformanceResponse:
    """Reads the comparison metrics written by train.py (see that file's docstring for
    the temporal split rationale and the deployed-model selection rule)."""
    raw = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    return ModelPerformanceResponse(**raw)
