import io
import pandas as pd
import traceback
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

try:
    company_db = CompanyDatabase()
    pipeline = FibreOptimaPipeline(enable_ml=True, enable_rag=False, company_db=company_db)
    
    df = pd.read_csv('downloads/test/01_factory_standard_baseline.csv')
    batches, report = pipeline.process_dataframe(df)
    
    batch_dicts = []
    for b in batches:
        rated_capacity = None
        historical_waste_pct = None
        current_production = None
        utilization_percentage = None
        capacity_status = "Unknown"
        maint_status = "Unknown"
        
        if b.machine_id:
            profile = company_db.get_machine_profile(b.machine_id)
            baseline = company_db.get_machine_baseline(b.machine_id)
            maint = company_db.get_maintenance_history(b.machine_id)
            if profile:
                rated_capacity = profile.get("rated_capacity")
            if baseline:
                historical_waste_pct = baseline.get("historical_waste_pct")
            if maint:
                maint_status = f"{maint.get('maintenance_type')} ({maint.get('days_ago')} days ago)"
            
            current_production = b.observed_telemetry.get("Production quantity")
            if rated_capacity and current_production and rated_capacity > 0:
                utilization_percentage = (current_production / rated_capacity) * 100
                if utilization_percentage < 80:
                    capacity_status = "Under Capacity"
                elif utilization_percentage <= 100:
                    capacity_status = "Normal Capacity"
                else:
                    capacity_status = "Over Capacity"
        
        obs_pct = float(b.observed_waste_pct) if hasattr(b, 'observed_waste_pct') and b.observed_waste_pct is not None else (float(b.waste_pct) if hasattr(b, 'waste_pct') else None)

        batch_dicts.append({
            "record_id": str(b.record_id),
            "machine_id": str(b.machine_id),
            "fabric_type": b.observed_telemetry.get("Fabric type", "Cotton"),
            "operator": b.observed_telemetry.get("Operator", "Unknown"),
            "shift": b.observed_telemetry.get("Shift", "Morning"),
            "production_quantity": b.observed_telemetry.get("Production quantity", 0.0),
            "waste_quantity": b.observed_telemetry.get("Waste quantity", 0.0),
            "observed_waste_pct": obs_pct,
            "predicted_waste_pct": float(b.predicted_waste_pct) if b.predicted_waste_pct is not None else None,
            "anomaly_score": float(b.anomaly_score) if b.anomaly_score is not None else None,
            "ml_flag": bool(b.ml_flag),
            "risk_level": str(b.risk_level),
            "is_ood": bool(b.is_ood) if hasattr(b, 'is_ood') else False,
            "ood_reasons": b.ood_reasons if hasattr(b, 'ood_reasons') else [],
            "prediction_confidence": b.prediction_confidence if hasattr(b, 'prediction_confidence') else "Unknown",
            "rated_capacity": rated_capacity,
            "current_production": current_production,
            "utilization_percentage": utilization_percentage,
            "capacity_status": capacity_status,
            "historical_waste_pct": historical_waste_pct,
            "maintenance_status": maint_status
        })

    valid_b = [bd for bd in batch_dicts if bd["risk_level"] != "DATA ISSUE" and bd["observed_waste_pct"] is not None]
    
    total_prod = sum(bd["production_quantity"] for bd in valid_b)
    total_waste = sum(bd["waste_quantity"] for bd in valid_b)
    overall_waste_pct = float((total_waste / total_prod * 100)) if total_prod > 0 else 0.0
    valid_preds = [bd["predicted_waste_pct"] for bd in valid_b if bd["predicted_waste_pct"] is not None]
    avg_pred_waste = float(sum(valid_preds) / len(valid_preds)) if valid_preds else 0.0

    print("Success! Processed", len(batch_dicts), "batches.")
except Exception as e:
    traceback.print_exc()
