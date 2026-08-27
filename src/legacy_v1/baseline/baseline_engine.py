import numpy as np
import pandas as pd

from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.models.schemas import BaselineResult


def get_baseline(
    reference_df: pd.DataFrame,
    machine_id: str,
    fabric_type: str,
    min_history: int = None
) -> BaselineResult:
    if min_history is None:
        min_history = SETTINGS.MIN_HISTORY

    if reference_df is None or reference_df.empty:
        return BaselineResult(0.0, 0.0, 0.0, 0, "none", primary_available=False)

    valid_df = reference_df[reference_df["waste_pct"] > 0]

    mf_df = valid_df[
        (valid_df["machine_id"] == machine_id) &
        (valid_df["fabric_type"] == fabric_type)
    ]

    primary_available = len(mf_df) >= min_history

    if primary_available:
        return _compute_baseline(mf_df["waste_pct"], "machine_fabric", primary_available=True)

    m_df = valid_df[
        (valid_df["machine_id"] == machine_id)
    ]

    if len(m_df) >= min_history:
        return _compute_baseline(m_df["waste_pct"], "machine", primary_available=False)

    f_df = valid_df[
        (valid_df["fabric_type"] == fabric_type)
    ]

    if len(f_df) >= min_history:
        return _compute_baseline(f_df["waste_pct"], "fabric", primary_available=False)

    g_df = valid_df
    if len(g_df) >= min_history:
        return _compute_baseline(g_df["waste_pct"], "global", primary_available=False)

    if len(mf_df) > 0:
        return _compute_baseline(mf_df["waste_pct"], "machine_fabric_insufficient", primary_available=False)
    if len(m_df) > 0:
        return _compute_baseline(m_df["waste_pct"], "machine_insufficient", primary_available=False)
    if len(f_df) > 0:
        return _compute_baseline(f_df["waste_pct"], "fabric_insufficient", primary_available=False)
    if len(g_df) > 0:
        return _compute_baseline(g_df["waste_pct"], "global_insufficient", primary_available=False)

    return BaselineResult(0.0, 0.0, 0.0, 0, "none", primary_available=False)


def _compute_baseline(waste_series: pd.Series, source: str, primary_available: bool = False) -> BaselineResult:
    mean_val = waste_series.mean()
    std_val = waste_series.std(ddof=0)
    median_val = waste_series.median()
    count = len(waste_series)

    if std_val == 0 or np.isnan(std_val):
        std_val = 0.0

    return BaselineResult(
        mean_waste_pct=float(mean_val),
        std_waste_pct=float(std_val),
        median_waste_pct=float(median_val),
        history_count=count,
        source=source,
        primary_available=primary_available
    )


def apply_baselines(records: list, reference_df: pd.DataFrame, min_history: int = None) -> list:
    for record in records:
        if not record.is_valid or record.risk_level == "DATA ISSUE":
            continue

        baseline = get_baseline(reference_df, record.machine_id, record.fabric_type, min_history)

        record.baseline_waste_pct = baseline.mean_waste_pct
        record.baseline_source = baseline.source
        record.history_count = baseline.history_count
        record.waste_deviation = record.waste_pct - baseline.mean_waste_pct

        if baseline.std_waste_pct > 0:
            record.waste_z_score = record.waste_deviation / baseline.std_waste_pct
        else:
            record.waste_z_score = None

        # Limited history if primary machine+fabric baseline was NOT available
        if not baseline.primary_available:
            record.limited_history = True

    return records
