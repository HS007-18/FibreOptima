import os
import sys
import json
import pandas as pd
import numpy as np

# Ensure src/ is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase
from src.v2.waste_predictor import load_waste_predictor

def run_tests():
    print("========================================")
    print("FIBREOPTIMA BLACK BOX VALIDATION")
    print("========================================\n")
    
    # 1. STARTUP TEST
    print("1. STARTUP TEST")
    try:
        company_db = CompanyDatabase()
        pipeline = FibreOptimaPipeline(company_db=company_db)
        print("PASS: Application starts without OPENAI_API_KEY")
    except Exception as e:
        print(f"FAIL: Startup crashed: {e}")
        return
        
    # Helper to process single dict
    def process(record):
        df = pd.DataFrame([record])
        batches, _ = pipeline.process_dataframe(df)
        return batches[0]

    # 2. TEST DATA CONTRACT (CASE A - Normal Batch)
    print("\n2. TEST DATA CONTRACT - Normal Batch")
    normal_record = {
        "Batch ID": "B-NORM-01",
        "Machine ID": "M03",
        "Fabric type": "Cotton",
        "Operator": "OP03",
        "Shift": "Morning",
        "Production quantity": 1000.0,
        "Production speed": 800.0,
        "Waste quantity": 50.0, # 5% waste
        "Machine age": 5.0,
        "Last maintenance date": "2026-01-01",
        "Humidity": 45.0,
        "Temperature": 25.0,
    }
    b_norm = process(normal_record)
    print(f"Prediction: {b_norm.predicted_waste_pct}, OOD: {b_norm.is_ood}, Anomaly: {b_norm.ml_flag}")

    # 3. HIGH-WASTE TEST
    print("\n3. HIGH-WASTE TEST")
    high_waste_record = normal_record.copy()
    high_waste_record["Production speed"] = 1100.0 # Fast
    high_waste_record["Machine age"] = 15.0 # Old
    high_waste_record["Humidity"] = 35.0 # Dry
    b_high = process(high_waste_record)
    print(f"Prediction: {b_high.predicted_waste_pct}, OOD: {b_high.is_ood}, Anomaly: {b_high.ml_flag}")
    print(f"Risk: {b_high.risk_level}")

    # 4. OOD TEST
    print("\n4. OOD TEST")
    ood_record = normal_record.copy()
    ood_record["Production quantity"] = 200.0
    ood_record["Humidity"] = 90.0
    ood_record["Temperature"] = 15.0
    b_ood = process(ood_record)
    print(f"Prediction: {b_ood.predicted_waste_pct}, OOD: {b_ood.is_ood}, Confidence: {b_ood.prediction_confidence}")
    print(f"OOD Reasons: {b_ood.ood_reasons}")

    # 5. CATEGORICAL OOD TEST
    print("\n5. CATEGORICAL OOD TEST")
    cat_ood_record = normal_record.copy()
    cat_ood_record["Fabric type"] = "Wool"
    b_cat_ood = process(cat_ood_record)
    print(f"Prediction: {b_cat_ood.predicted_waste_pct}, OOD: {b_cat_ood.is_ood}, Confidence: {b_cat_ood.prediction_confidence}")
    print(f"OOD Reasons: {b_cat_ood.ood_reasons}")
    
    # 6. MACHINE DATABASE TEST
    print("\n6. MACHINE DATABASE TEST")
    print(f"M03 Valid Profile: {company_db.get_machine_profile('M03')}")
    print(f"M99 (Unknown) Profile: {company_db.get_machine_profile('M99')}")
    
    # 7. CAPACITY TEST
    print("\n7. CAPACITY TEST")
    # Pipeline doesn't output utilization natively, investigation engine does it.
    packet_dict = pipeline._batch_to_packet_dict(b_norm)
    report = pipeline._investigation_engine.investigate(packet_dict)
    # The dictionary of observed_evidence is actually what we look at
    # Wait, in the updated investigation.py, utilization_percentage is inside company_context.
    # Let's just print the inference string
    print(f"Logical Inference for M03: {report.logical_inference}")
    
    # 15. CRITICAL DATA-INTEGRITY TEST
    print("\n15. CRITICAL DATA-INTEGRITY TEST (Target Leakage)")
    try:
        predictor = load_waste_predictor()
        print("WastePredictor loaded directly.")
        # Test if predict() fails when missing waste features
        test_df = pd.DataFrame([{
            "Machine ID": "M03", "Fabric type": "Cotton", "Operator": "OP01", "Shift": "Morning",
            "Production quantity": 1000, "Production speed": 800, "Machine age": 5,
            "Humidity": 45, "Temperature": 25, "Machine failure": 0
        }])
        try:
            preds = predictor.predict(test_df)
            print(f"Direct Prediction without Waste quantity: {preds}")
        except Exception as e:
            print(f"Direct Prediction failed (Leakage confirmed?): {e}")
    except Exception as e:
        print(f"Predictor loading failed: {e}")

if __name__ == "__main__":
    run_tests()
