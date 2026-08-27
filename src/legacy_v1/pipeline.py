from datetime import datetime

import pandas as pd

from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.baseline.baseline_engine import apply_baselines
from src.legacy_v1.explanation.explainer import apply_explanations
from src.legacy_v1.features.waste import add_derived_features
from src.legacy_v1.ingestion.loader import load_and_normalize_csv, load_production_data
from src.legacy_v1.models.schemas import BatchRecord, ValidationReport
from src.legacy_v1.recommendation.recommender import apply_recommendations
from src.legacy_v1.risk.risk_engine import apply_risk_classification
from src.legacy_v1.validation.validator import impute_missing_humidity, validate_records


def process_production_data(
    file_path: str,
    reference_date: datetime = None,
    historical_df: pd.DataFrame = None
) -> tuple[list[BatchRecord], ValidationReport, pd.DataFrame]:
    if reference_date is None:
        reference_date = SETTINGS.reference_date

    records = load_production_data(file_path)

    if historical_df is None:
        hist_df = load_and_normalize_csv(file_path)
    else:
        hist_df = historical_df.copy()

    records, report = validate_records(records, hist_df)

    records = impute_missing_humidity(records, hist_df, report)

    records = add_derived_features(records, hist_df, reference_date)

    if historical_df is None:
        hist_df = records_to_dataframe(records)

    records = apply_baselines(records, hist_df)

    records = apply_risk_classification(records, hist_df)

    records = apply_explanations(records)

    records = apply_recommendations(records)

    return records, report, hist_df


def records_to_dataframe(records: list[BatchRecord]) -> pd.DataFrame:
    data = []
    for r in records:
        data.append({
            "batch_id": r.batch_id,
            "machine_id": r.machine_id,
            "fabric_type": r.fabric_type,
            "operator": r.operator,
            "shift": r.shift,
            "production_quantity": r.production_quantity,
            "production_speed": r.production_speed,
            "waste_quantity": r.waste_quantity,
            "waste_pct": round(r.waste_pct, 2),
            "machine_age": r.machine_age,
            "days_since_maintenance": r.days_since_maintenance,
            "humidity": r.humidity,
            "temperature": r.temperature,
            "baseline_waste_pct": round(r.baseline_waste_pct, 2),
            "baseline_source": r.baseline_source,
            "history_count": r.history_count,
            "waste_deviation": round(r.waste_deviation, 2),
            "waste_z_score": round(r.waste_z_score, 2) if r.waste_z_score is not None else None,
            "maintenance_signal": r.maintenance_signal,
            "speed_signal": r.speed_signal,
            "environment_signal": r.environment_signal,
            "limited_history": r.limited_history,
            "risk_level": r.risk_level,
            "reasons": "; ".join(r.reasons),
            "recommendations": "; ".join(r.recommendations),
            "is_valid": r.is_valid,
            "is_duplicate": r.is_duplicate,
            "zero_production": r.zero_production,
            "humidity_missing": r.humidity_missing,
            "humidity_imputed": r.humidity_imputed,
            "invalid_value": r.invalid_value,
            "data_quality_reason": r.data_quality_reason,
        })
    return pd.DataFrame(data)
