from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.models.schemas import BatchRecord


def evaluate_maintenance_signal(record: BatchRecord) -> bool:
    return record.days_since_maintenance > SETTINGS.MAINTENANCE_OVERDUE_DAYS


def evaluate_speed_signal(record: BatchRecord) -> bool:
    if record.speed_z_score is None:
        return False
    return abs(record.speed_z_score) > SETTINGS.SPEED_ANOMALY_Z_THRESHOLD


def evaluate_environment_signal(record: BatchRecord, reference_df) -> bool:
    if reference_df is None or reference_df.empty:
        return False
    if record.humidity is None or record.temperature is None:
        return False

    mf_df = reference_df[
        (reference_df["machine_id"] == record.machine_id) &
        (reference_df["fabric_type"] == record.fabric_type)
    ]
    if len(mf_df) < 5:
        return False

    hum_mean = mf_df["humidity"].mean()
    hum_std = mf_df["humidity"].std()
    temp_mean = mf_df["temperature"].mean()
    temp_std = mf_df["temperature"].std()

    signals = 0
    if hum_std > 0 and abs(record.humidity - hum_mean) / hum_std > 2:
        signals += 1
    if temp_std > 0 and abs(record.temperature - temp_mean) / temp_std > 2:
        signals += 1

    return signals >= 1


def evaluate_machine_age_signal(record: BatchRecord) -> bool:
    return record.machine_age > SETTINGS.MACHINE_AGE_WARNING_YEARS


def classify_risk(record: BatchRecord, reference_df=None) -> BatchRecord:
    if not record.is_valid or record.zero_production:
        record.risk_level = "DATA ISSUE"
        return record

    record.maintenance_signal = evaluate_maintenance_signal(record)
    record.speed_signal = evaluate_speed_signal(record)
    record.environment_signal = evaluate_environment_signal(record, reference_df)

    waste_z = record.waste_z_score
    if waste_z is None:
        waste_z = 0.0

    signals = []
    if record.maintenance_signal:
        signals.append("maintenance")
    if record.speed_signal:
        signals.append("speed")
    if record.environment_signal:
        signals.append("environment")
    if evaluate_machine_age_signal(record):
        signals.append("machine_age")

    # Primary waste deviation drives risk; supporting signals amplify existing concern
    if waste_z >= SETTINGS.HIGH_RISK_Z_THRESHOLD:
        record.risk_level = "HIGH RISK"
    elif waste_z >= SETTINGS.WARNING_Z_THRESHOLD:
        # Moderate abnormality: supporting signals can escalate to HIGH RISK
        if len(signals) >= 1:
            record.risk_level = "HIGH RISK"
        else:
            record.risk_level = "WARNING"
    else:
        # Waste is within normal range: single signal = WARNING (caution)
        if len(signals) >= 1:
            record.risk_level = "WARNING"
        else:
            record.risk_level = "NORMAL"

    # Limited history: adds uncertainty but doesn't cap genuine HIGH RISK
    if record.limited_history and record.risk_level == "NORMAL":
        record.risk_level = "WARNING"

    return record


def apply_risk_classification(records: list[BatchRecord], reference_df=None) -> list[BatchRecord]:
    for record in records:
        classify_risk(record, reference_df)
    return records
