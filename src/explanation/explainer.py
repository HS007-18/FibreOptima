from src.legacy_v1.models.schemas import BatchRecord


def generate_explanation(record: BatchRecord) -> list[str]:
    reasons = []

    if record.risk_level == "DATA ISSUE":
        if record.zero_production:
            reasons.append("Production quantity is zero; waste percentage cannot be calculated.")
        if record.invalid_value:
            reasons.append("Record contains invalid numeric values.")
        if record.is_duplicate:
            reasons.append("Duplicate batch ID detected.")
        return reasons

    if record.risk_level == "NORMAL":
        reasons.append("Waste percentage is within expected historical range.")
        if record.limited_history:
            reasons.append("Note: Limited historical data for this machine-fabric combination.")
        return reasons

    if record.waste_z_score is not None:
        if record.waste_z_score > 0:
            reasons.append(
                f"Waste ({record.waste_pct:.1f}%) is significantly above the "
                f"{record.baseline_source.replace('_', ' ')} baseline ({record.baseline_waste_pct:.1f}%)."
            )
        else:
            reasons.append(
                f"Waste ({record.waste_pct:.1f}%) is below the "
                f"{record.baseline_source.replace('_', ' ')} baseline ({record.baseline_waste_pct:.1f}%)."
            )
    else:
        reasons.append(
            f"Waste ({record.waste_pct:.1f}%) compared to baseline ({record.baseline_waste_pct:.1f}%)."
        )

    if record.maintenance_signal:
        reasons.append(
            f"Maintenance is overdue ({record.days_since_maintenance} days since last maintenance)."
        )

    if record.speed_signal:
        direction = "unusually high" if record.speed_z_score and record.speed_z_score > 0 else "unusually low"
        reasons.append(
            f"Production speed is {direction} compared to historical machine behaviour "
            f"(z-score: {record.speed_z_score:.1f})."
        )

    if record.environment_signal:
        reasons.append(
            "Environmental conditions (humidity/temperature) deviate from historical norms for this machine-fabric combination."
        )

    if evaluate_machine_age_signal(record):
        reasons.append(
            f"Machine age ({record.machine_age:.0f} years) exceeds typical operational threshold."
        )

    if record.limited_history:
        reasons.append(
            "Limited historical data available; baseline confidence is reduced."
        )

    if record.humidity_imputed:
        reasons.append("Humidity value was imputed from historical median.")

    return reasons


def evaluate_machine_age_signal(record: BatchRecord) -> bool:
    from src.legacy_v1.config.settings import SETTINGS
    return record.machine_age > SETTINGS.MACHINE_AGE_WARNING_YEARS


def apply_explanations(records: list[BatchRecord]) -> list[BatchRecord]:
    for record in records:
        record.reasons = generate_explanation(record)
    return records
