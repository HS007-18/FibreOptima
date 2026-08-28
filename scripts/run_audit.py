import os
import sys
import pandas as pd
import time
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

def run_audit():
    print("--- 1. Testing Capacity Logic & Waste Units ---")
    company_db = CompanyDatabase()
    pipeline = FibreOptimaPipeline(company_db=company_db)
    
    # Adversarial cases
    df = pd.DataFrame([
        # 1. Normal Machine
        {
            "Batch ID": "B-AUDIT-1",
            "Machine ID": "M03",
            "Fabric type": "Cotton",
            "Operator": "OP03",
            "Shift": "Morning",
            "Production quantity": 600.0,
            "Production speed": 280.0,
            "Waste quantity": 96.0,  # 16% waste
            "Machine age": 12.0,
            "Last maintenance date": "2026-01-01",
            "Humidity": 40.0,
            "Temperature": 30.0,
        },
        # 2. Unknown Machine
        {
            "Batch ID": "B-AUDIT-2",
            "Machine ID": "M99",
            "Fabric type": "Cotton",
            "Operator": "OP03",
            "Shift": "Morning",
            "Production quantity": 600.0,
            "Production speed": 280.0,
            "Waste quantity": 96.0,
            "Machine age": 12.0,
            "Last maintenance date": "2026-01-01",
            "Humidity": 40.0,
            "Temperature": 30.0,
        }
    ])
    
    t0 = time.time()
    batches, _ = pipeline.process_dataframe(df)
    t1 = time.time()
    
    print(f"Pipeline latency for 2 batches: {t1-t0:.4f}s")
    for b in batches:
        print(f"\nBatch: {b.record_id}")
        report = pipeline.investigate_packet(b)
        print("Investigation Report Preview:")
        print("\n".join(report.split("\n")[:15]))
        
if __name__ == "__main__":
    run_audit()
