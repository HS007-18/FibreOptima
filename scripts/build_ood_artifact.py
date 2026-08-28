"""Build OOD Artifact from historical training data.

This script fits the OODDetector on the training dataset and saves
the resulting statistics to `models/artifacts/ood_metadata.json`.
It does NOT retrain any ML models.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.v2.ood_detector import OODDetector
from scripts.train_waste_model import load_and_prepare_data, NUMERICAL_FEATURES, CATEGORICAL_FEATURES

def build_ood_artifact():
    print("=" * 60)
    print("FibreOptima — Building OOD Artifact")
    print("=" * 60)
    
    data_path = "data/production/historical_production.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training dataset not found at {data_path}.")
        
    print(f"[1] Loading dataset: {data_path}")
    df = load_and_prepare_data(data_path)
    
    print("[2] Fitting OODDetector...")
    detector = OODDetector()
    detector.fit(df, NUMERICAL_FEATURES, CATEGORICAL_FEATURES)
    
    print("[3] Saving artifact...")
    detector.save()
    
    print("\nOOD statistics computed for:")
    print("  Numerical:", list(detector.stats["numerical"].keys()))
    print("  Categorical:", list(detector.stats["categorical"].keys()))
    
    print("\nArtifact saved successfully.")

if __name__ == "__main__":
    build_ood_artifact()
