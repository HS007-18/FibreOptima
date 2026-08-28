"""FibreOptima — Canonical Pipeline (V3).

Single entrypoint for all production intelligence:

    pipeline = FibreOptimaPipeline()

    # Batch processing from CSV
    records, report, df = pipeline.process_file(file_path)

    # DataFrame-based processing
    result = pipeline.process_dataframe(df)

    # Single-batch processing
    result = pipeline.process_record(record_dict)

    # Investigation
    investigation_text = pipeline.investigate_packet(packet)

Architecture:
  1. Input validation & normalisation
  2. Feature engineering
  3. ML waste prediction (HistGradientBoosting)
  4. ML anomaly detection (IsolationForest — no leakage)
  5. Statistical baseline comparison
  6. Offline investigation + RAG retrieval
  7. Recommendation

All waste_pct values are in PERCENTAGE units throughout.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.ingestion.loader import load_and_normalize_csv, load_production_data
from src.legacy_v1.validation.validator import validate_records, impute_missing_humidity
from src.legacy_v1.features.waste import add_derived_features
from src.legacy_v1.baseline.baseline_engine import apply_baselines
from src.legacy_v1.risk.risk_engine import apply_risk_classification
from src.legacy_v1.explanation.explainer import apply_explanations
from src.legacy_v1.recommendation.recommender import apply_recommendations
from src.legacy_v1.models.schemas import BatchRecord, ValidationReport
from src.v2.waste_predictor import WastePredictor, WASTE_FEATURE_COLS
from src.v2.anomaly_detector import AnomalyDetector
from src.hybrid.investigation import OfflineInvestigationEngine, InvestigationReport


# ─────────────────────────────────────────────────────────────────────────────
#  V2 Domain Schema — clean, not BatchRecord-dependent
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BatchResult:
    """V2 domain object — canonical output of the pipeline for one batch.

    All waste values are in PERCENTAGE (%).
    """
    # Identity
    record_id: str
    machine_id: str
    fabric_type: str
    operator: str
    shift: str

    # Production telemetry
    production_quantity: float
    production_speed: float
    waste_quantity: float
    waste_pct: float             # PERCENTAGE — e.g. 0.116 means 0.116%
    machine_age: float
    days_since_maintenance: int
    humidity: Optional[float]
    temperature: Optional[float]

    # Baseline comparison
    baseline_waste_pct: float    # PERCENTAGE
    baseline_source: str
    history_count: int
    waste_deviation: float       # PERCENTAGE (actual - baseline)
    waste_z_score: Optional[float]

    # ML outputs
    predicted_waste_pct: Optional[float]   # PERCENTAGE — model output
    prediction_error: Optional[float]      # PERCENTAGE — |predicted - actual|
    anomaly_score: float
    is_anomalous: bool

    # Risk signals
    maintenance_signal: bool
    speed_signal: bool
    environment_signal: bool
    machine_age_signal: bool
    limited_history: bool
    biz_flag: bool               # any business rule signal active
    ml_flag: bool                # anomaly model flagged

    # Risk classification
    risk_level: str              # "NORMAL" | "WARNING" | "HIGH RISK" | "DATA ISSUE"
    risk_class: str              # "Normal" | "Warning" | "High Risk" | "Data Issue"
    signals: List[str]

    # Data quality
    is_valid: bool
    is_duplicate: bool
    zero_production: bool
    humidity_missing: bool
    humidity_imputed: bool
    data_quality_reason: str

    # Human-readable outputs
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # OOD and Confidence
    is_ood: bool = False
    ood_reasons: List[str] = field(default_factory=list)
    prediction_confidence: str = "High"

    # Business rule flag (waste_pct % above threshold)
    business_rule_flag: bool = False

    # Observed telemetry (for investigation engine)
    observed_telemetry: Dict[str, Any] = field(default_factory=dict)

    # ML contributions
    ml_contributions: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    """Container for pipeline output from process_dataframe."""
    batches: List[BatchResult]
    report: ValidationReport
    df: pd.DataFrame              # flat DataFrame version of batches


# ─────────────────────────────────────────────────────────────────────────────
#  Adapter — BatchRecord → BatchResult
# ─────────────────────────────────────────────────────────────────────────────

_WASTE_PCT_BUSINESS_THRESHOLD = 15.0  # flag if waste_pct > 15%


def _adapt_record(
    record: BatchRecord,
    waste_prediction: Optional[float],
    prediction_error: Optional[float],
    anomaly_score: float,
    is_anomalous: bool,
    ml_contributions: Dict[str, float],
    signals: List[str],
    risk_level: str,
    biz_flag: bool,
    ml_flag: bool,
    is_ood: bool = False,
    ood_reasons: List[str] = None,
    prediction_confidence: str = "High",
) -> BatchResult:
    """Convert legacy BatchRecord + ML outputs into a clean BatchResult."""
    risk_class_map = {
        "NORMAL":     "Normal",
        "WARNING":    "Warning",
        "HIGH RISK":  "High Risk",
        "DATA ISSUE": "Data Issue",
    }

    # Build observed_telemetry dict (for investigation / test_end_to_end.py)
    observed = {
        "Fabric type":         record.fabric_type,
        "Production quantity": record.production_quantity,
        "Production speed":    record.production_speed,
        "Waste quantity":      record.waste_quantity,
        "Waste percentage":    round(record.waste_pct, 6),   # percentage
        "Machine age":         record.machine_age,
        "Humidity":            record.humidity,
        "Temperature":         record.temperature,
        "Operator":            record.operator,
        "Shift":               record.shift,
    }

    return BatchResult(
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
        humidity=record.humidity,
        temperature=record.temperature,
        baseline_waste_pct=record.baseline_waste_pct,
        baseline_source=record.baseline_source,
        history_count=record.history_count,
        waste_deviation=record.waste_deviation,
        waste_z_score=record.waste_z_score,
        predicted_waste_pct=waste_prediction,
        prediction_error=prediction_error,
        anomaly_score=anomaly_score,
        is_anomalous=is_anomalous,
        maintenance_signal=record.maintenance_signal,
        speed_signal=record.speed_signal,
        environment_signal=record.environment_signal,
        machine_age_signal=getattr(record, "machine_age_signal", False),
        limited_history=record.limited_history,
        biz_flag=biz_flag,
        ml_flag=ml_flag,
        risk_level=risk_level,
        risk_class=risk_class_map.get(risk_level, "Unknown"),
        signals=signals,
        is_valid=record.is_valid,
        is_duplicate=record.is_duplicate,
        zero_production=record.zero_production,
        humidity_missing=record.humidity_missing,
        humidity_imputed=record.humidity_imputed,
        data_quality_reason=record.data_quality_reason,
        reasons=list(record.reasons),
        recommendations=list(record.recommendations),
        business_rule_flag=record.waste_pct > _WASTE_PCT_BUSINESS_THRESHOLD,
        observed_telemetry=observed,
        ml_contributions=ml_contributions,
        is_ood=is_ood,
        ood_reasons=ood_reasons or [],
        prediction_confidence=prediction_confidence,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Risk determination
# ─────────────────────────────────────────────────────────────────────────────

def _determine_risk(
    record: BatchRecord,
    ml_flag: bool,
    anomaly_score: float,
) -> Tuple[str, str, List[str], bool]:
    """
    Determine risk level using hybrid V1 z-score + ML signal logic.
    Returns (risk_level, risk_class, signals, biz_flag).
    """
    signals: List[str] = []

    # Waste z-score signals
    z = record.waste_z_score
    if z is not None and z >= SETTINGS.HIGH_RISK_Z_THRESHOLD:
        signals.append("high_waste_deviation")
    elif z is not None and z >= SETTINGS.WARNING_Z_THRESHOLD:
        signals.append("moderate_waste_deviation")

    if record.maintenance_signal:
        signals.append("maintenance_overdue")
    if record.speed_signal:
        signals.append("abnormal_speed")
    if record.environment_signal:
        signals.append("environment_deviation")
    if getattr(record, "machine_age_signal", False):
        signals.append("machine_age_warning")
    if record.limited_history:
        signals.append("limited_history")

    biz_flag = any([
        record.maintenance_signal,
        record.speed_signal,
        record.environment_signal,
        getattr(record, "machine_age_signal", False),
    ])

    # Risk determination
    non_limited = [s for s in signals if s != "limited_history"]

    if z is not None and z >= SETTINGS.HIGH_RISK_Z_THRESHOLD:
        return "HIGH RISK", "High Risk", signals, biz_flag

    if z is not None and z >= SETTINGS.WARNING_Z_THRESHOLD:
        if non_limited:
            return "HIGH RISK", "High Risk", signals, biz_flag
        return "WARNING", "Warning", signals, biz_flag

    if ml_flag and non_limited:
        return "HIGH RISK", "High Risk", signals, biz_flag
    if ml_flag:
        return "WARNING", "Warning", signals, biz_flag

    if len(non_limited) >= 1:
        return "WARNING", "Warning", signals, biz_flag

    if record.limited_history:
        return "WARNING", "Warning", signals, biz_flag

    return "NORMAL", "Normal", signals, biz_flag


# ─────────────────────────────────────────────────────────────────────────────
#  FibreOptimaPipeline
# ─────────────────────────────────────────────────────────────────────────────

class FibreOptimaPipeline:
    """Canonical FibreOptima processing pipeline.

    Usage:
        pipeline = FibreOptimaPipeline()

        # Process a DataFrame
        result = pipeline.process_dataframe(df)
        for batch in result.batches:
            print(batch.risk_level, batch.predicted_waste_pct)

        # Investigate a specific batch
        investigation = pipeline.investigate_packet(batch)

    All waste_pct values in all outputs are in PERCENTAGE units.
    """

    def __init__(
        self,
        artifacts_dir: str = "models/artifacts",
        reference_date: Optional[datetime] = None,
        enable_ml: bool = True,
        enable_rag: bool = False,
        company_db: Optional[object] = None,
    ):
        self.artifacts_dir  = artifacts_dir
        self.reference_date = reference_date or SETTINGS.reference_date
        self.enable_ml      = enable_ml
        self.enable_rag     = enable_rag
        self.company_db     = company_db

        self._waste_predictor: Optional[WastePredictor]  = None
        self._anomaly_detector: Optional[AnomalyDetector] = None
        if enable_ml:
            self._init_ml_models()

        # Investigation engine
        self._investigation_engine = OfflineInvestigationEngine(company_db=self.company_db)

    # ── ML model initialisation ───────────────────────────────────────────
    def _init_ml_models(self) -> None:
        try:
            self._waste_predictor = WastePredictor(self.artifacts_dir)
        except Exception as e:
            print(f"[FibreOptimaPipeline] Warning: Waste predictor unavailable: {e}")

        try:
            self._anomaly_detector = AnomalyDetector(self.artifacts_dir)
        except Exception as e:
            print(f"[FibreOptimaPipeline] Warning: Anomaly detector unavailable: {e}")

    # ── primary interface ─────────────────────────────────────────────────
    def process_file(
        self,
        file_path: str,
        historical_df: Optional[pd.DataFrame] = None,
    ) -> Tuple[List[BatchResult], ValidationReport, pd.DataFrame]:
        """Process a production CSV file end-to-end."""
        records_raw = load_production_data(file_path)[-500:] # Process only last 500 rows for UI responsiveness
        hist_df     = historical_df if historical_df is not None else load_and_normalize_csv(file_path)
        hist_df     = self._normalise_df(hist_df)
        return self._run(records_raw, hist_df)

    def process_dataframe(
        self,
        df: pd.DataFrame,
        historical_df: Optional[pd.DataFrame] = None,
    ) -> Tuple[List[BatchResult], ValidationReport]:
        """Process a DataFrame of production records end-to-end.

        Returns (batches, report) — compatible with test_end_to_end.py signature.
        """
        records_raw = self._df_to_records(df)
        hist_df     = historical_df if historical_df is not None else df.copy()
        # Normalise hist_df column names if needed
        hist_df = self._normalise_df(hist_df)
        batches, report, _ = self._run(records_raw, hist_df)
        return batches, report

    def process_record(
        self,
        record_dict: Dict[str, Any],
        historical_df: Optional[pd.DataFrame] = None,
    ) -> BatchResult:
        """Process a single record dict."""
        df = pd.DataFrame([record_dict])
        batches, _ = self.process_dataframe(df, historical_df)
        if not batches:
            raise ValueError("Pipeline returned no results for input record.")
        return batches[0]

    # ── investigation ─────────────────────────────────────────────────────
    def investigate_packet(self, batch: BatchResult) -> str:
        """Run offline investigation on a BatchResult and return a formatted string."""
        if batch.risk_class == "Data Issue":
            return f"Investigation Mode: SKIPPED\nRecord: {batch.record_id}  |  Risk: Data Issue\n\nInvestigation skipped due to validation failure: {batch.data_quality_reason}"
        packet_dict = self._batch_to_packet_dict(batch)
        report = self._investigation_engine.investigate(packet_dict)
        return self._format_investigation(report)

    def investigate_packet_structured(self, batch: BatchResult) -> InvestigationReport:
        """Return the structured InvestigationReport dataclass."""
        if batch.risk_class == "Data Issue":
            return InvestigationReport(
                record_id=batch.record_id,
                investigation_mode="SKIPPED",
                risk_class="Data Issue",
                confidence=0.0,
                observed_evidence={"Error": "Data quality check failed."},
                ml_evidence={},
                retrieved_knowledge=[],
                logical_inference=[f"Validation failed: {batch.data_quality_reason}"],
                recommended_actions=["Fix input data schema and values."]
            )
        packet_dict = self._batch_to_packet_dict(batch)
        return self._investigation_engine.investigate(packet_dict)

    # ── internal pipeline ─────────────────────────────────────────────────
    def _run(
        self,
        records_raw: List[BatchRecord],
        hist_df: pd.DataFrame,
    ) -> Tuple[List[BatchResult], ValidationReport, pd.DataFrame]:
        """Execute the full pipeline on a list of BatchRecord objects."""
        # 1. Validate
        valid_machine_ids = None
        if self.company_db:
            valid_machine_ids = self.company_db.get_all_machine_ids()
            
        records, report = validate_records(records_raw, hist_df, valid_machine_ids=valid_machine_ids)

        # 2. Impute missing humidity
        records = impute_missing_humidity(records, hist_df, report)

        # 3. Derived features (waste_pct, days_since_maintenance)
        records = add_derived_features(records, hist_df, self.reference_date)

        # 4. Baseline comparison
        records = apply_baselines(records, hist_df)

        # 5. V1 risk signals
        records = apply_risk_classification(records, hist_df)

        # 6. ML layer
        batch_results = []
        for record in records:
            br = self._process_one(record)
            batch_results.append(br)

        # 7. Explanations / recommendations (V1 — on the original records)
        records = apply_explanations(records)
        records = apply_recommendations(records)

        # Sync reasons/recommendations back to batch_results
        for br, rec in zip(batch_results, records):
            br.reasons        = list(rec.reasons)
            br.recommendations = list(rec.recommendations)

        df = self._batches_to_df(batch_results)
        return batch_results, report, df

    def _process_one(self, record: BatchRecord) -> BatchResult:
        """Apply ML + risk determination to a single validated BatchRecord."""
        # Default ML outputs
        waste_prediction  = 0.0
        prediction_error  = 0.0
        anomaly_score     = 0.0
        is_anomalous      = False
        ml_contributions: Dict[str, float] = {}
        is_ood            = False
        ood_reasons       = []
        prediction_confidence = "High"

        if record.is_valid and not record.zero_production:
            # Waste prediction
            if self._waste_predictor:
                try:
                    feat_dict = self._build_waste_feature_dict(record)
                    waste_prediction = self._waste_predictor.predict_single(feat_dict)
                    prediction_error = abs(waste_prediction - record.waste_pct)
                except Exception as e:
                    print(f"[FibreOptimaPipeline] Waste prediction failed for {record.batch_id}: {e}")
                    waste_prediction = record.waste_pct  # fallback to actual

            # Anomaly detection
            if self._anomaly_detector:
                try:
                    feat_dict   = self._build_anomaly_feature_dict(record)
                    anom_result = self._anomaly_detector.predict_anomaly_single(feat_dict)
                    anomaly_score    = anom_result.get("anomaly_score", 0.0)
                    is_anomalous     = anom_result.get("is_anomalous", False)
                    ml_contributions = anom_result.get("feature_contributions", {})
                    is_ood           = anom_result.get("is_ood", False)
                    ood_reasons      = anom_result.get("ood_reasons", [])
                    prediction_confidence = anom_result.get("prediction_confidence", "High")
                except Exception as e:
                    print(f"[FibreOptimaPipeline] Anomaly detection failed for {record.batch_id}: {e}")

        # Risk signal determination (handles DATA ISSUE internally)
        if not record.is_valid or record.zero_production:
            return _adapt_record(
                record,
                waste_prediction=None,
                prediction_error=None,
                anomaly_score=0.0,
                is_anomalous=False,
                ml_contributions={},
                signals=["data_issue"],
                risk_level="DATA ISSUE",
                biz_flag=False,
                ml_flag=False,
                is_ood=False,
                prediction_confidence="N/A",
            )

        # Set machine_age_signal on record (V1 missing field)
        record.machine_age_signal = record.machine_age > SETTINGS.MACHINE_AGE_WARNING_YEARS

        risk_level, risk_class, signals, biz_flag = _determine_risk(
            record, ml_flag=is_anomalous, anomaly_score=anomaly_score
        )
        ml_flag = is_anomalous

        return _adapt_record(
            record,
            waste_prediction=waste_prediction,
            prediction_error=prediction_error,
            anomaly_score=anomaly_score,
            is_anomalous=is_anomalous,
            ml_contributions=ml_contributions,
            signals=signals,
            risk_level=risk_level,
            biz_flag=biz_flag,
            ml_flag=ml_flag,
            is_ood=is_ood,
            ood_reasons=ood_reasons,
            prediction_confidence=prediction_confidence,
        )

    # ── feature dict builders ─────────────────────────────────────────────
    @staticmethod
    def _build_waste_feature_dict(record: BatchRecord) -> Dict[str, Any]:
        return {
            "Machine ID":          record.machine_id,
            "Fabric type":         record.fabric_type,
            "Operator":            record.operator,
            "Shift":               record.shift,
            "Production quantity": record.production_quantity,
            "Production speed":    record.production_speed,
            "Machine age":         record.machine_age,
            "Humidity":            record.humidity,
            "Temperature":         record.temperature,
            "Machine failure":     0,  # default — not in raw input
        }

    @staticmethod
    def _build_anomaly_feature_dict(record: BatchRecord) -> Dict[str, Any]:
        return {
            "Machine ID":          record.machine_id,
            "Fabric type":         record.fabric_type,
            "Operator":            record.operator,
            "Shift":               record.shift,
            "Production quantity": record.production_quantity,
            "Production speed":    record.production_speed,
            "Machine age":         record.machine_age,
            "Humidity":            record.humidity,
            "Temperature":         record.temperature,
            "Machine failure":     0,
        }

    # ── investigation packet builder ──────────────────────────────────────
    @staticmethod
    def _batch_to_packet_dict(batch: BatchResult) -> Dict[str, Any]:
        """Convert BatchResult to the packet dict expected by InvestigationEngine."""
        return {
            "record_id":              batch.record_id,
            "machine_id":             batch.machine_id,
            "fabric_type":            batch.fabric_type,
            "operator":               batch.operator,
            "shift":                  batch.shift,
            "production_quantity":    batch.production_quantity,
            "production_speed":       batch.production_speed,
            "waste_quantity":         batch.waste_quantity,
            "waste_pct":              batch.waste_pct,
            "machine_age":            batch.machine_age,
            "days_since_maintenance": batch.days_since_maintenance,
            "humidity":               batch.humidity,
            "temperature":            batch.temperature,
            "waste_prediction":       batch.predicted_waste_pct,
            "waste_prediction_error": batch.prediction_error,
            "anomaly_score":          batch.anomaly_score,
            "is_anomalous":           batch.is_anomalous,
            "ml_flag":                batch.ml_flag,
            "biz_flag":               batch.biz_flag,
            "baseline_waste_pct":     batch.baseline_waste_pct,
            "waste_deviation":        batch.waste_deviation,
            "waste_z_score":          batch.waste_z_score,
            "baseline_source":        batch.baseline_source,
            "history_count":          batch.history_count,
            "maintenance_signal":     batch.maintenance_signal,
            "speed_signal":           batch.speed_signal,
            "environment_signal":     batch.environment_signal,
            "machine_age_signal":     batch.machine_age_signal,
            "limited_history":        batch.limited_history,
            "risk_level":             batch.risk_level,
            "risk_class":             batch.risk_class,
            "signals":                batch.signals,
            "ml_contributions":       batch.ml_contributions,
            "is_ood":                 batch.is_ood,
            "ood_reasons":            batch.ood_reasons,
            "prediction_confidence":  batch.prediction_confidence,
        }

    # ── investigation formatting ──────────────────────────────────────────
    @staticmethod
    def _format_investigation(report: InvestigationReport) -> str:
        """Format InvestigationReport into a readable string.

        Guaranteed to contain:
          "Investigation Mode:"  — for test assertions
          "OBSERVED EVIDENCE"   — for test assertions
          "LOGICAL INFERENCE"   — for test assertions
        """
        lines = [
            f"Investigation Mode: {report.investigation_mode}",
            f"Record: {report.record_id}  |  Risk: {report.risk_class}  |  Confidence: {report.confidence:.2f}",
            "",
            "OBSERVED EVIDENCE",
            "─" * 40,
        ]
        for k, v in report.observed_evidence.items():
            lines.append(f"  {k}: {v}")

        lines += ["", "ML EVIDENCE", "─" * 40]
        for k, v in report.ml_evidence.items():
            lines.append(f"  {k}: {v}")

        if report.retrieved_knowledge:
            lines += ["", "RETRIEVED KNOWLEDGE", "─" * 40]
            for doc in report.retrieved_knowledge[:3]:
                lines.append(f"  [{doc.get('source', '?')}] {str(doc.get('content', ''))[:120]}")

        lines += ["", "LOGICAL INFERENCE", "─" * 40]
        for inf in report.logical_inference:
            lines.append(f"  • {inf}")

        lines += ["", "RECOMMENDED ACTIONS", "─" * 40]
        for act in report.recommended_actions:
            lines.append(f"  → {act}")

        return "\n".join(lines)

    # ── data helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _df_to_records(df: pd.DataFrame) -> List[BatchRecord]:
        """Convert a DataFrame to a list of BatchRecord objects."""
        # Column alias map (title-case → snake_case)
        aliases = SETTINGS.COLUMN_ALIASES
        records = []
        for _, row in df.iterrows():
            def get(col_title, col_snake, default=None):
                if col_title in row.index:
                    return row[col_title]
                if col_snake in row.index:
                    return row[col_snake]
                return default

            production_quantity = get("Production quantity", "production_quantity", 0.0)
            production_quantity = float(production_quantity) if pd.notna(production_quantity) else 0.0

            production_speed = get("Production speed", "production_speed", 0.0)
            production_speed = float(production_speed) if pd.notna(production_speed) else 0.0

            waste_quantity = get("Waste quantity", "waste_quantity", 0.0)
            waste_quantity = float(waste_quantity) if pd.notna(waste_quantity) else 0.0

            machine_age = get("Machine age", "machine_age", 0.0)
            machine_age = float(machine_age) if pd.notna(machine_age) else 0.0

            humidity_raw = get("Humidity", "humidity", None)
            humidity = float(humidity_raw) if pd.notna(humidity_raw) and humidity_raw is not None else None

            temperature_raw = get("Temperature", "temperature", None)
            temperature = float(temperature_raw) if pd.notna(temperature_raw) and temperature_raw is not None else None

            record = BatchRecord(
                batch_id=str(get("Batch ID", "batch_id", "UNKNOWN")),
                machine_id=str(get("Machine ID", "machine_id", "UNKNOWN")),
                fabric_type=str(get("Fabric type", "fabric_type", "UNKNOWN")),
                operator=str(get("Operator", "operator", "UNKNOWN")),
                shift=str(get("Shift", "shift", "UNKNOWN")),
                production_quantity=production_quantity,
                production_speed=production_speed,
                waste_quantity=waste_quantity,
                machine_age=machine_age,
                last_maintenance_date=str(get("Last maintenance date", "last_maintenance_date", "2026-01-01")),
                humidity=humidity,
                temperature=temperature,
            )
            records.append(record)
        return records

    @staticmethod
    def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
        """Normalise column names to snake_case for legacy components."""
        aliases = {
            "Batch ID": "batch_id",
            "Machine ID": "machine_id",
            "Fabric type": "fabric_type",
            "Fabric Type": "fabric_type",
            "Operator": "operator",
            "Shift": "shift",
            "Production quantity": "production_quantity",
            "Production Quantity": "production_quantity",
            "Production speed": "production_speed",
            "Production Speed": "production_speed",
            "Waste quantity": "waste_quantity",
            "Waste Quantity": "waste_quantity",
            "Machine age": "machine_age",
            "Machine Age": "machine_age",
            "Last maintenance date": "last_maintenance_date",
            "Last Maintenance Date": "last_maintenance_date",
            "Humidity": "humidity",
            "Temperature": "temperature",
            "Machine failure": "machine_failure",
        }
        df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
        
        # Ensure waste_pct exists for baseline calculation
        if "waste_pct" not in df.columns and "waste_quantity" in df.columns and "production_quantity" in df.columns:
            import numpy as np
            df["waste_pct"] = (df["waste_quantity"] / df["production_quantity"].replace(0, np.nan)) * 100.0
            
        return df

    @staticmethod
    def _batches_to_df(batches: List[BatchResult]) -> pd.DataFrame:
        """Convert list of BatchResult to flat DataFrame."""
        rows = []
        for b in batches:
            rows.append({
                "batch_id":              b.record_id,
                "machine_id":            b.machine_id,
                "fabric_type":           b.fabric_type,
                "operator":              b.operator,
                "shift":                 b.shift,
                "production_quantity":   b.production_quantity,
                "production_speed":      b.production_speed,
                "waste_quantity":        b.waste_quantity,
                "waste_pct":             round(b.waste_pct, 6),
                "machine_age":           b.machine_age,
                "days_since_maintenance": b.days_since_maintenance,
                "humidity":              b.humidity,
                "temperature":           b.temperature,
                "baseline_waste_pct":    round(b.baseline_waste_pct, 6),
                "baseline_source":       b.baseline_source,
                "history_count":         b.history_count,
                "waste_deviation":       round(b.waste_deviation, 6),
                "waste_z_score":         round(b.waste_z_score, 4) if b.waste_z_score else None,
                "predicted_waste_pct":   round(b.predicted_waste_pct, 6) if b.predicted_waste_pct is not None else None,
                "prediction_error":      round(b.prediction_error, 6) if b.prediction_error is not None else None,
                "anomaly_score":         round(b.anomaly_score, 4),
                "is_anomalous":          b.is_anomalous,
                "ml_flag":               b.ml_flag,
                "biz_flag":              b.biz_flag,
                "business_rule_flag":    b.business_rule_flag,
                "risk_level":            b.risk_level,
                "risk_class":            b.risk_class,
                "signals":               "; ".join(b.signals),
                "maintenance_signal":    b.maintenance_signal,
                "speed_signal":          b.speed_signal,
                "environment_signal":    b.environment_signal,
                "limited_history":       b.limited_history,
                "is_valid":              b.is_valid,
                "is_duplicate":          b.is_duplicate,
                "zero_production":       b.zero_production,
                "humidity_missing":      b.humidity_missing,
                "humidity_imputed":      b.humidity_imputed,
                "data_quality_reason":   b.data_quality_reason,
                "reasons":               "; ".join(b.reasons),
                "recommendations":       "; ".join(b.recommendations),
                "is_ood":                b.is_ood,
                "ood_reasons":           "; ".join(b.ood_reasons),
                "prediction_confidence": b.prediction_confidence,
            })
        return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
#  Legacy backward-compatibility functions
#  (existing app.py and tests that call process_production_data)
# ─────────────────────────────────────────────────────────────────────────────

def process_production_data(
    file_path: str,
    reference_date: datetime = None,
    historical_df: pd.DataFrame = None,
    enable_ml: bool = True,
    enable_rag: bool = False,
) -> Tuple[List[BatchResult], ValidationReport, pd.DataFrame, pd.DataFrame, List[dict]]:
    """Legacy-compatible pipeline function.

    Returns: (batches, report, df, hist_df, investigations=[])
    """
    pipeline = FibreOptimaPipeline(
        reference_date=reference_date,
        enable_ml=enable_ml,
        enable_rag=enable_rag,
    )
    if file_path and os.path.exists(str(file_path)):
        batches, report, df = pipeline.process_file(file_path, historical_df)
        hist_df = historical_df if historical_df is not None else load_and_normalize_csv(file_path)
    else:
        raise FileNotFoundError(f"File not found: {file_path}")

    return batches, report, df, hist_df, []


def records_to_dataframe(records) -> pd.DataFrame:
    """Legacy adapter — converts BatchResult list to DataFrame."""
    if not records:
        return pd.DataFrame()
    if isinstance(records[0], BatchResult):
        pipeline = FibreOptimaPipeline.__new__(FibreOptimaPipeline)
        return FibreOptimaPipeline._batches_to_df(records)
    # If still legacy BatchRecord objects, convert best-effort
    data = []
    for r in records:
        data.append({k: getattr(r, k, None) for k in vars(r)})
    return pd.DataFrame(data)