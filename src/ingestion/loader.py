import numpy as np
import pandas as pd

from src.legacy_v1.config.settings import SETTINGS
from src.legacy_v1.models.schemas import BatchRecord


def load_and_normalize_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip()

    df = df.rename(columns=SETTINGS.COLUMN_ALIASES)

    missing_cols = set(SETTINGS.REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    for col in SETTINGS.NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "last_maintenance_date" in df.columns:
        df["last_maintenance_date"] = pd.to_datetime(
            df["last_maintenance_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    string_cols = ["batch_id", "machine_id", "fabric_type", "operator", "shift"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


import pydantic
from src.legacy_v1.schema.contracts import BatchRecordContract

def dataframe_to_records(df: pd.DataFrame) -> list[BatchRecord]:
    records = []
    for _, row in df.iterrows():
        humidity_val = row.get("humidity", np.nan)
        temp_val = row.get("temperature", np.nan)
        
        try:
            contract = BatchRecordContract(
                batch_id=str(row.get("batch_id", "")),
                machine_id=str(row.get("machine_id", "")),
                fabric_type=str(row.get("fabric_type", "")),
                operator=str(row.get("operator", "")),
                shift=str(row.get("shift", "")),
                production_quantity=float(row.get("production_quantity", 0.0) if pd.notna(row.get("production_quantity")) else 0.0),
                production_speed=float(row.get("production_speed", 0.0) if pd.notna(row.get("production_speed")) else 0.0),
                waste_quantity=float(row.get("waste_quantity", 0.0) if pd.notna(row.get("waste_quantity")) else 0.0),
                machine_age=float(row.get("machine_age", 0.0) if pd.notna(row.get("machine_age")) else 0.0),
                last_maintenance_date=str(row.get("last_maintenance_date", "")),
                humidity=float(humidity_val) if pd.notna(humidity_val) else None,
                temperature=float(temp_val) if pd.notna(temp_val) else None,
            )
            record = contract.to_v1_record()
        except (pydantic.ValidationError, ValueError) as e:
            # Fallback if types are completely broken (e.g. string in float column)
            record = BatchRecord(
                batch_id=str(row.get("batch_id", "")),
                machine_id=str(row.get("machine_id", "")),
                fabric_type=str(row.get("fabric_type", "")),
                operator=str(row.get("operator", "")),
                shift=str(row.get("shift", "")),
                production_quantity=row.get("production_quantity", 0.0),
                production_speed=row.get("production_speed", 0.0),
                waste_quantity=row.get("waste_quantity", 0.0),
                machine_age=row.get("machine_age", 0.0),
                last_maintenance_date=str(row.get("last_maintenance_date", "")),
                humidity=humidity_val if pd.notna(humidity_val) else None,
                temperature=temp_val if pd.notna(temp_val) else None,
            )
            # The existing V1 validation layer will likely catch it and flag it,
            # but we can also pre-flag it here.
            record.is_valid = False
            record.invalid_value = True
            record.risk_level = "DATA ISSUE"
            record.data_quality_reason = f"Schema error: {str(e)[:100]}"
            
        records.append(record)
    return records



def load_production_data(file_path: str) -> list[BatchRecord]:
    df = load_and_normalize_csv(file_path)
    return dataframe_to_records(df)
