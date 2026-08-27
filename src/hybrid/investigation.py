"""Offline Investigation Engine - Deterministic Evidence-Based Investigation.

This engine produces human-readable investigations without requiring an LLM API.
It uses deterministic rules based on ML signals, business rules, and RAG evidence.
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from src.hybrid.intelligence_packet import IntelligencePacket
# RAG is imported dynamically if enabled to avoid heavy ML dependencies


@dataclass
class InvestigationReport:
    """Structured investigation report."""
    investigation_mode: str
    record_id: str
    risk_level: str
    risk_class: str
    observed_evidence: Dict[str, Any]
    ml_evidence: Dict[str, Any]
    retrieved_knowledge: List[Dict[str, Any]]
    logical_inference: List[str]
    recommended_actions: List[str]
    confidence: float


class OfflineInvestigationEngine:
    """Deterministic investigation engine using evidence-based reasoning."""
    
    def __init__(self, rag_indexer: Optional[object] = None):
        self.rag_indexer = rag_indexer
        self.knowledge_base = self._load_domain_knowledge()
    
    def investigate(self, packet) -> InvestigationReport:
        """Run full investigation on intelligence packet."""
        # Handle both IntelligencePacket objects and dicts
        if isinstance(packet, dict):
            packet_dict = packet
        else:
            packet_dict = packet.to_dict() if hasattr(packet, 'to_dict') else packet.__dict__
        
        # 1. Observed Evidence
        observed_evidence = self._extract_observed_evidence(packet_dict)
        
        # 2. ML & Operational Evidence
        ml_evidence = self._extract_ml_evidence(packet_dict)
        
        # 3. Retrieve Domain Knowledge (RAG)
        retrieved_knowledge = self._retrieve_evidence(packet_dict)
        
        # 4. Logical Inference
        logical_inference = self._generate_inference(packet_dict, retrieved_knowledge)
        
        # 5. Recommended Actions
        recommended_actions = self._generate_actions(packet_dict, retrieved_knowledge)
        
        # 6. Confidence Score
        confidence = self._calculate_confidence(packet_dict, retrieved_knowledge)
        
        return InvestigationReport(
            investigation_mode="Offline Evidence Engine",
            record_id=packet_dict.get("record_id", "UNKNOWN"),
            risk_level=packet_dict.get("risk_level", "UNKNOWN"),
            risk_class=packet_dict.get("risk_class", "UNKNOWN"),
            observed_evidence=observed_evidence,
            ml_evidence=ml_evidence,
            retrieved_knowledge=retrieved_knowledge,
            logical_inference=logical_inference,
            recommended_actions=recommended_actions,
            confidence=confidence,
        )
    
    def _extract_observed_evidence(self, packet: dict) -> Dict[str, Any]:
        """Extract observed telemetry from packet."""
        return {
            "record_id": packet.get("record_id", "UNKNOWN"),
            "waste_percentage": round(packet.get("waste_pct", 0), 2),
            "waste_quantity": round(packet.get("waste_quantity", 0), 2),
            "production_quantity": packet.get("production_quantity", 0),
            "production_speed": packet.get("production_speed", 0),
            "machine_id": packet.get("machine_id", "UNKNOWN"),
            "fabric_type": packet.get("fabric_type", "UNKNOWN"),
            "operator": packet.get("operator", "UNKNOWN"),
            "shift": packet.get("shift", "UNKNOWN"),
            "machine_age": packet.get("machine_age", 0),
            "days_since_maintenance": packet.get("days_since_maintenance", 0),
            "humidity": packet.get("humidity"),
            "temperature": packet.get("temperature"),
            "waste_prediction": round(packet.get("waste_prediction", 0), 2),
            "waste_prediction_error": round(packet.get("waste_prediction_error", 0), 4),
        }
    
    def _extract_ml_evidence(self, packet: dict) -> Dict[str, Any]:
        """Extract ML and operational evidence."""
        return {
            "risk_level": packet.get("risk_level", "UNKNOWN"),
            "risk_class": packet.get("risk_class", "UNKNOWN"),
            "anomaly_score": round(packet.get("anomaly_score", 0), 4),
            "is_anomalous": packet.get("is_anomalous", False),
            "ml_flag": packet.get("ml_flag", False),
            "waste_prediction": round(packet.get("waste_prediction", 0), 2),
            "waste_prediction_error": round(packet.get("waste_prediction_error", 0), 4),
            "actual_waste_pct": round(packet.get("waste_pct", 0), 2),
            "baseline_waste_pct": round(packet.get("baseline_waste_pct", 0), 2),
            "waste_deviation": round(packet.get("waste_deviation", 0), 2),
            "waste_z_score": packet.get("waste_z_score"),
            "baseline_source": packet.get("baseline_source"),
            "history_count": packet.get("history_count", 0),
            "signals": packet.get("signals", []),
            "maintenance_signal": packet.get("maintenance_signal", False),
            "speed_signal": packet.get("speed_signal", False),
            "environment_signal": packet.get("environment_signal", False),
            "machine_age_signal": packet.get("machine_age_signal", False),
            "limited_history": packet.get("limited_history", False),
            "ml_flag": packet.get("ml_flag", False),
            "biz_flag": packet.get("biz_flag", False),
            "waste_z_score": packet.get("waste_z_score"),
            "anomaly_score": packet.get("anomaly_score"),
        }
    
    def _retrieve_evidence(self, packet: dict) -> List[Dict[str, Any]]:
        """Retrieve relevant domain knowledge from RAG."""
        evidence = []
        
        if self.rag_indexer:
            try:
                # Generate queries based on packet signals
                queries = self._generate_queries(packet)
                
                for query in queries[:3]:  # Limit queries
                    try:
                        docs = self.rag_indexer.vector_store.similarity_search(query, k=2)
                        for doc in docs:
                            evidence.append({
                                "source": doc.metadata.get("Source", "Textile Mill Handbook"),
                                "topic": doc.metadata.get("Topic", "General"),
                                "content": doc.page_content[:500],  # Truncate
                            })
                    except Exception as e:
                        pass  # Silently fail retrieval
            except Exception:
                pass
        
        # Fallback to built-in knowledge base
        if not evidence:
            evidence = self._get_fallback_evidence(packet)
        
        return evidence
    
    def _generate_queries(self, packet: dict) -> List[str]:
        """Generate retrieval queries based on packet signals."""
        queries = []
        
        fabric = packet.get("fabric_type", "Textile")
        waste_pct = packet.get("waste_pct", 0)
        machine_age = packet.get("machine_age", 0)
        
        # Base query
        queries.append(f"{fabric} waste percentage abnormal production speed")
        
        # Signal-specific queries
        if packet.get("maintenance_signal"):
            queries.append("machine maintenance overdue waste percentage increase")
        
        if packet.get("speed_signal"):
            queries.append("high production speed rpm vibration waste textile")
        
        if packet.get("environment_signal"):
            queries.append("humidity temperature textile waste quality")
        
        if packet.get("machine_age_signal"):
            queries.append(f"machine age {int(machine_age)} years wear waste production")
        
        if packet.get("limited_history"):
            queries.append("new machine limited historical baseline waste")
        
        if waste_pct > 15:
            queries.append("high waste percentage loom inspection threshold")
        
        return queries[:4]  # Limit queries
    
    def _get_fallback_evidence(self, packet: dict) -> List[Dict[str, Any]]:
        """Provide deterministic fallback evidence when RAG unavailable."""
        evidence = []
        
        # Always include general textile maintenance guidance
        evidence.append({
            "source": "Textile Manufacturing Handbook",
            "topic": "General Waste Reduction",
            "content": "Waste percentage above 15% typically indicates mechanical issues, speed miscalibration, or environmental control failures. Verify loom calibration, check humidity sensors, and inspect mechanical wear."
        })
        
        # Signal-specific evidence
        if packet.get("maintenance_signal"):
            evidence.append({
                "source": "Industrial Maintenance Manual",
                "topic": "Overdue Maintenance Impact",
                "content": "Machines overdue for maintenance by 30+ days show 15-40% increase in material waste due to misalignment, vibration, and timing drift. Schedule immediate inspection."
            })
        
        if packet.get("speed_signal"):
            evidence.append({
                "source": "Loom Operation Manual",
                "topic": "Speed-Related Waste",
                "content": "Production speed exceeding 250 RPM increases yarn breakage and fabric defects. Optimal speed varies by fabric type - Cotton: 200-220, Polyester: 220-240, Silk: 180-200."
            })
        
        if packet.get("environment_signal"):
            evidence.append({
                "source": "Environmental Control Guidelines",
                "topic": "Humidity/Temperature Effects",
                "content": "Cotton requires 60-70% humidity; below 55% causes static and breakage. Polyester tolerant 50-75%. Temperature >28°C accelerates fiber degradation."
            })
        
        if packet.get("limited_history"):
            evidence.append({
                "source": "Statistical Process Control Guide",
                "topic": "New Machine Baseline",
                "content": "Machines with <8 historical batches use fabric-level baseline. Expect higher uncertainty. Collect minimum 8 batches before establishing machine-specific baseline."
            })
        
        return evidence
    
    def _generate_inference(self, packet: dict, evidence: List[Dict]) -> List[str]:
        """Generate logical inference from evidence."""
        inferences = []
        
        waste_pct = packet.get("waste_pct", 0)
        signals = packet.get("signals", [])
        
        # Primary inference based on risk level
        risk_level = packet.get("risk_level", "NORMAL")
        
        if risk_level == "HIGH RISK":
            inferences.append(
                f"CRITICAL: Waste percentage ({packet.get('waste_pct', 0):.2f}%) significantly exceeds "
                f"historical baseline ({packet.get('baseline_waste_pct', 0):.2f}%) by "
                f"{packet.get('waste_deviation', 0):.2f} percentage points."
            )
            
            if packet.get("maintenance_signal"):
                inferences.append(
                    f"Maintenance overdue by {packet.get('days_since_maintenance', 0)} days. "
                    f"Mechanical misalignment likely contributing to elevated waste."
                )
            
            if packet.get("speed_signal"):
                inferences.append(
                    f"Production speed ({packet.get('production_speed', 0):.0f} RPM) exceeds "
                    f"normal operating range for {packet.get('fabric_type', 'this fabric')}."
                )
            
            if packet.get("environment_signal"):
                inferences.append(
                    f"Environmental deviation detected: Humidity {packet.get('humidity', 'N/A')}%, "
                    f"Temperature {packet.get('temperature', 'N/A')}°C. Outside optimal range for "
                    f"{packet.get('fabric_type', 'this fabric')}."
                )
        
        elif risk_level == "WARNING":
            inferences.append(
                f"MODERATE RISK: Waste ({packet.get('waste_pct', 0):.2f}%) above normal range. "
                f"Baseline: {packet.get('baseline_waste_pct', 0):.2f}%. "
                f"Deviation: {packet.get('waste_deviation', 0):.2f}%."
            )
            
            if packet.get("limited_history"):
                inferences.append(
                    "Limited historical data for this machine-fabric combination. "
                    "Baseline derived from fabric-level statistics. Confidence reduced."
                )
            
            if packet.get("maintenance_signal"):
                inferences.append("Maintenance overdue. Recommend scheduling within 7 days.")
        
        else:  # NORMAL
            inferences.append(
                "NORMAL OPERATIONS: Waste percentage within expected historical range. "
                f"Current: {packet.get('waste_pct', 0):.2f}%, Baseline: {packet.get('baseline_waste_pct', 0):.2f}%."
            )
        
        # ML-specific inferences
        if packet.get("is_anomalous"):
            inferences.append(
                f"ML Anomaly Detector flagged this batch as statistically unusual "
                f"(anomaly score: {packet.get('anomaly_score', 0):.4f}). "
                f"Top contributing features: {', '.join(list(packet.get('ml_contributions', {}).keys())[:3])}."
            )
        
        if packet.get("waste_prediction_error", 0) < 0.02:
            inferences.append("ML waste prediction closely matches actual (error < 0.02%). High confidence in prediction.")
        elif packet.get("waste_prediction_error", 0) > 0.1:
            inferences.append(
                f"ML prediction error ({packet.get('waste_prediction_error', 0):.4f}%) higher than typical. "
                f"Investigate feature drift or unusual operating conditions."
            )
        
        return inferences
    
    def _generate_actions(self, packet: dict, evidence: List[Dict]) -> List[str]:
        """Generate recommended actions."""
        actions = []
        risk_level = packet.get("risk_level", "NORMAL")
        
        if risk_level == "HIGH RISK":
            actions.append("IMMEDIATE: Halt production line for safety inspection")
            actions.append("Verify loom/mechanical calibration and alignment")
            actions.append("Check humidity control systems and environmental sensors")
            actions.append("Review maintenance logs - schedule immediate preventive maintenance")
            actions.append("Reduce production speed to baseline until root cause identified")
        
        elif risk_level == "WARNING":
            actions.append("Schedule maintenance review within 48 hours")
            actions.append("Inspect machine for wear, alignment, and calibration")
            actions.append("Verify environmental controls (humidity/temperature) within spec")
            actions.append("Review recent production parameter changes")
            actions.append("Monitor next 3 batches closely for trend confirmation")
        
        else:  # NORMAL
            actions.append("Continue standard monitoring")
            actions.append("Log batch in quality tracking system")
        
        # Signal-specific actions
        if packet.get("maintenance_signal"):
            actions.append("ACTION: Schedule overdue maintenance - verify lubrication, alignment, belt tension")
        
        if packet.get("speed_signal"):
            actions.append("ACTION: Reduce production speed to fabric-specific optimal range")
        
        if packet.get("environment_signal"):
            actions.append("ACTION: Calibrate humidity/temperature sensors; verify HVAC operation")
        
        if packet.get("limited_history"):
            actions.append("ACTION: Prioritize data collection for this machine-fabric combination (target: 8+ batches)")
        
        # ML-specific actions
        if packet.get("is_anomalous"):
            actions.append("ML FLAG: Investigate feature contributions for root cause analysis")
        
        if packet.get("waste_prediction_error", 0) > 0.05:
            actions.append("ML MODEL: High prediction error - verify sensor calibration and data quality")
        
        return actions
    
    def _calculate_confidence(self, packet: dict, evidence: List[Dict]) -> float:
        """Calculate investigation confidence score (0-1)."""
        confidence = 0.5  # Base
        
        # Evidence availability
        if packet.get("maintenance_signal"):
            confidence += 0.1
        if packet.get("speed_signal"):
            confidence += 0.1
        if packet.get("environment_signal"):
            confidence += 0.1
        
        # History availability
        if not packet.get("limited_history"):
            confidence += 0.15
        else:
            confidence -= 0.1
        
        # Evidence quality
        if packet.get("history_count", 0) >= 20:
            confidence += 0.1
        elif packet.get("history_count", 0) >= 8:
            confidence += 0.05
        
        # ML agreement
        if packet.get("ml_flag") and packet.get("biz_flag"):
            confidence += 0.1  # Both ML and rules agree
        elif packet.get("ml_flag") != packet.get("biz_flag"):
            confidence -= 0.05  # Disagreement
        
        # Prediction accuracy
        if packet.get("waste_prediction_error", 1) < 0.02:
            confidence += 0.1
        elif packet.get("waste_prediction_error", 1) > 0.1:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _load_domain_knowledge(self) -> Dict[str, str]:
        """Load built-in domain knowledge."""
        return {
            "cotton_waste_threshold": "15%",
            "polyester_waste_threshold": "12%",
            "silk_waste_threshold": "18%",
            "optimal_humidity_cotton": "60-70%",
            "optimal_humidity_polyester": "50-75%",
            "optimal_humidity_silk": "65-75%",
            "max_speed_cotton": 220,
            "max_speed_polyester": 240,
            "max_speed_silk": 200,
            "maintenance_interval_days": 30,
        }