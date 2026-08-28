import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

def audit():
    pipeline = FibreOptimaPipeline(enable_rag=False)
    db = CompanyDatabase()
    
    # Simulate the user's test CSV
    data = []
    for i in range(1, 11):
        data.append({
            "Batch ID": f"B10{11-i:02d}",
            "Machine ID": f"M-10{i%5 + 1}",  # M-101 to M-105
            "Fabric type": "Cotton",
            "Operator": "OP01",
            "Shift": "Morning",
            "Production quantity": 1000.0,
            "Production speed": 800.0,
            "Waste quantity": 50.0,
            "Machine age": 5.0,
            "Last maintenance date": "2026-08-01",
            "Humidity": 70.0,
            "Temperature": 30.0,
        })
        
    df = pd.DataFrame(data)
    batches, _ = pipeline.process_dataframe(df)
    
    print("=" * 80)
    print("LIVE DEMO RUNTIME AUDIT (Simulated)")
    print("=" * 80)
    for b in batches:
        print(f"Batch: {b.record_id} | Machine: {b.machine_id} | Pred: {b.predicted_waste_pct:.2f}% | OOD: {b.is_ood} | Risk: {b.risk_level}")
        print(f"  OOD Reasons: {b.ood_reasons}")
        profile = db.get_machine_profile(b.machine_id)
        print(f"  Company DB Profile Found: {bool(profile)}")

if __name__ == "__main__":
    audit()
