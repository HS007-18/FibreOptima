import pandas as pd

from src.legacy_v1.baseline.baseline_engine import apply_baselines, get_baseline
from src.legacy_v1.models.schemas import BatchRecord


def test_baseline_sufficient_history():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 10,
        "fabric_type": ["Cotton"] * 10,
        "waste_pct": [5.0, 5.2, 4.8, 5.1, 5.3, 4.9, 5.0, 5.2, 4.8, 5.1],
    })
    baseline = get_baseline(ref_df, "M01", "Cotton", min_history=8)
    assert baseline.history_count == 10
    assert baseline.source == "machine_fabric"
    assert abs(baseline.mean_waste_pct - 5.04) < 0.1
    assert baseline.std_waste_pct > 0


def test_baseline_insufficient_history_fallback_to_machine():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 5 + ["M01"] * 10,
        "fabric_type": ["Cotton"] * 5 + ["Polyester"] * 10,
        "waste_pct": [5.0, 5.2, 4.8, 5.1, 5.3] + [4.0] * 10,
    })
    baseline = get_baseline(ref_df, "M01", "Cotton", min_history=8)
    assert baseline.source == "machine"
    assert baseline.history_count == 15


def test_baseline_fallback_to_fabric():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 5,
        "fabric_type": ["Cotton"] * 5,
        "waste_pct": [5.0, 5.2, 4.8, 5.1, 5.3],
    })
    ref_df2 = pd.DataFrame({
        "machine_id": ["M02", "M03"] * 5,
        "fabric_type": ["Cotton"] * 10,
        "waste_pct": [4.5] * 10,
    })
    combined = pd.concat([ref_df, ref_df2])
    baseline = get_baseline(combined, "M01", "Cotton", min_history=8)
    assert baseline.source == "fabric"
    assert baseline.history_count == 15


def test_baseline_fallback_to_global():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 3,
        "fabric_type": ["Cotton"] * 3,
        "waste_pct": [5.0, 5.2, 4.8],
    })
    ref_df2 = pd.DataFrame({
        "machine_id": ["M02"] * 3,
        "fabric_type": ["Polyester"] * 3,
        "waste_pct": [4.0, 4.1, 3.9],
    })
    combined = pd.concat([ref_df, ref_df2])
    baseline = get_baseline(combined, "M01", "Cotton", min_history=8)
    assert baseline.source == "machine_fabric_insufficient"
    assert baseline.history_count == 3


def test_baseline_zero_std_protection():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 10,
        "fabric_type": ["Cotton"] * 10,
        "waste_pct": [5.0] * 10,
    })
    baseline = get_baseline(ref_df, "M01", "Cotton", min_history=8)
    assert baseline.std_waste_pct == 0.0
    assert baseline.mean_waste_pct == 5.0


def test_apply_baselines_to_records():
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 10,
        "fabric_type": ["Cotton"] * 10,
        "waste_pct": [5.0, 5.2, 4.8, 5.1, 5.3, 4.9, 5.0, 5.2, 4.8, 5.1],
    })
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M01", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=5, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    records[0].waste_pct = 5.0
    result = apply_baselines(records, ref_df, min_history=8)
    assert result[0].baseline_source == "machine_fabric"
    assert result[0].history_count == 10
    assert abs(result[0].baseline_waste_pct - 5.04) < 0.1


def test_apply_baselines_new_machine():
    # Only 2 Cotton records total (< 8), no machine records for M99
    # Global has 12 records (>= 8) so falls back to global
    ref_df = pd.DataFrame({
        "machine_id": ["M01"] * 10,
        "fabric_type": ["Polyester"] * 10,
        "waste_pct": [5.0] * 10,
    })
    ref_df2 = pd.DataFrame({
        "machine_id": ["M02", "M03"],
        "fabric_type": ["Cotton"] * 2,
        "waste_pct": [4.5] * 2,
    })
    combined = pd.concat([ref_df, ref_df2])
    records = [
        BatchRecord(
            batch_id="B001", machine_id="M99", fabric_type="Cotton",
            operator="OP001", shift="Morning",
            production_quantity=1000, production_speed=1000, waste_quantity=50,
            machine_age=0, last_maintenance_date="2024-11-01",
            humidity=65.0, temperature=24.0
        )
    ]
    records[0].waste_pct = 10.0
    result = apply_baselines(records, combined, min_history=8)
    # Global has sufficient history, so uses global baseline
    assert result[0].baseline_source == "global"
    assert result[0].history_count == 12
