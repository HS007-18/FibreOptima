import pytest
from src.legacy_v1.config.settings import SETTINGS
from src.pipeline import FibreOptimaPipeline, process_production_data, records_to_dataframe

@pytest.fixture(scope="module")
def pipeline():
    return FibreOptimaPipeline(enable_rag=False)

@pytest.fixture(scope="module")
def historical_df():
    # Only load it once
    records, report, hist_df, df, _ = process_production_data("data/production/historical_production.csv", enable_ml=False, enable_rag=False)
    return hist_df

@pytest.fixture(scope="module")
def adversarial_records(pipeline, historical_df):
    batches, report, df = pipeline.process_file("data/evaluation/adversarial_cases.csv", historical_df=historical_df)
    return batches

def test_tc01_high_production_high_absolute_waste(adversarial_records):
    tc01 = next(r for r in adversarial_records if r.record_id == "TC01_HIGH_PROD")
    assert tc01.waste_pct == 5.0

def test_tc02_low_production_high_waste_pct(adversarial_records):
    tc02 = next(r for r in adversarial_records if r.record_id == "TC02_LOW_PROD_HIGH_WASTE")
    assert tc02.waste_pct == 20.0

def test_tc03_new_machine(adversarial_records):
    tc03 = next(r for r in adversarial_records if r.record_id == "TC03_NEW_MACHINE")
    assert tc03.machine_id == "M99"

def test_tc04_maintenance_overdue(adversarial_records):
    tc04 = next(r for r in adversarial_records if r.record_id == "TC04_MAINT_OVERDUE")
    assert tc04.days_since_maintenance > SETTINGS.MAINTENANCE_OVERDUE_DAYS
    assert tc04.maintenance_signal is True

def test_tc05_missing_humidity(adversarial_records):
    tc05 = next(r for r in adversarial_records if r.record_id == "TC05_MISSING_HUMIDITY")
    assert tc05.humidity is not None
    assert tc05.humidity_imputed is True

def test_tc06_zero_production(adversarial_records):
    tc06 = next(r for r in adversarial_records if r.record_id == "TC06_ZERO_PROD")
    assert tc06.zero_production is True
    assert tc06.risk_level == "DATA ISSUE"
    assert tc06.is_valid is False

def test_tc07_duplicate_batch(adversarial_records):
    tc07 = next(r for r in adversarial_records if r.record_id == "TC07_DUPLICATE")
    assert tc07.record_id == "TC07_DUPLICATE"

def test_tc08_abnormal_speed(adversarial_records):
    tc08 = next(r for r in adversarial_records if r.record_id == "TC08_HIGH_SPEED")
    assert tc08.production_speed == 1500.0

def test_no_crash_on_invalid_data(adversarial_records):
    assert len(adversarial_records) == 8
