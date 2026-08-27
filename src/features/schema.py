"""Feature schema contract for FibreOptima.

Ensures strict training vs inference schema alignment.
"""

from typing import List
import pandas as pd


REQUIRED_INPUT_COLUMNS: List[str] = [
    "Batch ID",
    "Machine ID",
    "Fabric type",
    "Operator",
    "Shift",
    "Production quantity",
    "Production speed",
    "Waste quantity",
    "Machine age",
    "Last maintenance date",
    "Humidity",
    "Temperature",
]

NUMERICAL_FEATURES: List[str] = [
    "Production quantity",
    "Production speed",
    "Waste quantity",
    "Machine age",
    "Humidity",
    "Temperature",
    "Waste percentage",
    "High speed",
    "Old machine",
    "Missing humidity",
]

CATEGORICAL_FEATURES: List[str] = [
    "Fabric type",
    "Operator",
    "Shift",
]


def validate_input_schema(df: pd.DataFrame, is_training: bool = False) -> None:
    """Validate input dataframe against schema contract."""
    missing = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Feature Schema Mismatch! Missing required columns: {missing}.\n"
            f"Required schema: {REQUIRED_INPUT_COLUMNS}"
        )
