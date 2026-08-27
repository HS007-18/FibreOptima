"""End-to-end investigation script for FibreOptima."""

import os
import sys
import json
import pandas as pd
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.features.schema import validate_input_schema
from src.agent.investigator import InvestigationAgent


def main():
    data_path = "data/evaluation/stratified_evaluation.csv"
    if not os.path.exists(data_path):
        data_path = "data/production/historical_production.csv"

    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}. Run scripts/download_real_data.py first.")
        return

    df_eval = pd.read_csv(data_path)
    validate_input_schema(df_eval)

    artifacts_dir = "models/artifacts"
    preprocessor_path = os.path.join(artifacts_dir, "preprocessor.pkl")
    detector_path = os.path.join(artifacts_dir, "anomaly_detector.pkl")
    metadata_path = os.path.join(artifacts_dir, "model_metadata.json")

    if not os.path.exists(preprocessor_path) or not os.path.exists(detector_path):
        print("Model artifacts missing. Run scripts/train_model.py first.")
        return

    preprocessor = joblib.load(preprocessor_path)
    detector = joblib.load(detector_path)

    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            print(f"Loaded Model Artifact Version: {metadata.get('feature_version')} (Trained: {metadata.get('training_timestamp')})")

    # Select an anomalous or high waste sample record
    high_waste = df_eval[df_eval["Waste quantity"] > 10.0]
    sample_record = high_waste.iloc[[0]] if not high_waste.empty else df_eval.iloc[[0]]

    packet = detector.analyze_record(sample_record, preprocessor)

    print("\n" + "=" * 60)
    print("--- ANOMALY INTELLIGENCE PACKET ---")
    print(f"Batch Record ID      : {packet.record_id}")
    print(f"Risk Classification  : {packet.risk_class}")
    print(f"Anomaly Score        : {packet.anomaly_score:.4f}")
    print(f"ML Anomaly Flag      : {packet.ml_anomaly_flag}")
    print(f"Business Rule Flag   : {packet.business_rule_flag}")
    print("=" * 60 + "\n")

    agent = InvestigationAgent()
    report = agent.investigate(packet)

    print("--- AGENTIC INVESTIGATION REPORT ---")
    print(report)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
