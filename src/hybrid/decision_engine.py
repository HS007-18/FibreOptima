"""Hybrid Decision Engine - Combines V1 Business Rules with ML Predictions.

This is the core intelligence layer that combines:
1. V1 Statistical Baselines & Business Rules
2. ML Waste Prediction
3. ML Anomaly Detection
Into a unified risk assessment.
"""

import pandas as pd
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.models.schemas import BatchRecord
from src.legacy_v1.risk.risk_engine import (
    evaluate_maintenance_signal,
    evaluate_speed_signal,
    evaluate_environment_signal,
    evaluate_machine_age_signal,
)
from src.legacy_v1.models.schemas import BaselineResult
from src.v2.waste_predictor import WastePredictor
from src.v2.anomaly_detector import AnomalyDetector


@dataclass
class HybridRiskResult:
    """Unified risk assessment result."""
    risk_level: str  # NORMAL, WARNING, HIGH RISK, DATA ISSUE
    waste_prediction: float  # ML predicted waste %
    actual_waste_pct: float  # Actual calculated waste %
    baseline_waste_pct: float  # Historical baseline
    waste_deviation: float  # Actual - baseline
    waste_z_score: float  # Z-score from baseline
    anomaly_score: float  # ML anomaly score
    is_anomalous: bool  # ML anomaly flag
    ml_flag: bool  # ML anomaly flag (alias)
    biz_flag: bool  # Business rule flag
    maintenance_signal: bool
    speed_signal: bool
    environment_signal: bool
    machine_age_signal: bool
    limited_history: bool
    risk_class: str  # Normal, Warning, High Risk
    signals: List[str]  # Active signal names
    waste_prediction_error: float  # |predicted - actual|


class HybridDecisionEngine:
    """Combines V1 statistical rules with ML predictions for unified risk assessment."""
    
    def __init__(self):
        self.waste_predictor = None
        self.anomaly_detector = None
        self._init_models()
    
    def _init_models(self):
        """Initialize ML models."""
        try:
            from src.v2.waste_predictor import WastePredictor
            self.waste_predictor = WastePredictor()
        except Exception as e:
            print(f"Warning: Waste predictor not available: {e}")
            self.waste_predictor = None
        
        try:
            from src.v2.anomaly_detector import AnomalyDetector
            self.anomaly_detector = AnomalyDetector()
        except Exception as e:
            print(f"Warning: Anomaly detector not available: {e}")
            self.anomaly_detector = None
    
    def assess_risk(self, record: BatchRecord, reference_df: pd.DataFrame = None) -> HybridRiskResult:
        """Assess risk using hybrid approach: V1 rules + ML predictions."""
        
        # 1. Handle DATA ISSUE cases first
        if not record.is_valid or record.zero_production:
            return HybridRiskResult(
                risk_level="DATA ISSUE",
                waste_prediction=0.0,
                actual_waste_pct=record.waste_pct,
                baseline_waste_pct=0.0,
                waste_deviation=0.0,
                waste_z_score=0.0,
                anomaly_score=0.0,
                is_anomalous=False,
                ml_flag=False,
                biz_flag=False,
                maintenance_signal=False,
                speed_signal=False,
                environment_signal=False,
                machine_age_signal=False,
                limited_history=record.limited_history,
                risk_class="DATA ISSUE",
                signals=["data_issue"],
                waste_prediction_error=0.0,
            )
        
        # 2. Get ML Waste Prediction
        waste_prediction = 0.0
        waste_prediction_error = 0.0
        if self.waste_predictor:
            try:
                # Create feature dict for prediction
                record_dict = {
                    "Machine ID": record.machine_id,
                    "Fabric type": record.fabric_type,
                    "Operator": record.operator,
                    "Shift": record.shift,
                    "Production quantity": record.production_quantity,
                    "Production speed": record.production_speed,
                    "Machine age": record.machine_age,
                    "Humidity": record.humidity if record.humidity else 0.0,
                    "Temperature": record.temperature if record.temperature else 0.0,
                    "Machine failure": 0,  # Default
                }
                waste_prediction = self.waste_predictor.predict_single(record_dict)
                waste_prediction_error = abs(waste_prediction - record.waste_pct)
            except Exception as e:
                print(f"Warning: Waste prediction failed: {e}")
                waste_prediction = record.waste_pct  # Fallback to actual
        
        # 3. Get ML Anomaly Detection
        anomaly_score = 0.0
        is_anomalous = False
        ml_contributions = {}
        ml_z_scores = {}
        if self.anomaly_detector:
            try:
                # Create DataFrame for anomaly detector
                import pandas as pd
                df = pd.DataFrame([{
                    "Batch ID": record.batch_id,
                    "Machine ID": record.machine_id,
                    "Fabric type": record.fabric_type,
                    "Operator": record.operator,
                    "Shift": record.shift,
                    "Production quantity": record.production_quantity,
                    "Production speed": record.production_speed,
                    "Waste quantity": record.waste_quantity,
                    "Machine age": record.machine_age,
                    "Last maintenance date": record.last_maintenance_date,
                    "Humidity": record.humidity if record.humidity else 0.0,
                    "Temperature": record.temperature if record.temperature else 0.0,
                }])
                anomaly_result = self.anomaly_detector.predict_anomaly(pd.DataFrame([{
                    "Batch ID": record.batch_id,
                    "Machine ID": record.machine_id,
                    "Fabric type": record.fabric_type,
                    "Operator": record.operator,
                    "Shift": record.shift,
                    "Production quantity": record.production_quantity,
                    "Production speed": record.production_speed,
                    "Waste quantity": record.waste_quantity,
                    "Machine age": record.machine_age,
                    "Last maintenance date": record.last_maintenance_date,
                    "Humidity": record.humidity if record.humidity else 0.0,
                    "Temperature": record.temperature if record.temperature else 0.0,
                }]))
                anomaly_score = anomaly_result.get("anomaly_score", 0.0)
                is_anomalous = anomaly_result.get("is_anomalous", False)
                ml_contributions = anomaly_result.get("feature_contributions", {})
            except Exception as e:
                print(f"Warning: Anomaly detection failed: {e}")
        
        # 4. V1 Business Rule Signals
        maintenance_signal = evaluate_maintenance_signal(record)
        speed_signal = evaluate_speed_signal(record)
        environment_signal = evaluate_environment_signal(record, reference_df=None)
        machine_age_signal = record.machine_age > SETTINGS.MACHINE_AGE_WARNING_YEARS
        
        # 5. Baseline & Z-Score (from V1)
        baseline_waste_pct = record.baseline_waste_pct
        waste_deviation = record.waste_deviation
        waste_z_score = record.waste_z_score if record.waste_z_score is not None else 0.0
        
        # 6. Collect Active Signals
        signals = []
        if record.waste_z_score is not None and record.waste_z_score >= SETTINGS.HIGH_RISK_Z_THRESHOLD:
            signals.append("high_waste_deviation")
        elif record.waste_z_score is not None and record.waste_z_score >= SETTINGS.WARNING_Z_THRESHOLD:
            signals.append("moderate_waste_deviation")
        
        if maintenance_signal:
            signals.append("maintenance_overdue")
        if speed_signal:
            signals.append("abnormal_speed")
        if environment_signal:
            signals.append("environment_deviation")
        if machine_age_signal:
            signals.append("machine_age_warning")
        if record.limited_history:
            signals.append("limited_history")
        
        # 7. ML Flags
        ml_flag = is_anomalous if 'is_anomalous' in locals() else False
        biz_flag = any([maintenance_signal, speed_signal, environment_signal, machine_age_signal])
        
        # 8. Determine Risk Level (Hybrid Logic)
        risk_level = self._determine_risk_level(
            waste_z_score=waste_z_score if record.waste_z_score is not None else 0.0,
            signals=signals,
            ml_flag=ml_flag,
            anomaly_score=anomaly_score,
            record=record,
        )
        
        # Risk class mapping
        risk_class_map = {
            "NORMAL": "Normal",
            "WARNING": "Warning",
            "HIGH RISK": "High Risk",
            "DATA ISSUE": "Data Issue",
        }
        risk_class = risk_class_map.get(risk_level, "Unknown")
        
        return HybridRiskResult(
            risk_level=risk_level,
            waste_prediction=waste_prediction,
            actual_waste_pct=record.waste_pct,
            baseline_waste_pct=baseline_waste_pct,
            waste_deviation=waste_deviation,
            waste_z_score=waste_z_score,
            anomaly_score=anomaly_score,
            is_anomalous=is_anomalous,
            ml_flag=ml_flag,
            biz_flag=biz_flag,
            maintenance_signal=maintenance_signal,
            speed_signal=speed_signal,
            environment_signal=environment_signal,
            machine_age_signal=machine_age_signal,
            limited_history=record.limited_history,
            risk_class=risk_class,
            signals=signals,
            waste_prediction_error=waste_prediction_error,
        )
    
    def _determine_risk_level(self, waste_z_score: float, signals: List[str], 
                              ml_flag: bool, anomaly_score: float, record: BatchRecord) -> str:
        """Determine final risk level using hybrid logic."""
        
        # DATA ISSUE already handled
        
        # HIGH RISK conditions (any one true):
        # 1. Strong waste deviation (z >= 2.5)
        if waste_z_score >= SETTINGS.HIGH_RISK_Z_THRESHOLD:
            return "HIGH RISK"
        
        # 2. Moderate waste deviation (1.5 <= z < 2.5) + any supporting signal
        if waste_z_score >= SETTINGS.WARNING_Z_THRESHOLD:
            if len([s for s in signals if s != "limited_history"]) >= 1:
                return "HIGH RISK"
            return "WARNING"
        
        # 3. ML anomaly flag + any supporting signal
        if ml_flag and len([s for s in signals if s != "limited_history"]) >= 1:
            return "HIGH RISK"
        
        # 4. ML anomaly alone
        if ml_flag:
            return "WARNING"
        
        # 5. Waste in normal range but supporting signals
        if len([s for s in signals if s != "limited_history"]) >= 2:
            return "WARNING"
        elif len([s for s in signals if s != "limited_history"]) >= 1:
            return "WARNING"
        
        # 6. Limited history alone
        if record.limited_history:
            return "WARNING"
        
        return "NORMAL"


def create_hybrid_engine():
    """Factory function to create hybrid decision engine."""
    return HybridDecisionEngine()