import os
import pytest
import pandas as pd
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

def test_end_to_end_pipeline():
    # We use an existing machine ID to trigger DB lookup
    df = pd.DataFrame(
        [
            {
                "Batch ID": "B-TEST-01",
                "Machine ID": "M03",
                "Fabric type": "Cotton",
                "Operator": "OP03",
                "Shift": "Morning",
                "Production quantity": 1000.0,
                "Production speed": 280.0,
                "Waste quantity": 160.0,
                "Machine age": 12.0,
                "Last maintenance date": "2026-01-01",
                "Humidity": 40.0,
                "Temperature": 30.0,
            }
        ]
    )

    company_db = CompanyDatabase()
    pipeline = FibreOptimaPipeline(company_db=company_db)
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
    
    # Check if DB context logic kicked in (it might mention baseline or speed)
    # The investigation report is a string representation of InvestigationReport in pipeline.py
    # or the OfflineInvestigationEngine formatting.
    assert "M03" in report
