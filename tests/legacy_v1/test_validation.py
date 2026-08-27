import pandas as pd

from src.legacy_v1.models.schemas import BatchRecord, ValidationReport
from src.legacy_v1.validation.validator import impute_missing_humidity, validate_records


def test_zero_production():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=0, production_speed=1000, waste_quantity=10,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    validated, report = validate_records(records)
    assert validated[0].zero_production is True
    assert validated[0].is_valid is False
    assert validated[0].risk_level == "DATA ISSUE"
    assert report.zero_production == 1


def test_duplicate_detection():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        ),
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    validated, report = validate_records(records)
    assert validated[0].is_duplicate is False
    assert validated[1].is_duplicate is True
    assert validated[1].is_valid is False
    assert report.duplicates == 1


def test_missing_humidity():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=None, temperature=24.0
        )
    ]
    validated, report = validate_records(records)
    assert validated[0].humidity_missing is True
    assert report.missing_values == 1


def test_invalid_values():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=-100, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        ),
        BatchRecord(
            batch_id="B002", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=-10,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        ),
        BatchRecord(
            batch_id="B003", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=-2, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        ),
    ]
    validated, report = validate_records(records)
    assert all(r.invalid_value for r in validated)
    assert all(not r.is_valid for r in validated)
    assert report.invalid_values == 3


def test_humidity_imputation():
    ref_df = pd.DataFrame({
        "machine_id": ["M01", "M01", "M01"],
        "fabric_type": ["Cotton", "Cotton", "Cotton"],
        "humidity": [60.0, 65.0, 70.0],
    })
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=None, temperature=24.0
        )
    ]
    records[0].humidity_missing = True
    records[0].is_valid = True
    report = ValidationReport()
    validated = impute_missing_humidity(records, ref_df, report)
    assert validated[0].humidity is not None
    assert validated[0].humidity_imputed is True
    assert report.imputed_values == 1


def test_humidity_out_of_range():
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=150.0, temperature=24.0
        ),
        BatchRecord(
            batch_id="B002", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=-10.0, temperature=24.0
        ),
    ]
    validated, report = validate_records(records)
    assert validated[0].invalid_value is True
    assert validated[1].invalid_value is True
    assert report.invalid_values == 2
