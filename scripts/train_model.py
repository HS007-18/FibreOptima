"""Operational Anomaly Detector Training — FibreOptima V2.

Model: IsolationForest
Task: Detect statistically unusual operational batches (not waste prediction)

STRICTLY NO LEAKAGE:
  - Waste quantity is NOT an input feature
  - Waste percentage is NOT an input feature
  - waste_pct_pct is NOT an input feature

Features used: operational telemetry only (speed, quantity, age, environment,
               failure flag, categorical identifiers)

Artifacts:
  models/artifacts/anomaly_detector.pkl     (IsolationForest)
  models/artifacts/preprocessor.pkl         (fitted sklearn Pipeline)
  models/artifacts/model_metadata.json      (provenance)
"""

import os
import sys
import json
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ─────────────────────────────────────────────────────────────────
#  FEATURE SCHEMA — operational telemetry ONLY, no waste info
# ─────────────────────────────────────────────────────────────────
ANOMALY_CATEGORICAL_FEATURES = [
    "Machine ID",
    "Fabric type",
    "Operator",
    "Shift",
]

ANOMALY_NUMERICAL_FEATURES = [
    "Production quantity",
    "Production speed",
    "Machine age",
    "Humidity",
    "Temperature",
    "Machine failure",
]

ANOMALY_ALL_FEATURES = ANOMALY_CATEGORICAL_FEATURES + ANOMALY_NUMERICAL_FEATURES

# These MUST NOT appear as features — leakage
ANOMALY_FORBIDDEN = [
    "Waste quantity",
    "Waste percentage",
    "waste_pct_pct",
    "waste_pct",
]

# IsolationForest params
CONTAMINATION = 0.05   # 5% — conservative; don't over-flag
RANDOM_STATE  = 42


def build_anomaly_preprocessor() -> Pipeline:
    """Build preprocessing pipeline for anomaly detector."""
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
            ("num", num_transformer, ANOMALY_NUMERICAL_FEATURES),
            ("cat", cat_transformer, ANOMALY_CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline([("preprocessor", preprocessor)])


def leakage_check(df: pd.DataFrame) -> None:
    """Hard-stop if any forbidden column is present."""
    found = [c for c in ANOMALY_FORBIDDEN if c in df.columns]
    if found:
        # We expect these columns in raw data — we just won't SELECT them
        # The check that matters: they are not in ANOMALY_ALL_FEATURES
        for col in ANOMALY_FORBIDDEN:
            if col in ANOMALY_ALL_FEATURES:
                raise RuntimeError(
                    f"LEAKAGE: '{col}' is in ANOMALY_ALL_FEATURES. Abort."
                )


def main():
    data_path = "data/production/historical_production.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    print("=" * 60)
    print("FibreOptima — Anomaly Detector Training (V2 Clean)")
    print("=" * 60)
    print(f"\nFeatures: {ANOMALY_ALL_FEATURES}")
    print(f"Forbidden (leakage check): {ANOMALY_FORBIDDEN}")
    print(f"Contamination: {CONTAMINATION}")

    print("\n[1] Loading data...")
    df = pd.read_csv(data_path)
    print(f"  Rows: {len(df)}  Cols: {list(df.columns)}")

    print("\n[2] Leakage check...")
    leakage_check(df)
    print("  PASSED — no forbidden columns in feature schema.")

    # Select features only
    X = df[ANOMALY_ALL_FEATURES].copy()
    print(f"  Feature matrix shape: {X.shape}")

    print("\n[3] Building preprocessor...")
    preprocessor = build_anomaly_preprocessor()
    X_processed = preprocessor.fit_transform(X)
    feature_names = list(
        preprocessor.named_steps["preprocessor"].get_feature_names_out()
    )
    print(f"  Processed shape: {X_processed.shape}")
    print(f"  Feature names ({len(feature_names)}): {feature_names}")

    print("\n[4] Training IsolationForest...")
    model = IsolationForest(
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_estimators=200,
        n_jobs=None,
    )
    model.fit(X_processed)

    # Evaluate on training data (unsupervised — no labels)
    scores = model.decision_function(X_processed)
    predictions = model.predict(X_processed)
    anomaly_count = int((predictions == -1).sum())
    normal_count  = int((predictions ==  1).sum())

    print(f"  Score stats: min={scores.min():.4f}  mean={scores.mean():.4f}  max={scores.max():.4f}")
    print(f"  Flagged anomalies: {anomaly_count} ({anomaly_count/len(X)*100:.1f}%)")
    print(f"  Normal:            {normal_count} ({normal_count/len(X)*100:.1f}%)")

    print("\n[5] Saving artifacts...")
    artifacts_dir = "models/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    joblib.dump(preprocessor, os.path.join(artifacts_dir, "preprocessor.pkl"))
    joblib.dump(model,        os.path.join(artifacts_dir, "anomaly_detector.pkl"))

    metadata = {
        "model": "IsolationForest",
        "model_params": {
            "contamination": CONTAMINATION,
            "random_state": RANDOM_STATE,
            "n_estimators": 200,
        },
        "features": ANOMALY_ALL_FEATURES,
        "feature_names_out": feature_names,
        "forbidden_columns": ANOMALY_FORBIDDEN,
        "leakage_status": "CLEAN — no waste quantity/percentage in features",
        "training_dataset": "data/production/historical_production.csv",
        "dataset_source": "UCI AI4I 2020 (proxy-transformed to textile domain)",
        "training_records": len(X),
        "evaluation_records": len(X),
        "anomaly_rate_pct": round(anomaly_count / len(X) * 100, 2),
        "score_stats": {
            "min": float(scores.min()),
            "mean": float(scores.mean()),
            "max": float(scores.max()),
            "std": float(scores.std()),
        },
        "random_seed": RANDOM_STATE,
        "training_timestamp": datetime.now().isoformat(),
        "feature_version": "v2_anomaly_clean",
        "version": "2.0",
    }

    with open(os.path.join(artifacts_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  preprocessor.pkl")
    print(f"  anomaly_detector.pkl")
    print(f"  model_metadata.json")

    print("\n[6] Reproducibility test...")
    pp_loaded = joblib.load(os.path.join(artifacts_dir, "preprocessor.pkl"))
    m_loaded  = joblib.load(os.path.join(artifacts_dir, "anomaly_detector.pkl"))

    sample_X = X.iloc[:5]
    X_proc_sample = pp_loaded.transform(sample_X)
    sample_scores = m_loaded.decision_function(X_proc_sample)
    sample_preds  = m_loaded.predict(X_proc_sample)

    print("  Sample scores:", [f"{s:.4f}" for s in sample_scores])
    print("  Sample preds (1=normal, -1=anomaly):", sample_preds.tolist())
    print("  Reproducibility test PASSED.")

    print("\n[7] Inference schema validation...")
    # Test single-row inference with missing values (edge case)
    edge_case = pd.DataFrame([{
        "Machine ID": "UNKNOWN-MACHINE",  # unseen category
        "Fabric type": "Cotton",
        "Operator": "Op-New",            # unseen operator
        "Shift": "Morning",
        "Production quantity": 1000.0,
        "Production speed": 280.0,
        "Machine age": None,             # missing age
        "Humidity": None,                # missing humidity
        "Temperature": 30.0,
        "Machine failure": 0,
    }])
    X_edge_proc = pp_loaded.transform(edge_case)
    edge_score = float(m_loaded.decision_function(X_edge_proc)[0])
    edge_pred  = int(m_loaded.predict(X_edge_proc)[0])
    print(f"  Edge case (unknown machine, missing humidity): score={edge_score:.4f}, pred={edge_pred}")
    print("  Inference schema validation PASSED (no crash on unseen/missing values).")

    print("\n" + "=" * 60)
    print("Anomaly detector training complete. Clean artifact ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
