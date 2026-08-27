import pandas as pd

from src.legacy_v1.models.schemas import BatchRecord
from src.legacy_v1.risk.risk_engine import classify_risk


def test_normal_risk():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1000, waste_quantity=50,
        machine_age=5, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.waste_pct = 5.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "machine_fabric"
    record.history_count = 10
    record.waste_z_score = 0.0
    record.days_since_maintenance = 10
    record.speed_z_score = 0.0
    record.limited_history = False

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.risk_level == "NORMAL"


def test_warning_risk_moderate_deviation():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1000, waste_quantity=50,
        machine_age=5, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.waste_pct = 7.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "machine_fabric"
    record.history_count = 10
    record.waste_z_score = 1.8
    record.days_since_maintenance = 10
    record.speed_z_score = 0.0
    record.limited_history = False

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.risk_level == "WARNING"


def test_high_risk_strong_deviation():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1000, waste_quantity=50,
        machine_age=5, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.waste_pct = 15.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "machine_fabric"
    record.history_count = 10
    record.waste_z_score = 3.0
    record.days_since_maintenance = 10
    record.speed_z_score = 0.0
    record.limited_history = False

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.risk_level == "HIGH RISK"


def test_data_issue_zero_production():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=0, production_speed=0, waste_quantity=10,
        machine_age=5, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.zero_production = True
    record.is_valid = False

    result = classify_risk(record)
    assert result.risk_level == "DATA ISSUE"


def test_maintenance_signal():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1000, waste_quantity=50,
        machine_age=5, last_maintenance_date="2024-09-01",
        humidity=65.0, temperature=24.0
    )
    record.days_since_maintenance = 100
    record.waste_pct = 7.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "machine_fabric"
    record.history_count = 10
    record.waste_z_score = 1.0
    record.speed_z_score = 0.0
    record.limited_history = False

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.maintenance_signal is True
    assert result.risk_level in ["WARNING", "HIGH RISK"]


def test_speed_signal():
    record = BatchRecord(
        batch_id="B001", machine_id="M01", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1500, waste_quantity=50,
        machine_age=5, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.waste_pct = 7.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "machine_fabric"
    record.history_count = 10
    record.waste_z_score = 1.0
    record.days_since_maintenance = 10
    record.speed_z_score = 3.0
    record.limited_history = False

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.speed_signal is True
    assert result.risk_level in ["WARNING", "HIGH RISK"]


def test_limited_history_warning():
    record = BatchRecord(
        batch_id="B001", machine_id="M99", fabric_type="Cotton",
        operator="OP001", shift="Morning",
        production_quantity=1000, production_speed=1000, waste_quantity=50,
        machine_age=0, last_maintenance_date="2024-11-01",
        humidity=65.0, temperature=24.0
    )
    record.waste_pct = 7.0
    record.baseline_waste_pct = 5.0
    record.baseline_source = "fabric_insufficient"
    record.history_count = 5
    record.waste_z_score = 1.5
    record.days_since_maintenance = 10
    record.speed_z_score = 0.0
    record.limited_history = True

    ref_df = pd.DataFrame({
        "machine_id": ["M01"], "fabric_type": ["Cotton"],
        "humidity": [65.0], "temperature": [24.0]
    })

    result = classify_risk(record, ref_df)
    assert result.limited_history is True
    assert result.risk_level == "WARNING"
