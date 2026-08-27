from src.legacy_v1.features.waste import (
    calculate_days_since_maintenance,
    calculate_waste_percentage,
)
from src.legacy_v1.models.schemas import BatchRecord


def test_waste_percentage_normal():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    result = calculate_waste_percentage(records)
    assert result[0].waste_pct == 5.0


def test_waste_percentage_zero_waste():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=0,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    result = calculate_waste_percentage(records)
    assert result[0].waste_pct == 0.0


def test_waste_percentage_zero_production():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=0, production_speed=0, waste_quantity=10,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    result = calculate_waste_percentage(records)
    assert result[0].waste_pct == 0.0


def test_waste_percentage_missing_production():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=0, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    result = calculate_waste_percentage(records)
    assert result[0].waste_pct == 0.0


def test_negative_waste_quantity():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=-50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    result = calculate_waste_percentage(records)
    assert result[0].waste_pct == -5.0


def test_days_since_maintenance():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    from datetime import datetime
    ref_date = datetime(2024, 12, 31)
    result = calculate_days_since_maintenance(records, ref_date)
    assert result[0].days_since_maintenance == 60
