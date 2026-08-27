from datetime import datetime

import pandas as pd

from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.models.schemas import BatchRecord


def calculate_waste_percentage(records: list[BatchRecord]) -> list[BatchRecord]:
    for record in records:
        if record.production_quantity > 0:
            record.waste_pct = (record.waste_quantity / record.production_quantity) * 100
        else:
            record.waste_pct = 0.0
    return records


def calculate_days_since_maintenance(records: list[BatchRecord], reference_date: datetime = None) -> list[BatchRecord]:
    if reference_date is None:
        reference_date = SETTINGS.reference_date

    for record in records:
        try:
            maint_date = datetime.fromisoformat(record.last_maintenance_date)
            record.days_since_maintenance = (reference_date - maint_date).days
        except (ValueError, TypeError):
            record.days_since_maintenance = 999
    return records


def calculate_speed_deviation(records: list[BatchRecord], reference_df: pd.DataFrame) -> list[BatchRecord]:
    if reference_df is None or reference_df.empty:
        return records

    machine_speed_stats = reference_df.groupby("machine_id")["production_speed"].agg(["mean", "std"]).reset_index()
    machine_speed_stats.columns = ["machine_id", "speed_mean", "speed_std"]

    for record in records:
        if not record.is_valid:
            continue
        machine_stats = machine_speed_stats[machine_speed_stats["machine_id"] == record.machine_id]
        if not machine_stats.empty:
            mean_speed = machine_stats.iloc[0]["speed_mean"]
            std_speed = machine_stats.iloc[0]["speed_std"]
            if std_speed and std_speed > 0:
                record.speed_z_score = (record.production_speed - mean_speed) / std_speed
            else:
                record.speed_z_score = 0.0
        else:
            record.speed_z_score = None
    return records


def add_derived_features(records: list[BatchRecord], reference_df: pd.DataFrame = None, reference_date: datetime = None) -> list[BatchRecord]:
    records = calculate_waste_percentage(records)
    records = calculate_days_since_maintenance(records, reference_date)
    if reference_df is not None:
        records = calculate_speed_deviation(records, reference_df)
    return records
