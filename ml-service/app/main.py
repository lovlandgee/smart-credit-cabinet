from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "revenue_growth", "profit_margin", "debt_load", "amount_to_revenue",
    "bki_score", "overdue_90d", "registration_years", "tax_arrears", "legal_risk_flags",
]
ARTIFACT_PATH = Path(os.getenv("ML_ARTIFACT_PATH", "/app/artifacts/risk_model.joblib"))
TRAINING_DATA = os.getenv("ML_TRAINING_DATA", "/app/data/historical_applications.csv")
MODEL_VERSION = os.getenv("ML_MODEL_VERSION", "risk-logistic-v1")
DATE_COLUMN = os.getenv("ML_DATE_COLUMN", "application_date")
DRIFT_THRESHOLD = float(os.getenv("ML_DRIFT_THRESHOLD", "0.2"))

class PredictRequest(BaseModel):
    features: dict[str, float] = Field(..., description="Named model features")

class TrainResponse(BaseModel):
    model_version: str
    source: str
    rows: int
    metrics: dict[str, float]
    validation: dict[str, Any]

class DriftRequest(BaseModel):
    rows: list[dict[str, float]]


def synthetic_data() -> tuple[pd.DataFrame, pd.Series, str]:
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(rng.normal(0, 1, size=(1600, len(FEATURE_NAMES))), columns=FEATURE_NAMES)
    frame["revenue_growth"] = rng.uniform(-.45, .65, len(frame))
    frame["profit_margin"] = rng.uniform(-.15, .35, len(frame))
    frame["debt_load"] = rng.uniform(.02, 1.25, len(frame))
    frame["amount_to_revenue"] = rng.uniform(.03, .85, len(frame))
    frame["bki_score"] = rng.uniform(420, 820, len(frame))
    frame["overdue_90d"] = rng.integers(0, 4, len(frame))
    frame["registration_years"] = rng.uniform(1, 15, len(frame))
    frame["tax_arrears"] = rng.integers(0, 2, len(frame))
    frame["legal_risk_flags"] = rng.integers(0, 3, len(frame))
    signal = (-2.4 * frame.revenue_growth - 3.2 * frame.profit_margin + 3.1 * frame.debt_load + 2.4 * frame.amount_to_revenue - .009 * (frame.bki_score - 600) + .8 * frame.overdue_90d - .08 * frame.registration_years + 1.3 * frame.tax_arrears + .5 * frame.legal_risk_flags + rng.normal(0, .35, len(frame)))
    return frame, pd.Series((signal > .8).astype(int), name="target"), "synthetic-demo"


def load_data() -> tuple[pd.DataFrame, pd.Series, str, pd.Series | None]:
    path = Path(TRAINING_DATA)
    if not path.exists():
        x, y, source = synthetic_data()
        return x, y, source, None
    frame = pd.read_csv(path)
    missing = set(FEATURE_NAMES + ["target", DATE_COLUMN]) - set(frame.columns)
    if missing:
        raise ValueError(f"Training data is missing columns: {sorted(missing)}")
    dates = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    if dates.isna().any():
        raise ValueError(f"Column {DATE_COLUMN} contains invalid dates")
    if dates.nunique() < 2:
        raise ValueError("Temporal validation requires at least two distinct dates")
    order = dates.sort_values().index
    return frame.loc[order, FEATURE_NAMES].astype(float), frame.loc[order, "target"].astype(int), str(path), dates.loc[order]


def train_model() -> TrainResponse:
    x, y, source, dates = load_data()
    if y.nunique() < 2:
        raise ValueError("Training target must contain both classes 0 and 1")
    if dates is None:
        split = int(len(x) * .8)
        validation = {"type": "synthetic-fallback", "train_rows": split, "test_rows": len(x) - split}
    else:
        split = max(1, min(len(x) - 1, int(len(x) * .8)))
        validation = {"type": "temporal", "train_end": dates.iloc[split - 1].date().isoformat(), "test_start": dates.iloc[split].date().isoformat(), "train_rows": split, "test_rows": len(x) - split}
    x_train, x_test = x.iloc[:split], x.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("Temporal train/test split must contain both target classes")
    model = Pipeline([("scale", StandardScaler()), ("classifier", LogisticRegression(max_iter=500, solver="lbfgs", random_state=42))])
    model.fit(x_train, y_train)
    probability = model.predict_proba(x_test)[:, 1]
    predicted = (probability >= .5).astype(int)
    metrics = {"roc_auc": float(roc_auc_score(y_test, probability)), "average_precision": float(average_precision_score(y_test, probability)), "accuracy": float(accuracy_score(y_test, predicted)), "f1": float(f1_score(y_test, predicted))}
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    reference = {name: {"mean": float(x_train[name].mean()), "std": float(x_train[name].std() or 1.0)} for name in FEATURE_NAMES}
    joblib.dump({"model": model, "features": FEATURE_NAMES, "version": MODEL_VERSION, "metrics": metrics, "source": source, "reference": reference, "validation": validation}, ARTIFACT_PATH)
    return TrainResponse(model_version=MODEL_VERSION, source=source, rows=len(x), metrics=metrics, validation=validation)


def artifact() -> dict[str, Any]:
    if ARTIFACT_PATH.exists():
        data = joblib.load(ARTIFACT_PATH)
        if data.get("version") == MODEL_VERSION and "reference" in data and "validation" in data:
            return data
    train_model()
    return joblib.load(ARTIFACT_PATH)

app = FastAPI(title="Credit Risk ML Service", version="1.0.0")

@app.on_event("startup")
def startup() -> None:
    artifact()

@app.get("/health")
def health() -> dict[str, Any]:
    data = artifact()
    return {"status": "ok", "model_version": data["version"], "source": data["source"], "metrics": data["metrics"], "validation": data.get("validation")}

@app.get("/metrics")
def metrics() -> dict[str, Any]:
    data = artifact()
    return {"model_version": data["version"], "source": data["source"], "metrics": data["metrics"], "validation": data.get("validation")}

@app.post("/train", response_model=TrainResponse)
def train() -> TrainResponse:
    try:
        return train_model()
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/drift")
def drift(payload: DriftRequest) -> dict[str, Any]:
    data = artifact()
    if not payload.rows:
        raise HTTPException(status_code=400, detail="rows must not be empty")
    current = pd.DataFrame(payload.rows).reindex(columns=FEATURE_NAMES).astype(float)
    if current.isna().any().any():
        raise HTTPException(status_code=400, detail="rows contain missing model features")
    details = {}
    for name in FEATURE_NAMES:
        ref = data["reference"][name]
        z_score = abs(float(current[name].mean()) - ref["mean"]) / max(ref["std"], 1e-9)
        details[name] = {"z_score": round(z_score, 4), "drifted": z_score >= DRIFT_THRESHOLD}
    drifted = [name for name, value in details.items() if value["drifted"]]
    return {"model_version": data["version"], "rows": len(current), "drift_detected": bool(drifted), "drifted_features": drifted, "threshold": DRIFT_THRESHOLD, "features": details}

@app.post("/predict")
def predict(payload: PredictRequest) -> dict[str, Any]:
    data = artifact()
    values = [payload.features.get(name, 0.0) for name in FEATURE_NAMES]
    probability = float(data["model"].predict_proba(pd.DataFrame([values], columns=FEATURE_NAMES))[0][1])
    return {"model": data["version"], "default_probability": round(probability, 4), "score": round(980 - probability * 730), "risk_band": "high" if probability >= .67 else "medium" if probability >= .35 else "low", "features": payload.features, "metrics": data["metrics"], "source": data["source"], "disclaimer": "Проверяйте модель на одобренных исторических данных перед production."}
