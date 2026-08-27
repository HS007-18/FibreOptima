"""Intelligence Packet - Structured contract between Hybrid Engine and Investigation Engine."""

from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict
from src.hybrid.decision_engine import HybridRiskResult


@dataclass
class IntelligencePacket:
    """Structured packet passed from Hybrid Decision Engine to Investigation Engine."""
    
    # Record Identity
    record_id: str
    machine_id: str
    fabric_type: str
    operator: str
    shift: str
    
    # Production Telemetry
    production_quantity: float
    production_speed: float
    waste_quantity: float
    waste_pct: float
    machine_age: float
    days_since_maintenance: int
    humidity: float
    temperature: float
    
    # ML Predictions
    waste_prediction: float
    waste_prediction_error: float
    anomaly_score: float
    is_anomalous: bool
    ml_flag: bool
    
    # V1 Business Rules
    baseline_waste_pct: float
    waste_deviation: float
    waste_z_score: float
    baseline_source: str
    history_count: int
    
    # Risk Signals
    maintenance_signal: bool
    speed_signal: bool
    environment_signal: bool
    machine_age_signal: bool
    limited_history: bool
    
    # Risk Classification
    risk_level: str  # NORMAL, WARNING, HIGH RISK, DATA ISSUE
    risk_class: str  # Normal, Warning, High Risk, Data Issue
    signals: List[str]
    biz_flag: bool
    
    # ML Anomaly Details
    ml_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    investigation_mode: str = "Offline Evidence Engine"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_hybrid_result(cls, record, hybrid_result: 'HybridRiskResult') -> 'IntelligencePacket':
        """Create packet from hybrid risk result and original record."""
        from src.hybrid.decision_engine import HybridRiskResult
        assert isinstance(hybrid_result, HybridRiskResult)
        
        return cls(
            record_id=record.batch_id,
            machine_id=record.machine_id,
            fabric_type=record.fabric_type,
            operator=record.operator,
            shift=record.shift,
            production_quantity=record.production_quantity,
            production_speed=record.production_speed,
            waste_quantity=record.waste_quantity,
            waste_pct=record.waste_pct,
            machine_age=record.machine_age,
            days_since_maintenance=record.days_since_maintenance,
            humidity=record.humidity if record.humidity else 0.0,
            temperature=record.temperature if record.temperature else 0.0,
            waste_prediction=hybrid_result.waste_prediction,
            waste_prediction_error=hybrid_result.waste_prediction_error,
            anomaly_score=hybrid_result.anomaly_score,
            is_anomalous=hybrid_result.is_anomalous,
            ml_flag=hybrid_result.ml_flag,
            baseline_waste_pct=hybrid_result.baseline_waste_pct,
            waste_deviation=hybrid_result.waste_deviation,
            waste_z_score=hybrid_result.waste_z_score,
            baseline_source=record.baseline_source,
            history_count=record.history_count,
            maintenance_signal=hybrid_result.maintenance_signal,
            speed_signal=hybrid_result.speed_signal,
            environment_signal=hybrid_result.environment_signal,
            machine_age_signal=hybrid_result.machine_age_signal,
            limited_history=hybrid_result.limited_history,
            risk_level=hybrid_result.risk_level,
            risk_class=hybrid_result.risk_class,
            signals=hybrid_result.signals,
            biz_flag=hybrid_result.biz_flag,
            ml_contributions={},
        )


# For backwards compatibility with existing code
def create_intelligence_packet(record, hybrid_result) -> dict:
    """Create intelligence packet as dictionary (legacy format)."""
    packet = IntelligencePacket.from_hybrid_result(record, hybrid_result)
    return packet.to_dict()