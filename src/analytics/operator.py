import pandas as pd

from src.legacy_v1.models.schemas import BatchRecord


def analyze_operator(records: list[BatchRecord]) -> pd.DataFrame:
    valid_records = [r for r in records if r.is_valid and r.risk_level != "DATA ISSUE"]
    if not valid_records:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "operator": r.operator,
        "waste_pct": r.waste_pct,
        "risk_level": r.risk_level,
    } for r in valid_records])

    agg = df.groupby("operator").agg(
        batch_count=("waste_pct", "count"),
        avg_waste_pct=("waste_pct", "mean"),
        high_risk_count=("risk_level", lambda x: (x == "HIGH RISK").sum()),
        warning_count=("risk_level", lambda x: (x == "WARNING").sum()),
        normal_count=("risk_level", lambda x: (x == "NORMAL").sum()),
    ).reset_index()

    agg["avg_waste_pct"] = agg["avg_waste_pct"].round(2)
    return agg
