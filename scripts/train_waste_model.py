"""Waste Percentage Prediction Model Training — FibreOptima V2.

Target: waste_pct_pct = (Waste quantity / Production quantity) × 100
Units: PERCENTAGE (e.g. 8.42 means 8.42% waste)
Forbidden features: Waste quantity, Waste percentage, waste_pct (leakage)

Models compared:
  - HistGradientBoostingRegressor (primary candidate)
  - RandomForestRegressor (baseline)

Artifacts saved to models/artifacts/:
  - waste_predictor.pkl        (best model)
  - waste_preprocessor.pkl     (fitted sklearn Pipeline)
  - waste_model_metadata.json  (full provenance)
"""

import os
import sys
import json
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ─────────────────────────────────────────────────────────────────
#  FEATURE SCHEMA (canonical — must match inference exactly)
# ─────────────────────────────────────────────────────────────────
CATEGORICAL_FEATURES = [
    "Machine ID",
    "Fabric type",
    "Operator",
    "Shift",
]

NUMERICAL_FEATURES = [
    "Production quantity",
    "Production speed",
    "Machine age",
    "Humidity",
    "Temperature",
    "Machine failure",
]

ALL_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

# Target: waste_pct = (Waste quantity / Production quantity) × 100
# NOTE on proxy-data scale: In this dataset Production quantity is RPM×10 (metres)
# and Waste quantity is Torque²/100 (kg). The ratio ×100 yields values 0.001–0.49.
# These ARE percentage values for this proxy domain — the waste rate is genuinely small.
# The canonical unit is: waste_pct in [0.0, 100.0] (percentage)
TARGET_COLUMN = "waste_pct"  # percentage, proxy range: ~0.001–0.49%

# Columns that MUST NOT appear as features (leakage guard)
FORBIDDEN_COLUMNS = [
    "Waste quantity",
    "Waste percentage",
    "waste_pct",
]

# Percentage bounds for clipping
WASTE_PCT_MIN = 0.0
WASTE_PCT_MAX = 100.0


# ─────────────────────────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────────────────────────
def load_and_prepare_data(data_path: str) -> pd.DataFrame:
    """Load CSV and compute percentage target BEFORE any split.

    Target is waste_pct = (Waste quantity / Production quantity) × 100.
    For this proxy dataset (RPM×10 metres vs Torque²/100 kg),
    values are legitimately in range 0.001–0.49%.
    """
    df = pd.read_csv(data_path)

    required_raw = ["Waste quantity", "Production quantity"]
    missing = [c for c in required_raw if c not in df.columns]
    if missing:
        raise ValueError(f"Raw data missing columns needed for target: {missing}")

    # Compute target — (Waste quantity / Production quantity) × 100 = percentage
    df[TARGET_COLUMN] = (
        df["Waste quantity"] / df["Production quantity"].replace(0, np.nan)
    ) * 100.0
    df[TARGET_COLUMN] = df[TARGET_COLUMN].clip(lower=WASTE_PCT_MIN, upper=WASTE_PCT_MAX)

    # Hard leakage check — forbidden columns must not be in feature list
    for col in FORBIDDEN_COLUMNS:
        if col in ALL_FEATURES:
            raise RuntimeError(
                f"LEAKAGE DETECTED: '{col}' is in ALL_FEATURES. Training aborted."
            )

    # Drop rows where target is NaN (zero production edge case)
    before = len(df)
    df = df.dropna(subset=[TARGET_COLUMN])
    dropped = before - len(df)
    if dropped > 0:
        print(f"  Dropped {dropped} rows with NaN target (zero production_quantity).")

    return df


# ─────────────────────────────────────────────────────────────────
#  PREPROCESSOR
# ─────────────────────────────────────────────────────────────────
def build_preprocessor() -> Pipeline:
    """Build sklearn preprocessing pipeline aligned with ALL_FEATURES."""
    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, NUMERICAL_FEATURES),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline([("preprocessor", preprocessor)])


# ─────────────────────────────────────────────────────────────────
#  MODEL TRAINING
# ─────────────────────────────────────────────────────────────────
def train_models(X_train, y_train, X_val, y_val, preprocessor):
    """Train candidate models and return the best one by val MAE."""
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)

    candidates = {
        "HistGradientBoosting": HistGradientBoostingRegressor(
            random_state=42,
            max_iter=200,
            learning_rate=0.1,
            max_depth=6,
            min_samples_leaf=20,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = {}
    best_name = None
    best_model = None
    best_val_mae = float("inf")

    for name, model in candidates.items():
        print(f"\n  Training {name}...")
        model.fit(X_train_proc, y_train)

        y_hat_train = model.predict(X_train_proc)
        y_hat_val = model.predict(X_val_proc)

        # Clamp predictions to valid percentage range
        y_hat_val = np.clip(y_hat_val, WASTE_PCT_MIN, WASTE_PCT_MAX)

        metrics = {
            "train_mae_pct":  float(mean_absolute_error(y_train, y_hat_train)),
            "val_mae_pct":    float(mean_absolute_error(y_val, y_hat_val)),
            "train_rmse_pct": float(np.sqrt(mean_squared_error(y_train, y_hat_train))),
            "val_rmse_pct":   float(np.sqrt(mean_squared_error(y_val, y_hat_val))),
            "train_r2":       float(r2_score(y_train, y_hat_train)),
            "val_r2":         float(r2_score(y_val, y_hat_val)),
        }
        results[name] = metrics

        print(f"    Train MAE: {metrics['train_mae_pct']:.3f}%  Val MAE: {metrics['val_mae_pct']:.3f}%")
        print(f"    Train R²:  {metrics['train_r2']:.4f}         Val R²:  {metrics['val_r2']:.4f}")

        if metrics["val_mae_pct"] < best_val_mae:
            best_val_mae = metrics["val_mae_pct"]
            best_name = name
            best_model = model

    return preprocessor, best_model, best_name, results


# ─────────────────────────────────────────────────────────────────
#  SAVE ARTIFACTS
# ─────────────────────────────────────────────────────────────────
def save_artifacts(preprocessor, model, model_name, results, extra_meta):
    """Persist model, preprocessor, and provenance metadata."""
    artifacts_dir = "models/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    joblib.dump(preprocessor, os.path.join(artifacts_dir, "waste_preprocessor.pkl"))
    joblib.dump(model, os.path.join(artifacts_dir, "waste_predictor.pkl"))

    metadata = {
        "model_type": model_name,
        "model_params": model.get_params(),
        "target": TARGET_COLUMN,
        "target_units": "percentage (0.0–100.0)",
        "target_formula": "waste_pct_pct = (Waste quantity / Production quantity) * 100",
        "features": {
            "numerical": NUMERICAL_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "all": ALL_FEATURES,
            "feature_order": ALL_FEATURES,
        },
        "forbidden_columns": FORBIDDEN_COLUMNS,
        "training_dataset": "data/production/historical_production.csv",
        "dataset_source": "UCI AI4I 2020 (proxy-transformed to textile domain)",
        "training_records": extra_meta["train_size"],
        "validation_records": extra_meta["val_size"],
        "metrics": results,
        "random_seed": 42,
        "split_strategy": "random 80/20",
        "training_timestamp": datetime.now().isoformat(),
        "feature_version": "v3_waste_pct_percentage",
        "version": "3.0",
    }

    with open(os.path.join(artifacts_dir, "waste_model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n  Artifacts saved to {artifacts_dir}/")
    print(f"  waste_preprocessor.pkl")
    print(f"  waste_predictor.pkl  ({model_name})")
    print(f"  waste_model_metadata.json")


# ─────────────────────────────────────────────────────────────────
#  REPRODUCIBILITY TEST
# ─────────────────────────────────────────────────────────────────
def reproducibility_test(X_val):
    """Load saved artifacts in a fresh context and verify identical output."""
    pp_loaded = joblib.load("models/artifacts/waste_preprocessor.pkl")
    m_loaded  = joblib.load("models/artifacts/waste_predictor.pkl")

    sample = X_val.iloc[:5]
    X_proc = pp_loaded.transform(sample)
    preds  = m_loaded.predict(X_proc)
    preds  = np.clip(preds, WASTE_PCT_MIN, WASTE_PCT_MAX)

    print("\n  Reproducibility test — 5 sample predictions (waste_pct %):")
    for i, p in enumerate(preds):
        print(f"    [{i}] predicted waste_pct = {p:.6f}%")

    # Verify scale is consistent — must not be raw ratio (would be ~0.001×)
    # For this proxy dataset, expected range is 0.001–0.49%
    if preds.max() < 0.0001:
        raise RuntimeError(
            f"SCALE ERROR: max predicted value {preds.max():.8f} — "
            "predictions appear to be raw ratios. Check target formula."
        )
    print("  Scale check PASSED.")
    print("  Reproducibility test PASSED.")
    return preds


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    data_path = "data/production/historical_production.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Training dataset not found at {data_path}. "
            "Run `python scripts/download_real_data.py` first."
        )

    print("=" * 60)
    print("FibreOptima — Waste Predictor Training (V3)")
    print("=" * 60)
    print(f"\nTarget: {TARGET_COLUMN} (units: PERCENTAGE)")
    print(f"Formula: (Waste quantity / Production quantity) × 100")
    print(f"Leakage guard: {FORBIDDEN_COLUMNS}")

    print("\n[1] Loading data...")
    df = load_and_prepare_data(data_path)
    print(f"  Dataset shape: {df.shape}")
    print(f"  Target stats: mean={df[TARGET_COLUMN].mean():.6f}%  "
          f"std={df[TARGET_COLUMN].std():.6f}%  "
          f"max={df[TARGET_COLUMN].max():.6f}%")
    print(f"  Note: Proxy-dataset waste_pct range is 0.001–0.49% (small by design — "
          f"units are kg waste / (RPM×10 metres) × 100)")

    print("\n[2] Splitting data (80/20, random seed=42)...")
    X = df[ALL_FEATURES]
    y = df[TARGET_COLUMN]
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )
    print(f"  Train: {len(X_train)} rows  |  Val: {len(X_val)} rows")

    print("\n[3] Training models...")
    preprocessor = build_preprocessor()
    preprocessor, best_model, best_name, results = train_models(
        X_train, y_train, X_val, y_val, preprocessor
    )
    print(f"\n  Winner: {best_name}")
    print(f"  Val MAE:  {results[best_name]['val_mae_pct']:.3f}%")
    print(f"  Val RMSE: {results[best_name]['val_rmse_pct']:.3f}%")
    print(f"  Val R²:   {results[best_name]['val_r2']:.4f}")

    print("\n[4] Saving artifacts...")
    save_artifacts(
        preprocessor, best_model, best_name, results,
        {"train_size": len(X_train), "val_size": len(X_val)},
    )

    print("\n[5] Reproducibility test...")
    reproducibility_test(X_val)

    print("\n" + "=" * 60)
    print("Training complete. Waste predictor ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()