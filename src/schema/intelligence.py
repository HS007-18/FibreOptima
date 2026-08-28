from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class AnomalyIntelligencePacket:
    """Structured contract between ML/Business logic and Downstream Agent."""

    record_id: str
    is_anomalous: bool
    anomaly_score: float
    business_rule_flag: bool
    ml_anomaly_flag: bool
    risk_class: str
    observed_telemetry: Dict[str, Any]
    statistical_deviations: Dict[str, float]
    feature_contributions: Dict[str, float]
    investigation_mode: str = "Offline Evidence Engine"
    is_ood: bool = False
    ood_reasons: list = field(default_factory=list)
    prediction_confidence: str = "High"
