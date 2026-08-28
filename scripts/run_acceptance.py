import os
import sys
import pandas as pd
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

def test_acceptance():
    print("========================================")
    print("FIBREOPTIMA FINAL ACCEPTANCE SCENARIO")
    print("========================================\n")
    
    # 1. Initialize DB and Pipeline
    company_db = CompanyDatabase()
    pipeline = FibreOptimaPipeline(company_db=company_db)
    
    # 2. Simulate realistic batch from front-end
    df = pd.DataFrame([
        {
            "Batch ID": "B-FINAL-99",
            "Machine ID": "M03",
            "Fabric type": "Cotton",
            "Operator": "OP03",
            "Shift": "Morning",
            "Production quantity": 1500.0, # M03 capacity is usually ~1000
            "Production speed": 950.0, # Rated is 850
            "Waste quantity": 300.0,   # 20% waste (high)
            "Machine age": 12.0,
            "Last maintenance date": "2026-01-01",
            "Humidity": 40.0,
            "Temperature": 30.0,
        }
    ])
    
    # 3. Process the dataframe (Feature extraction, prediction, OOD, Risk)
    print("Processing Batch...")
    batches, _ = pipeline.process_dataframe(df)
    b = batches[0]
    
    print("\n--- BATCH RESULT METADATA ---")
    print(f"Record ID: {b.record_id}")
    print(f"Machine ID: {b.machine_id}")
    print(f"Predicted Waste: {b.predicted_waste_pct:.2f}%")
    print(f"ML Anomaly Flag: {b.ml_flag}")
    print(f"OOD Flag: {b.is_ood}")
    if b.is_ood:
        print(f"OOD Reasons: {b.ood_reasons}")
    print(f"Risk Level: {b.risk_level}")
    
    # 4. Trigger the full Offline Investigation Engine (DB Context + RAG + Formatting)
    print("\n--- TRIGGERING OFFLINE INVESTIGATION ENGINE ---")
    report = pipeline.investigate_packet(b)
    print(report)

if __name__ == "__main__":
    test_acceptance()
