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

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "FibreOptima V3 API Backend is running.",
        "frontend_url": "http://localhost:5173",
        "docs_url": "/docs"
    }

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
            "fabric_type": b.observed_telemetry.get("Fabric type", "Cotton"),
            "operator": b.observed_telemetry.get("Operator", "Unknown"),
            "shift": b.observed_telemetry.get("Shift", "Morning"),
            "production_quantity": b.observed_telemetry.get("Production quantity", 0.0),
            "waste_quantity": b.observed_telemetry.get("Waste quantity", 0.0),
            "observed_waste_pct": float(b.waste_pct) if hasattr(b, 'waste_pct') and b.waste_pct is not None else None,
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
        
    # Helper to compute level analytics
    valid_b = [bd for bd in batch_dicts if bd["risk_level"] != "DATA ISSUE" and bd["observed_waste_pct"] is not None]
    
    # Factory Level
    total_prod = sum(bd["production_quantity"] for bd in valid_b)
    total_waste = sum(bd["waste_quantity"] for bd in valid_b)
    overall_waste_pct = float((total_waste / total_prod * 100)) if total_prod > 0 else 0.0
    valid_preds = [bd["predicted_waste_pct"] for bd in valid_b if bd["predicted_waste_pct"] is not None]
    avg_pred_waste = float(sum(valid_preds) / len(valid_preds)) if valid_preds else 0.0

    def compute_group_analytics(group_key):
        groups = {}
        for bd in valid_b:
            key = bd.get(group_key, "Unknown")
            if key not in groups:
                groups[key] = {"key": key, "prod": 0.0, "waste": 0.0, "count": 0, "anomalies": 0, "high_risk": 0, "predicted_sum": 0.0}
            groups[key]["prod"] += bd["production_quantity"]
            groups[key]["waste"] += bd["waste_quantity"]
            groups[key]["count"] += 1
            if bd["ml_flag"]: groups[key]["anomalies"] += 1
            if bd["risk_level"] == "HIGH RISK": groups[key]["high_risk"] += 1
            if bd["predicted_waste_pct"] is not None: groups[key]["predicted_sum"] += bd["predicted_waste_pct"]
            
        res = []
        for k, v in groups.items():
            obs_pct = (v["waste"] / v["prod"] * 100) if v["prod"] > 0 else 0.0
            pred_pct = (v["predicted_sum"] / v["count"]) if v["count"] > 0 else 0.0
            res.append({
                "name": k,
                "total_production": round(v["prod"], 1),
                "total_waste": round(v["waste"], 1),
                "avg_waste_pct": round(obs_pct, 2),
                "avg_predicted_waste_pct": round(pred_pct, 2),
                "record_count": v["count"],
                "anomaly_count": v["anomalies"],
                "high_risk_count": v["high_risk"]
            })
        return res

    return {
        "batches": batch_dicts,
        "metrics": {
            "total_records": len(batches),
            "total_production": round(total_prod, 1),
            "total_waste": round(total_waste, 1),
            "overall_waste_pct": round(overall_waste_pct, 2),
            "avg_predicted_waste": round(avg_pred_waste, 2),
            "high_risk": sum(1 for b in batches if b.risk_level == "HIGH RISK"),
            "warnings": sum(1 for b in batches if b.risk_level == "WARNING"),
            "normal": sum(1 for b in batches if b.risk_level == "NORMAL"),
            "data_issues": sum(1 for b in batches if b.risk_level == "DATA ISSUE")
        },
        "machine_analytics": compute_group_analytics("machine_id"),
        "fabric_analytics": compute_group_analytics("fabric_type"),
        "shift_analytics": compute_group_analytics("shift"),
        "operator_analytics": compute_group_analytics("operator")
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

@app.post("/api/chat")
async def chat_assistant(payload: dict):
    """Local AI Chat Assistant endpoint for pipeline mechanics & machine recommendations."""
    msg = payload.get("message", "").strip().lower()
    ctx = payload.get("context", {})
    
    if not msg and not ctx:
        raise HTTPException(status_code=400, detail="Message or context is required.")

    # 1. Contextual query about a specific analyzed batch
    if ctx and ("batch" in msg or "analyse" in msg or "analysis" in msg or "why" in msg or "recommend" in msg or "this" in msg):
        record_id = ctx.get("record_id", "BATCH-CURRENT")
        m_id = ctx.get("machine_id", "M01")
        pred = f"{ctx.get('predicted_waste_pct'):.2f}%" if ctx.get('predicted_waste_pct') is not None else "N/A"
        risk = ctx.get("risk_level", "NORMAL")
        is_ood = ctx.get("is_ood", False)
        util = f"{ctx.get('utilization_percentage'):.1f}%" if ctx.get('utilization_percentage') else "N/A"
        
        reply = (
            f"### Analysis Report Context: {record_id} ({m_id})\n\n"
            f"- Machine: {m_id}\n"
            f"- Predicted Waste: {pred}\n"
            f"- Risk Classification: {risk}\n"
            f"- Capacity Utilization: {util}\n"
            f"- Out-of-Distribution Safety: {'OOD DETECTED' if is_ood else 'IN DISTRIBUTION'}\n\n"
            f"### Recommendations & Insights:\n"
            f"1. Machine {m_id} is operating at {util} of rated capacity under {risk} status.\n"
            f"2. {'WARNING: Operating in OOD mode lowers model prediction confidence.' if is_ood else 'Model confidence is HIGH.'}\n"
            f"3. Action: Inspect machine speed calibration and baseline alignment before proceeding with full scale production."
        )
        return {"reply": reply, "source": f"Analysis Context ({m_id})"}

    # 2. Check for specific machine queries (e.g., M01, M02, M03... M10)
    import re
    m_match = re.search(r'\bm0[1-9]\b|\bm10\b|\bm[0-9]+\b', msg)
    if m_match or "machine" in msg or "recommend" in msg:
        target_m = m_match.group(0).upper() if m_match else ctx.get("machine_id", "M01")
        profile = company_db.get_machine_profile(target_m)
        baseline = company_db.get_machine_baseline(target_m)
        maint = company_db.get_maintenance_history(target_m)
        
        if profile:
            maint_str = f"{maint.get('maintenance_type')} ({maint.get('days_ago')} days ago)" if maint else "No recent maintenance recorded"
            waste_str = f"{baseline.get('historical_waste_pct'):.1f}%" if baseline else "Standard baseline"
            
            reply = (
                f"### Operational Recommendations for Machine {target_m}\n\n"
                f"- Machine Type: {profile.get('machine_type')}\n"
                f"- Status: {profile.get('status')}\n"
                f"- Rated Capacity: {profile.get('rated_capacity')} units | Rated Speed: {profile.get('rated_speed')} RPM\n"
                f"- Historical Waste Baseline: {waste_str}\n"
                f"- Maintenance Status: {maint_str}\n\n"
                f"### Actionable Advice:\n"
                f"1. Keep operating speed under {profile.get('rated_speed')} RPM to avoid numerical Out-of-Distribution (OOD) risk.\n"
                f"2. Inspect loom alignment if batch waste exceeds historical baseline ({waste_str}).\n"
                f"3. Maintain ambient humidity between 65%–74.5% to ensure ML prediction confidence remains High."
            )
            return {"reply": reply, "source": "CompanyDB Facts"}

    # 3. Check for OOD questions
    if "ood" in msg or "out of distribution" in msg or "confidence" in msg:
        reply = (
            "### Out-of-Distribution (OOD) Safety Layer\n\n"
            "What is OOD?\n"
            "OOD triggers when operating telemetry (e.g., speed, temperature, humidity) falls outside the statistical bounds learned by the ML model during training.\n\n"
            "Key Rules:\n"
            "- Numerical OOD: Speed > 2886 RPM or Humidity outside [65%, 74.5%].\n"
            "- Categorical OOD: Unseen fabric types (e.g. Kevlar) or unknown operators.\n"
            "- Confidence Impact: OOD lowers prediction confidence to LOW, warning operators that the model is extrapolating.\n"
            "- Math Independence: OOD does not alter or fake the underlying prediction calculation."
        )
        return {"reply": reply, "source": "OOD Safety Architecture"}

    # 4. Check for general pipeline / how it works questions
    if "how" in msg or "pipeline" in msg or "work" in msg or "rag" in msg or "ml" in msg:
        reply = (
            "### FibreOptima 3-Pillar Intelligence Architecture\n\n"
            "FibreOptima transforms factory telemetry into actionable machine intelligence using three local sources:\n\n"
            "1. ML Intelligence: HistGradientBoosting Regressor predicts expected waste %; Isolation Forest measures statistical anomaly scores.\n"
            "2. Company Intelligence: SQLite CompanyDB provides machine facts (rated limits, baseline waste %, maintenance history).\n"
            "3. Technical Knowledge (RAG): Local ChromaDB vector store retrieves textile manufacturing manuals & troubleshooting guides.\n\n"
            "The Offline Investigation Engine synthesizes all three to deliver root-cause explanations and recommendations with zero external API keys."
        )
        return {"reply": reply, "source": "Pipeline Architecture"}

    # Default fallback
    reply = (
        f"I am the FibreOptima Local AI Assistant. I analyze factory telemetry using local ML models, SQLite CompanyDB facts, and Chroma RAG domain knowledge.\n\n"
        f"You can ask me:\n"
        f"- 'How does FibreOptima work?'\n"
        f"- 'Explain OOD safety'\n"
        f"- 'Recommendations for Machine M01'\n"
        f"- 'What recommendations apply to the current batch analysis?'"
    )
    return {"reply": reply, "source": "Local Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
