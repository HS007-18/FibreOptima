import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

db = CompanyDatabase()
pipeline = FibreOptimaPipeline(enable_ml=True, enable_rag=False, company_db=db)

df = pd.read_csv("downloads/test/11_final_demo.csv")
batches, report = pipeline.process_dataframe(df)

results = []
for b in batches:
    rated_capacity = None
    historical_waste_pct = None
    current_production = None
    utilization_percentage = None
    capacity_status = "Unknown"
    
    if b.machine_id:
        profile = db.get_machine_profile(b.machine_id)
        if profile:
            rated_capacity = profile.get("rated_capacity")
        current_production = b.observed_telemetry.get("Production quantity")
        if rated_capacity and current_production and rated_capacity > 0:
            utilization_percentage = (current_production / rated_capacity) * 100
            if utilization_percentage < 80:
                capacity_status = "Under Capacity"
            elif utilization_percentage <= 100:
                capacity_status = "Normal Capacity"
            else:
                capacity_status = "Over Capacity"
                
    results.append({
        "Batch": b.record_id,
        "Machine": b.machine_id,
        "Prediction": f"{b.predicted_waste_pct:.2f}%" if b.predicted_waste_pct is not None else "N/A",
        "Risk": b.risk_level,
        "OOD": b.is_ood,
        "Util": f"{utilization_percentage:.1f}%" if utilization_percentage else "N/A",
        "Cap Status": capacity_status
    })

print(f"{'Batch':<12} | {'Machine':<8} | {'Pred':<8} | {'Risk':<12} | {'OOD':<5} | {'Util':<8} | {'Cap Status'}")
print("-" * 80)
for r in results:
    print(f"{r['Batch']:<12} | {r['Machine']:<8} | {r['Pred']:<8} | {r['Risk']:<12} | {str(r['OOD']):<5} | {r['Util']:<8} | {r['Cap Status']}")
