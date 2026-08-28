"""Stress testing the FibreOptima Pipeline with edge cases."""

import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import FibreOptimaPipeline

def get_base_record():
    return {
        "Batch ID": "B-STRESS-001",
        "Machine ID": "M03",
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
    }

def build_test_cases():
    cases = []
    
    # 1. Unknown machine ID
    c1 = get_base_record()
    c1["Batch ID"] = "TC01-UnknownMachine"
    c1["Machine ID"] = "M99"
    cases.append(c1)
    
    # 2. Unknown operator
    c2 = get_base_record()
    c2["Batch ID"] = "TC02-UnknownOperator"
    c2["Operator"] = "OP99"
    cases.append(c2)
    
    # 3. Unknown fabric
    c3 = get_base_record()
    c3["Batch ID"] = "TC03-UnknownFabric"
    c3["Fabric type"] = "Kevlar"
    cases.append(c3)
    
    # 4. Missing humidity
    c4 = get_base_record()
    c4["Batch ID"] = "TC04-MissingHumidity"
    c4["Humidity"] = None
    cases.append(c4)
    
    # 5. Null values
    c5 = get_base_record()
    c5["Batch ID"] = "TC05-NullValues"
    c5["Temperature"] = None
    cases.append(c5)
    
    # 6. Zero production
    c6 = get_base_record()
    c6["Batch ID"] = "TC06-ZeroProduction"
    c6["Production quantity"] = 0.0
    cases.append(c6)
    
    # 7. Extremely high production
    c7 = get_base_record()
    c7["Batch ID"] = "TC07-HighProduction"
    c7["Production quantity"] = 500000.0
    cases.append(c7)
    
    # 8. Extremely low production
    c8 = get_base_record()
    c8["Batch ID"] = "TC08-LowProduction"
    c8["Production quantity"] = 1.0
    cases.append(c8)
    
    # 9. High waste + normal ML score
    c9 = get_base_record()
    c9["Batch ID"] = "TC09-HighWaste_NormalML"
    c9["Waste quantity"] = 300.0 # 30% waste
    cases.append(c9)
    
    # 10. Low waste + ML anomaly
    c10 = get_base_record()
    c10["Batch ID"] = "TC10-LowWaste_MLAnomaly"
    c10["Waste quantity"] = 10.0 # 1% waste
    c10["Temperature"] = 80.0 # Extreme temp to trigger anomaly
    c10["Production speed"] = 3500.0
    cases.append(c10)
    
    # 11. OOD + normal waste
    c11 = get_base_record()
    c11["Batch ID"] = "TC11-OOD_NormalWaste"
    c11["Fabric type"] = "Kevlar"
    c11["Waste quantity"] = 50.0
    cases.append(c11)
    
    # 12. OOD + high waste
    c12 = get_base_record()
    c12["Batch ID"] = "TC12-OOD_HighWaste"
    c12["Fabric type"] = "Kevlar"
    c12["Waste quantity"] = 400.0
    cases.append(c12)
    
    # 13. Machine operating above rated capacity
    c13 = get_base_record()
    c13["Batch ID"] = "TC13-AboveCapacity"
    c13["Machine ID"] = "M01" 
    c13["Production speed"] = 1500.0 # M01 rated speed is likely ~800-1000
    cases.append(c13)
    
    # 14. Maintenance overdue
    c14 = get_base_record()
    c14["Batch ID"] = "TC14-MaintenanceOverdue"
    c14["Last maintenance date"] = "2020-01-01"
    cases.append(c14)
    
    # 15. No RAG evidence (Already tested globally by setting enable_rag=False)
    c15 = get_base_record()
    c15["Batch ID"] = "TC15-NoRAGEvidence"
    cases.append(c15)
    
    # 16. Machine with no maintenance history
    c16 = get_base_record()
    c16["Batch ID"] = "TC16-NoMaintenanceHistory"
    c16["Machine ID"] = "M-NEW"
    cases.append(c16)
    
    # 17. Batch with all valid fields
    c17 = get_base_record()
    c17["Batch ID"] = "TC17-AllValid"
    cases.append(c17)
    
    # 18. Multiple simultaneous failures
    c18 = get_base_record()
    c18["Batch ID"] = "TC18-MultipleFailures"
    c18["Machine ID"] = "M99"
    c18["Fabric type"] = "Kevlar"
    c18["Production quantity"] = 0.0
    c18["Humidity"] = 99.0
    c18["Temperature"] = 50.0
    c18["Waste quantity"] = 500.0
    cases.append(c18)

    return cases

def run_stress_test():
    print("=" * 80)
    print(" FIBREOPTIMA STRESS TEST SUITE ")
    print("=" * 80)
    
    # Run with RAG disabled to simulate "No RAG evidence" across the board for speed
    pipeline = FibreOptimaPipeline(enable_ml=True, enable_rag=False)
    cases = build_test_cases()
    
    print(f"{'Test Case':<30} | {'Status':<10} | {'Risk':<10} | {'OOD':<5} | {'Anom':<5} | {'Investigates?':<12}")
    print("-" * 80)
    
    passed = 0
    for case in cases:
        case_id = case["Batch ID"]
        status = "PASS"
        risk = ""
        ood = ""
        anom = ""
        investigates = "Yes"
        
        try:
            batch = pipeline.process_record(case)
            risk = batch.risk_level
            ood = str(batch.is_ood)
            anom = str(batch.is_anomalous)
            
            # Ensure investigation engine can process it
            inv_report = pipeline.investigate_packet_structured(batch)
            if not inv_report or not inv_report.logical_inference:
                investigates = "No (Empty)"
        except Exception as e:
            status = f"FAIL ({type(e).__name__})"
            investigates = "No (Crash)"
            print(f"\n[!] Error in {case_id}: {e}")
            
        print(f"{case_id:<30} | {status:<10} | {risk:<10} | {ood:<5} | {anom:<5} | {investigates:<12}")
        if status == "PASS":
            passed += 1
            
    print("-" * 80)
    print(f"Total: {len(cases)} | Passed: {passed} | Failed: {len(cases) - passed}")
    print("=" * 80)

if __name__ == "__main__":
    run_stress_test()
