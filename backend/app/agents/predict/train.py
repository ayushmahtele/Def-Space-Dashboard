"""Trains and compares 4 classifiers on the real, sourced dataset in
backend/data/launch_weather/launch_weather_dataset.csv (see PROVENANCE.md there).

Only uses features that are also obtainable for an arbitrary AOI at query time (real
historical/forecast weather from Open-Meteo) — deliberately excludes launch-pad identity
and the free-text `weather_concerns_raw` field, since those aren't available when a user
asks about an arbitrary location that isn't a SpaceX launch pad. Train/serve feature
parity avoids the model silently depending on inputs the live agent can't supply.

TEMPORAL SPLIT (not random 80/20): the dataset spans 2016-03-04 to 2026-07-30. A random
split would let the model "see" weather patterns from dates chronologically after the
ones it's tested on, which isn't realistic for a model meant to generalize to future
launches. Train = 2016-2023, test = 2024-2026 (option "B" from the actual per-year class
distribution check — chosen because 2016-2021 alone contains only 5 real NO-GO examples
total, too few to anchor a 6-year-only training window, and this split gives the test set
substantially more NO-GO examples (10) than a random 80/20 split did (5), for more
meaningful precision/recall).

Trains 4 classifiers on the identical split for comparison (RandomForest, XGBoost,
Logistic Regression, Gradient Boosting), all using class weighting (not synthetic
oversampling) to handle the ~5% NO-GO rate honestly. The model with the best NO-GO
F1-score on the temporal test set is auto-selected as the deployed model (see
`select_deployed_model` below) and saved as model.joblib for predict/service.py to load;
all 4 are saved individually too, and full comparison metrics are written to
comparison_metrics.json for the Model Performance UI tab.

Run with: venv/Scripts/python.exe -m app.agents.predict.train
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "launch_weather"
CSV_PATH = DATA_DIR / "launch_weather_dataset.csv"
MODEL_PATH = DATA_DIR / "model.joblib"
BACKGROUND_PATH = DATA_DIR / "background.joblib"
COMPARISON_PATH = DATA_DIR / "comparison_metrics.json"
METRICS_PATH = DATA_DIR / "metrics.json"

FEATURE_COLUMNS = [
    "temp_max_c",
    "temp_min_c",
    "precipitation_mm",
    "windspeed_max_kmh",
    "windgusts_max_kmh",
    "cloudcover_mean_pct",
]
TARGET_COLUMN = "label_go"

TRAIN_CUTOFF_YEAR = 2024  # train: date.year < this; test: date.year >= this

IMBALANCE_NOTE = (
    "GO/NO-GO is heavily imbalanced (~5% NO-GO across the full dataset, real launches, "
    "not sampled) because NO-GO calls are genuinely rare events. Accuracy alone is "
    "misleading here — a model that always predicts GO would score ~91% accuracy on the "
    "test set while catching zero NO-GO cases. Precision/recall/F1 on the NO-GO class "
    "specifically are the numbers that actually reflect whether this model is useful."
)


def select_deployed_model(results: dict) -> str:
    """Picks the model with the best NO-GO F1 (the class that actually matters here),
    tie-broken by macro-F1 then accuracy. Documented explicitly rather than defaulting
    to "highest accuracy," which the imbalance makes a misleading metric on its own."""
    def sort_key(item):
        key, r = item
        report = r["classification_report"]
        return (report["NO-GO"]["f1-score"], report["macro avg"]["f1-score"], r["accuracy"])

    return max(results.items(), key=sort_key)[0]


def build_models(y_train: pd.Series) -> dict:
    neg, pos = int((y_train == 0).sum()), int((y_train == 1).sum())
    scale_pos_weight = neg / pos if pos else 1.0

    return {
        "random_forest": (
            "Random Forest",
            RandomForestClassifier(n_estimators=300, max_depth=6, class_weight="balanced", random_state=42),
            None,  # sample_weight — None means the estimator handles balancing itself
        ),
        "xgboost": (
            "XGBoost",
            XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                eval_metric="logloss",
            ),
            None,
        ),
        "logistic_regression": (
            "Logistic Regression",
            Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)),
            ]),
            None,
        ),
        "gradient_boosting": (
            "Gradient Boosting",
            GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42),
            "balanced",  # sklearn's GradientBoostingClassifier has no class_weight param — use sample_weight
        ),
    }


def main() -> None:
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    train_mask = df["date"].dt.year < TRAIN_CUTOFF_YEAR
    test_mask = ~train_mask
    train_df, test_df = df[train_mask], df[test_mask]

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN]

    dataset_info = {
        "total_rows": len(df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_date_start": train_df["date"].min().date().isoformat(),
        "train_date_end": train_df["date"].max().date().isoformat(),
        "test_date_start": test_df["date"].min().date().isoformat(),
        "test_date_end": test_df["date"].max().date().isoformat(),
        "train_go": int((y_train == 1).sum()),
        "train_no_go": int((y_train == 0).sum()),
        "test_go": int((y_test == 1).sum()),
        "test_no_go": int((y_test == 0).sum()),
        "split_method": (
            f"Temporal split (not random): train on all launches before {TRAIN_CUTOFF_YEAR}, "
            f"test on {TRAIN_CUTOFF_YEAR} onward. Chosen over a random 80/20 split because "
            "2016-2021 alone contains only 5 real NO-GO examples — too few to anchor a "
            "training-only window — and this split roughly doubles the NO-GO count "
            "available in the test set versus the random split used previously."
        ),
    }

    models = build_models(y_train)
    results: dict[str, dict] = {}

    for key, (display_name, model, sample_weight_mode) in models.items():
        if sample_weight_mode == "balanced":
            sw = compute_sample_weight("balanced", y_train)
            model.fit(X_train, y_train, sample_weight=sw)
        else:
            model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, target_names=["NO-GO", "GO"], output_dict=True)
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[key] = {
            "display_name": display_name,
            "accuracy": report["accuracy"],
            "classification_report": report,
            "confusion_matrix": cm,
        }

        joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, DATA_DIR / f"model_{key}.joblib")

        print(f"\n=== {display_name} ===")
        print(classification_report(y_test, y_pred, target_names=["NO-GO", "GO"]))
        print("Confusion matrix [[TN, FP], [FN, TP]]:", cm)

    deployed_key = select_deployed_model(results)
    deployed_model = models[deployed_key][1]
    joblib.dump({"model": deployed_model, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)

    background = X_train.sample(min(50, len(X_train)), random_state=42).reset_index(drop=True)
    joblib.dump(background, BACKGROUND_PATH)

    print(f"\nDeployed model (best NO-GO F1, see select_deployed_model): {results[deployed_key]['display_name']} ({deployed_key})")

    comparison = {
        "dataset": dataset_info,
        "imbalance_note": IMBALANCE_NOTE,
        "selection_rule": (
            "The deployed model is the one with the best F1-score on the NO-GO class "
            "specifically (ties broken by macro-avg F1, then accuracy) — not the "
            "highest raw accuracy, which is misleading on this imbalanced a dataset."
        ),
        "deployed_model_key": deployed_key,
        "models": [
            {
                "key": key,
                "display_name": r["display_name"],
                "accuracy": r["accuracy"],
                "go": {
                    "precision": r["classification_report"]["GO"]["precision"],
                    "recall": r["classification_report"]["GO"]["recall"],
                    "f1_score": r["classification_report"]["GO"]["f1-score"],
                    "support": int(r["classification_report"]["GO"]["support"]),
                },
                "no_go": {
                    "precision": r["classification_report"]["NO-GO"]["precision"],
                    "recall": r["classification_report"]["NO-GO"]["recall"],
                    "f1_score": r["classification_report"]["NO-GO"]["f1-score"],
                    "support": int(r["classification_report"]["NO-GO"]["support"]),
                },
                "macro_f1": r["classification_report"]["macro avg"]["f1-score"],
                "confusion_matrix": r["confusion_matrix"],
                "is_deployed": key == deployed_key,
            }
            for key, r in results.items()
        ],
    }
    COMPARISON_PATH.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(f"Wrote {COMPARISON_PATH}")

    # Kept for backward compatibility with anything still reading the single-model file —
    # mirrors the deployed model's own metrics.
    METRICS_PATH.write_text(
        json.dumps(
            {
                "n_train": len(X_train),
                "n_test": len(X_test),
                "classification_report": results[deployed_key]["classification_report"],
                "confusion_matrix": results[deployed_key]["confusion_matrix"],
                "note": IMBALANCE_NOTE,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {METRICS_PATH}")
    print(f"Wrote {MODEL_PATH} (deployed) and {BACKGROUND_PATH}")


if __name__ == "__main__":
    main()
