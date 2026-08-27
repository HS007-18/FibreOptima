import pytest
import pandas as pd
import numpy as np
from src.v2.anomaly_detector import AnomalyDetector, ANOMALY_FEATURE_COLS

@pytest.fixture
def sample_record():
    return {
        "Batch ID": "B-TEST-01",
        "Machine ID": "M-01",
        "Fabric type": "Cotton",
        "Operator": "Op-1",
        "Shift": "Morning",
        "Production quantity": 1000.0,
        "Production speed": 280.0,
        "Machine age": 12.0,
        "Humidity": 40.0,
        "Temperature": 30.0,
        "Machine failure": 0,
    }

def test_anomaly_detector_loads_and_predicts(sample_record):
    detector = AnomalyDetector()
    
    # Test dictionary inference
    result = detector.predict_anomaly_single(sample_record)
    
    assert "anomaly_score" in result
    assert "is_anomalous" in result
    assert "feature_contributions" in result
    assert isinstance(result["anomaly_score"], float)
    assert isinstance(result["is_anomalous"], bool)

def test_anomaly_detector_leakage_guard(sample_record):
    detector = AnomalyDetector()
    
    df = pd.DataFrame([sample_record])
    # Add a forbidden column
    df["Waste quantity"] = 20.0
    
    with pytest.raises(ValueError, match="leakage guard"):
        detector.predict_anomaly(df)
