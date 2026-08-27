"""Anomaly Detector Wrapper — V2 ML Model Wrapper.

Loads the trained IsolationForest anomaly detector.
Feature schema: operational telemetry ONLY (no waste leakage).

CLEAN — no Waste quantity, no Waste percentage in features.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


# ─── canonical feature schema (must match train_model.py exactly) ────────────
ANOMALY_FEATURE_COLS = [
    "Machine ID",
    "Fabric type",
    "Operator",
    "Shift",
    "Production quantity",
    "Production speed",
    "Machine age",
    "Humidity",
    "Temperature",
    "Machine failure",
]

ANOMALY_FORBIDDEN_COLS = ["Waste quantity", "Waste percentage", "waste_pct"]

_NUMERIC_COLS = [
    "Production quantity", "Production speed", "Machine age",
    "Humidity", "Temperature", "Machine failure",
]


class AnomalyDetector:
    """Wrapper for IsolationForest operational anomaly detection.

    Detects statistically unusual production batches based on
    operational telemetry — NOT based on waste quantity (no leakage).

    anomaly_score > 0 → more normal
    anomaly_score < 0 → more anomalous
    is_anomalous = True when the model predicts -1 (outlier)
    """

    def __init__(self, artifacts_dir: str = "models/artifacts"):
        self.artifacts_dir  = artifacts_dir
        self.preprocessor   = None
        self.model          = None
        self.metadata: Optional[Dict] = None
        self.feature_names_: List[str] = []
        self._load_artifacts()

    # ── loading ────────────────────────────────────────────────────────────
    def _load_artifacts(self) -> None:
        preprocessor_path = os.path.join(self.artifacts_dir, "preprocessor.pkl")
        model_path        = os.path.join(self.artifacts_dir, "anomaly_detector.pkl")
        metadata_path     = os.path.join(self.artifacts_dir, "model_metadata.json")

        for path, label in [(preprocessor_path, "Preprocessor"), (model_path, "Model")]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{label} artifact not found: {path}")

        self.preprocessor = joblib.load(preprocessor_path)
        self.model        = joblib.load(model_path)
        
        # FIX: Force n_jobs=1 for inference to prevent joblib multiprocessing hangs (especially on Windows during pytest)
        if hasattr(self.model, "n_jobs"):
            self.model.n_jobs = 1

        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)

        # Cache feature names from fitted preprocessor
        try:
            self.feature_names_ = list(
                self.preprocessor.named_steps["preprocessor"].get_feature_names_out()
            )
        except Exception:
            self.feature_names_ = []

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _check_leakage(df: pd.DataFrame) -> None:
        found = [c for c in ANOMALY_FORBIDDEN_COLS if c in df.columns]
        if found:
            raise ValueError(f"Anomaly detector leakage guard: {found} must not be features.")

    def _prepare(self, df: pd.DataFrame) -> np.ndarray:
        """Validate, clean, and transform input."""
        self._check_leakage(df)

        missing = [c for c in ANOMALY_FEATURE_COLS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required feature columns: {missing}. "
                f"Required: {ANOMALY_FEATURE_COLS}"
            )

        X = df[ANOMALY_FEATURE_COLS].copy()

        # Coerce numeric; replace inf with NaN (imputer will handle)
        for col in _NUMERIC_COLS:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            X[col] = X[col].replace([np.inf, -np.inf], np.nan)

        return self.preprocessor.transform(X)

    # ── primary interface ──────────────────────────────────────────────────
    def predict_anomaly(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run anomaly detection on a DataFrame.

        Returns dict with:
          anomaly_score  : float (higher = more normal, <0 = anomalous)
          is_anomalous   : bool
          feature_contributions : dict  (perturbation-based attribution)
          statistical_deviations: dict  (placeholder — historical stats needed)
        """
        X_proc = self._prepare(df)

        # IsolationForest: decision_function < 0 → anomalous
        scores = self.model.decision_function(X_proc)
        preds  = self.model.predict(X_proc)

        anomaly_score = float(scores[0])
        is_anomalous  = bool(preds[0] == -1)

        contributions = self._compute_contributions(X_proc)

        return {
            "anomaly_score":          anomaly_score,
            "is_anomalous":           is_anomalous,
            "feature_contributions":  contributions,
            "statistical_deviations": {},   # populated externally from historical stats
        }

    def predict_anomaly_single(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Run anomaly detection on a single record dict."""
        defaults = {"Machine failure": 0, "Humidity": None, "Temperature": None}
        merged = {**defaults, **record}
        df = pd.DataFrame([merged])
        return self.predict_anomaly(df)

    # ── feature attribution ────────────────────────────────────────────────
    def _compute_contributions(self, X_proc: np.ndarray) -> Dict[str, float]:
        """Estimate feature contributions via perturbation analysis."""
        if not self.feature_names_:
            return {}

        baseline = float(self.model.decision_function(X_proc)[0])
        contributions: Dict[str, float] = {}

        n_features = len(self.feature_names_)
        if n_features > 0:
            perturbed_array = np.tile(X_proc, (n_features, 1))
            for i in range(n_features):
                perturbed_array[i, i] = 0.0
                
            perturbed_scores = self.model.decision_function(perturbed_array)
            for i, fname in enumerate(self.feature_names_):
                contributions[fname] = abs(baseline - float(perturbed_scores[i]))

        total = sum(contributions.values()) or 1.0
        return {k: float(v / total) for k, v in contributions.items()}

    # ── metadata ───────────────────────────────────────────────────────────
    def get_metadata(self) -> Dict:
        return self.metadata or {}

    def get_feature_schema(self) -> Dict:
        return {
            "features": ANOMALY_FEATURE_COLS,
            "forbidden": ANOMALY_FORBIDDEN_COLS,
        }


def load_anomaly_detector(artifacts_dir: str = "models/artifacts") -> AnomalyDetector:
    """Factory function to load the anomaly detector."""
    return AnomalyDetector(artifacts_dir)