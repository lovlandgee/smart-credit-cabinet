from pathlib import Path

import pandas as pd

from app import main


def test_train_persists_joblib_artifact(tmp_path: Path, monkeypatch) -> None:
    artifact = tmp_path / "risk_model.joblib"
    monkeypatch.setattr(main, "ARTIFACT_PATH", artifact)
    result = main.train_model()
    assert artifact.exists()
    assert result.rows > 100
    assert 0 <= result.metrics["roc_auc"] <= 1
    assert 0 <= result.metrics["f1"] <= 1


def test_predict_returns_probability(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(main, "ARTIFACT_PATH", tmp_path / "risk_model.joblib")
    main.train_model()
    result = main.predict(main.PredictRequest(features={name: 0.0 for name in main.FEATURE_NAMES}))
    assert 0 <= result["default_probability"] <= 1
    assert result["model"] == main.MODEL_VERSION


def test_temporal_validation_uses_dates(tmp_path: Path, monkeypatch) -> None:
    data = pd.DataFrame({name: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] for name in main.FEATURE_NAMES})
    data["target"] = [0, 1] * 5
    data["application_date"] = pd.date_range("2024-01-01", periods=10)
    path = tmp_path / "historical.csv"
    data.to_csv(path, index=False)
    monkeypatch.setattr(main, "TRAINING_DATA", str(path))
    monkeypatch.setattr(main, "ARTIFACT_PATH", tmp_path / "risk_model.joblib")
    result = main.train_model()
    assert result.validation["type"] == "temporal"
    assert result.validation["train_rows"] == 8
    assert result.validation["test_rows"] == 2


def test_drift_detects_shift(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(main, "ARTIFACT_PATH", tmp_path / "risk_model.joblib")
    main.train_model()
    rows = [{name: 0.0 for name in main.FEATURE_NAMES} for _ in range(20)]
    rows = [{**row, "bki_score": 1200.0} for row in rows]
    result = main.drift(main.DriftRequest(rows=rows))
    assert result["drift_detected"] is True
    assert "bki_score" in result["drifted_features"]
