"""Waste Percentage Predictor — V2 ML Model Wrapper.

Loads the trained HistGradientBoostingRegressor and provides a clean
prediction interface.

Output unit: waste_pct in percentage (%).
For the proxy dataset the typical range is 0.001–0.49%.

Feature schema (must match training exactly — see waste_model_metadata.json):
  Categorical: Machine ID, Fabric type, Operator, Shift
  Numerical:   Production quantity, Production speed, Machine age,
               Humidity, Temperature, Machine failure

FORBIDDEN as input features (leakage):
  Waste quantity, Waste percentage, waste_pct
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional


# ─── canonical feature order ────────────────────────────────────────────────
WASTE_FEATURE_COLS = [
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

WASTE_FORBIDDEN_COLS = ["Waste quantity", "Waste percentage", "waste_pct"]


class WastePredictor:
    """Wrapper for the trained waste percentage regression model.

    All predictions are returned in percentage units (waste_pct %).
    For the proxy dataset this is typically 0.001–0.49%.
    """

    def __init__(self, artifacts_dir: str = "models/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.preprocessor = None
        self.model = None
        self.metadata: Optional[Dict] = None
        self._load_artifacts()

    # ── loading ────────────────────────────────────────────────────────────
    def _load_artifacts(self) -> None:
        preprocessor_path = os.path.join(self.artifacts_dir, "waste_preprocessor.pkl")
        model_path        = os.path.join(self.artifacts_dir, "waste_predictor.pkl")
        metadata_path     = os.path.join(self.artifacts_dir, "waste_model_metadata.json")

        for path, label in [(preprocessor_path, "Preprocessor"), (model_path, "Model")]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{label} artifact not found: {path}")

        self.preprocessor = joblib.load(preprocessor_path)
        self.model        = joblib.load(model_path)

        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)

    # ── leakage guard ──────────────────────────────────────────────────────
    @staticmethod
    def _check_leakage(df: pd.DataFrame) -> None:
        """Raise ValueError if any forbidden (leakage) column is in the DataFrame."""
        found = [c for c in WASTE_FORBIDDEN_COLS if c in df.columns]
        if found:
            raise ValueError(
                f"Leakage guard triggered: forbidden columns present in input: {found}. "
                f"These are target-derived and must not be passed as features."
            )

    # ── prediction interface ───────────────────────────────────────────────
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict waste percentage for a DataFrame of records.

        Args:
            df: DataFrame containing at minimum all WASTE_FEATURE_COLS.
                Missing optional columns will be imputed by the preprocessor.

        Returns:
            np.ndarray of waste_pct predictions (percentage, e.g. 0.116).
        """
        # Leakage check
        self._check_leakage(df)

        # Validate required columns
        missing = [c for c in WASTE_FEATURE_COLS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required feature columns: {missing}. "
                f"Required schema: {WASTE_FEATURE_COLS}"
            )

        # Select features in canonical order
        X = df[WASTE_FEATURE_COLS].copy()

        # Handle inf/nan in numerical cols — preprocessor imputer handles NaN
        # but infinity must be clamped first
        num_cols = ["Production quantity", "Production speed", "Machine age",
                    "Humidity", "Temperature", "Machine failure"]
        for col in num_cols:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            X[col] = X[col].replace([np.inf, -np.inf], np.nan)

        # Handle zero / negative production quantity
        X["Production quantity"] = X["Production quantity"].clip(lower=0.0)

        X_proc = self.preprocessor.transform(X)
        preds  = self.model.predict(X_proc)

        # Clamp to valid percentage range
        preds = np.clip(preds, 0.0, 100.0)
        return preds

    def predict_single(self, record: Dict[str, Any]) -> float:
        """Predict waste percentage for a single record dict.

        Args:
            record: dict with keys matching WASTE_FEATURE_COLS.
                    Unknown/unseen categoricals are handled via OneHotEncoder
                    with handle_unknown='ignore'.

        Returns:
            float: predicted waste_pct (percentage).
        """
        # Provide defaults for missing optional values
        defaults = {
            "Machine failure": 0,
            "Humidity": None,
            "Temperature": None,
        }
        merged = {**defaults, **record}

        df = pd.DataFrame([merged])
        preds = self.predict(df)
        return float(preds[0])

    # ── metadata ───────────────────────────────────────────────────────────
    def get_metadata(self) -> Dict:
        return self.metadata or {}

    def get_feature_schema(self) -> Dict:
        return {
            "features": WASTE_FEATURE_COLS,
            "forbidden": WASTE_FORBIDDEN_COLS,
            "target": "waste_pct",
            "target_units": "percentage",
        }


def load_waste_predictor(artifacts_dir: str = "models/artifacts") -> WastePredictor:
    """Factory function to load the waste predictor."""
    return WastePredictor(artifacts_dir)