from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import sys

# Ensure src/ is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

app = FastAPI(title="FibreOptima V3 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate pipeline globally to cache models
company_db = CompanyDatabase()
pipeline = FibreOptimaPipeline(enable_rag=False, company_db=company_db)

# In-memory cache for hackathon demo
_batch_cache = {}

@app.post("/api/process")
async def process_data(file: UploadFile = File(...)):
    """Process a CSV file through the FibreOptima pipeline."""
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    
    # Run the pipeline
    batches, report = pipeline.process_dataframe(df)
    
    # Convert BatchResult objects to dictionaries with native types for JSON serialization
    batch_dicts = []
    _batch_cache.clear() # Clear cache on new upload for demo
    
    for b in batches:
        # Cache for investigation
        _batch_cache[str(b.record_id)] = b
        
        # Get capacity and baseline from company_db to expose to UI
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
        
        batch_dicts.append({
            "record_id": str(b.record_id),
            "machine_id": str(b.machine_id),
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
        
    return {
        "batches": batch_dicts,
        "metrics": {
            "total_batches": len(batches),
            "high_risk": sum(1 for b in batches if b.risk_level == "HIGH RISK"),
            "warnings": sum(1 for b in batches if b.risk_level == "WARNING"),
            "normal": sum(1 for b in batches if b.risk_level == "NORMAL")
        }
    }

@app.get("/api/machines")
async def get_machines():
    """Fetch all machines from Company Database."""
    return company_db.get_all_machines()

@app.get("/api/machines/{machine_id}")
async def get_machine(machine_id: str):
    """Fetch a single machine's details."""
    profile = company_db.get_machine_profile(machine_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found.")
    baseline = company_db.get_machine_baseline(machine_id)
    maintenance = company_db.get_maintenance_history(machine_id)
    return {
        **profile,
        "baseline": baseline,
        "maintenance": maintenance
    }

@app.post("/api/machines")
async def add_machine(payload: dict):
    """Add a new machine to Company Database."""
    if not payload.get("machine_id"):
        raise HTTPException(status_code=400, detail="Machine ID is required.")
    success = company_db.add_machine(payload)
    return {"status": "success" if success else "failed", "machine_id": payload["machine_id"]}

@app.post("/api/predict")
async def predict_single(payload: dict):
    """Predict for a single batch telemetry payload."""
    df = pd.DataFrame([payload])
    batches, report = pipeline.process_dataframe(df)
    if not batches:
        raise HTTPException(status_code=400, detail="Failed to process telemetry batch.")
    
    b = batches[0]
    _batch_cache[str(b.record_id)] = b
    
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
                
    investigation_report = pipeline.investigate_packet(b)
    
    return {
        "record_id": str(b.record_id),
        "machine_id": str(b.machine_id),
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
        "maintenance_status": maint_status,
        "investigation": investigation_report,
        "telemetry": b.observed_telemetry
    }

@app.get("/api/investigate/{record_id}")
async def investigate_batch(record_id: str):
    """Trigger an investigation for a specific batch."""
    if record_id not in _batch_cache:
        raise HTTPException(status_code=404, detail="Batch ID not found in current session.")
        
    packet = _batch_cache[record_id]
    report = pipeline.investigate_packet(packet)
    
    return {
        "record_id": record_id,
        "investigation": report
    }

@app.get("/api/status")
async def get_status():
    """System health status endpoint."""
    return {
        "components": [
            {"name": "ML Waste Model (GBDT)", "status": "Local / Active", "type": "Statistical Model"},
            {"name": "Isolation Forest Anomaly Detector", "status": "Local / Active", "type": "Unsupervised ML"},
            {"name": "OOD Detection Engine", "status": "Local / Active", "type": "Safety Layer"},
            {"name": "Company Database (SQLite)", "status": "Connected", "type": "SQL Fact DB"},
            {"name": "Chroma Vector Database", "status": "Connected", "type": "Knowledge Index"},
            {"name": "HuggingFace Embeddings", "status": "Local / Cached", "type": "Embedding Model"},
            {"name": "Offline Investigation Engine", "status": "Available", "type": "Reasoning Core"},
            {"name": "External LLM", "status": "Optional (Bypassed)", "type": "API Service"}
        ],
        "api_key_required": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
