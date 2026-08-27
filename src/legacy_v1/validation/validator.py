import numpy as np
import pandas as pd

from src.legacy_v1.models.schemas import BatchRecord, ValidationReport


def validate_records(records: list[BatchRecord], reference_df: pd.DataFrame = None) -> tuple[list[BatchRecord], ValidationReport]:
    report = ValidationReport()
    report.total_records = len(records)

    batch_id_counts = {}
    for r in records:
        batch_id_counts[r.batch_id] = batch_id_counts.get(r.batch_id, 0) + 1

    seen_batch_ids = set()

    for record in records:
        issues = []

        if batch_id_counts[record.batch_id] > 1:
            if record.batch_id in seen_batch_ids:
                record.is_duplicate = True
                record.is_valid = False
                issues.append(f"Duplicate batch ID: {record.batch_id}")
                report.duplicates += 1
            else:
                seen_batch_ids.add(record.batch_id)
        else:
            seen_batch_ids.add(record.batch_id)

        if record.production_quantity == 0:
            record.zero_production = True
            record.is_valid = False
            record.risk_level = "DATA ISSUE"
            issues.append("Production quantity is zero")
            report.zero_production += 1

        if record.humidity is None or (isinstance(record.humidity, float) and np.isnan(record.humidity)):
            record.humidity_missing = True
            issues.append("Humidity is missing")
            report.missing_values += 1

        invalid_checks = [
            (record.production_quantity < 0, "Production quantity is negative"),
            (record.waste_quantity < 0, "Waste quantity is negative"),
            (record.machine_age < 0, "Machine age is negative"),
            (record.humidity is not None and record.humidity < 0, "Humidity is negative"),
            (record.humidity is not None and record.humidity > 100, "Humidity exceeds 100%"),
            (record.temperature is not None and record.temperature < -50, "Temperature unrealistic"),
            (record.temperature is not None and record.temperature > 100, "Temperature unrealistic"),
        ]

        for condition, msg in invalid_checks:
            if condition:
                record.invalid_value = True
                record.is_valid = False
                record.risk_level = "DATA ISSUE"
                issues.append(msg)
                report.invalid_values += 1

        if issues:
            record.data_quality_reason = "; ".join(issues)
            report.data_issues += 1
        else:
            report.valid_records += 1

    report.details = [
        f"Total Records: {report.total_records}",
        f"Valid Records: {report.valid_records}",
        f"Data Issues: {report.data_issues}",
        f"Duplicates: {report.duplicates}",
        f"Missing Values: {report.missing_values}",
        f"Zero Production: {report.zero_production}",
        f"Invalid Values: {report.invalid_values}",
    ]

    return records, report


def impute_missing_humidity(records: list[BatchRecord], reference_df: pd.DataFrame, report: ValidationReport) -> list[BatchRecord]:
    if reference_df is None or reference_df.empty:
        return records

    humidity_medians = reference_df.groupby(["machine_id", "fabric_type"])["humidity"].median()
    global_median = reference_df["humidity"].median()

    for record in records:
        if record.humidity_missing and record.is_valid:
            key = (record.machine_id, record.fabric_type)
            if key in humidity_medians and not np.isnan(humidity_medians[key]):
                record.humidity = float(humidity_medians[key])
            else:
                record.humidity = float(global_median)
            record.humidity_imputed = True
            report.imputed_values += 1

    return records
