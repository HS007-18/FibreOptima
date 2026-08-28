import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

def run_tests():
    db = CompanyDatabase()
    pipeline = FibreOptimaPipeline(enable_ml=True, enable_rag=False, company_db=db)
    
    # Generate base valid record
    base_record = {
        "Batch ID": "B-TEST-001",
        "Machine ID": "M01",
        "Fabric type": "Cotton",
        "Operator": "OP01",
        "Shift": "Morning",
        "Production quantity": 1200.0,
        "Production speed": 800.0,
        "Waste quantity": 20.0,
        "Machine age": 5.0,
        "Humidity": 50.0,
        "Temperature": 25.0
    }
    
    scenarios = [
        ("Known machine", base_record),
        ("Unknown machine", {**base_record, "Machine ID": "M-101", "Batch ID": "B-TEST-002"}),
        ("Unknown operator", {**base_record, "Operator": "OP99", "Batch ID": "B-TEST-003"}),
        ("Unknown fabric", {**base_record, "Fabric type": "Kevlar", "Batch ID": "B-TEST-004"}),
        ("Known machine + numerical OOD", {**base_record, "Production speed": 9999.0, "Batch ID": "B-TEST-005"}),
        ("Known machine + high waste", {**base_record, "Waste quantity": 500.0, "Batch ID": "B-TEST-006"}),
        ("Zero production", {**base_record, "Production quantity": 0.0, "Waste quantity": 0.0, "Batch ID": "B-TEST-007"}),
        ("Multiple simultaneous failures", {**base_record, "Machine ID": "M-999", "Production quantity": 0.0, "Batch ID": "B-TEST-008"}),
    ]
    
    print(f"{'Scenario':<35} | {'Risk':<12} | {'Waste Pred':<10} | {'OOD':<5} | {'Reason / Quality Issue'}")
    print("-" * 100)
    
    for name, data in scenarios:
        try:
            batch = pipeline.process_record(data)
            pred = f"{batch.predicted_waste_pct:.2f}%" if batch.predicted_waste_pct is not None else "N/A"
            reason = batch.data_quality_reason if not batch.is_valid else " / ".join(batch.ood_reasons)
            print(f"{name:<35} | {batch.risk_level:<12} | {pred:<10} | {str(batch.is_ood):<5} | {reason}")
        except Exception as e:
            print(f"{name:<35} | ERROR: {str(e)}")

if __name__ == "__main__":
    run_tests()
