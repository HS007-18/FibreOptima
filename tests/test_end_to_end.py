import os
import pytest
import pandas as pd
from src.pipeline import FibreOptimaPipeline


def test_end_to_end_pipeline():
    # Setup test telemetry
    df = pd.DataFrame(
        [
            {
                "Batch ID": "B-TEST-01",
                "Machine ID": "M-01",
                "Fabric type": "Cotton",
                "Operator": "Op-1",
                "Shift": "Morning",
                "Production quantity": 1000.0,
                "Production speed": 280.0,  # High speed > 250
                "Waste quantity": 160.0,   # Waste % = 16% > 15% (biz_flag)
                "Machine age": 12.0,       # Old machine > 10
                "Last maintenance date": "2026-01-01",
                "Humidity": 40.0,          # Low humidity
                "Temperature": 30.0,
            }
        ]
    )

    pipeline = FibreOptimaPipeline()
    packets, _ = pipeline.process_dataframe(df)

    assert len(packets) == 1
    packet = packets[0]

    assert packet.record_id == "B-TEST-01"
    assert packet.business_rule_flag is True
    assert packet.observed_telemetry["Waste percentage"] == 16.0

    # Test Layer 5 Agent investigation
    report = pipeline.investigate_packet(packet)
    assert "Investigation Mode:" in report
    assert "OBSERVED EVIDENCE" in report
    assert "LOGICAL INFERENCE" in report
