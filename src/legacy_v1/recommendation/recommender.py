from src.legacy_v1.models.schemas import BatchRecord


def generate_recommendations(record: BatchRecord) -> list[str]:
    recommendations = []

    if record.risk_level == "DATA ISSUE":
        if record.zero_production:
            recommendations.append("Investigate why production quantity is zero for this batch.")
        if record.invalid_value:
            recommendations.append("Review data entry for invalid numeric values.")
        if record.is_duplicate:
            recommendations.append("Remove duplicate batch record from the dataset.")
        return recommendations

    if record.risk_level == "NORMAL":
        recommendations.append("No immediate action required. Continue monitoring.")
        return recommendations

    priority_actions = []

    if record.maintenance_signal:
        priority_actions.append("Verify maintenance status and inspect the machine.")

    if record.speed_signal:
        priority_actions.append("Review production speed against normal machine operating behaviour.")

    if record.environment_signal:
        priority_actions.append("Review current environmental conditions for the fabric being produced.")

    if record.waste_z_score is not None and record.waste_z_score > 2:
        priority_actions.append("Inspect machine and fabric process for recent changes or issues.")

    if evaluate_machine_age_signal(record):
        priority_actions.append("Consider scheduling preventive maintenance for aging machine.")

    if record.limited_history:
        priority_actions.append("Collect more production data for this machine-fabric combination to improve baseline confidence.")

    if priority_actions:
        recommendations.extend(priority_actions)
    else:
        recommendations.append("Review batch details and compare with recent production history.")

    return recommendations


def evaluate_machine_age_signal(record: BatchRecord) -> bool:
    from src.legacy_v1.config.settings import SETTINGS
    return record.machine_age > SETTINGS.MACHINE_AGE_WARNING_YEARS


def apply_recommendations(records: list[BatchRecord]) -> list[BatchRecord]:
    for record in records:
        record.recommendations = generate_recommendations(record)
    return records
