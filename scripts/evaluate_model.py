"""Evaluates persisted IsolationForest anomaly detector model on unseen test split."""

import os
import sys
import pandas as pd
import joblib
import logging
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.features.schema import validate_input_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting local ML evaluation...")

    data_path = "data/evaluation/stratified_evaluation.csv"
    if not os.path.exists(data_path):
        logger.error(f"Evaluation data not found at {data_path}. Run scripts/train_model.py first.")
        return

    df_eval = pd.read_csv(data_path)
    validate_input_schema(df_eval)
    logger.info(f"Loaded {len(df_eval)} records from {data_path}")

    artifacts_dir = "models/artifacts"
    preprocessor_path = os.path.join(artifacts_dir, "preprocessor.pkl")
    detector_path = os.path.join(artifacts_dir, "anomaly_detector.pkl")

    if not os.path.exists(preprocessor_path) or not os.path.exists(detector_path):
        logger.error("Model artifacts not found. Run scripts/train_model.py first.")
        return

    preprocessor = joblib.load(preprocessor_path)
    detector = joblib.load(detector_path)
    logger.info("Loaded preprocessor and anomaly detector artifacts.")

    X_eval = preprocessor.transform(df_eval)
    y_pred_if = detector.model.predict(X_eval)
    y_pred = [1 if p == -1 else 0 for p in y_pred_if]

    if "Machine failure" not in df_eval.columns:
        logger.error("Ground truth 'Machine failure' column missing from evaluation set.")
        return
    y_true = df_eval["Machine failure"].values

    logger.info("\n--- UNSUPERVISED ANOMALY DETECTION METRICS ---")
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    logger.info(f"Precision: {precision:.4f} (When model flags anomaly, how often is it actually failing?)")
    logger.info(f"Recall:    {recall:.4f} (Out of all true failures, how many did the model catch?)")
    logger.info(f"F1 Score:  {f1:.4f}")

    logger.info("\nConfusion Matrix:")
    logger.info(f"\n{confusion_matrix(y_true, y_pred)}")


if __name__ == "__main__":
    main()
