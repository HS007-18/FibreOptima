"""Downloads UCI AI4I 2020 Predictive Maintenance dataset and applies deterministic proxy transformations to create the FibreOptima proxy production dataset.

Methodology:
- Source: UCI Machine Learning Repository (AI4I 2020 Predictive Maintenance Dataset)
- Deterministic Proxy Mappings:
  - Rotational speed [rpm] -> Production speed & Production quantity proxy
  - Torque [Nm] -> Waste quantity proxy
  - Tool wear [min] -> Machine age proxy
  - Air temperature [K] -> Humidity proxy
  - Process temperature [K] -> Temperature proxy
"""

import os
import urllib.request
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

UCI_DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
RAW_DATA_PATH = "data/production/ai4i_raw.csv"
HISTORICAL_DATA_PATH = "data/production/historical_production.csv"


def download_and_prepare():
    os.makedirs("data/production", exist_ok=True)
    if not os.path.exists(RAW_DATA_PATH):
        logger.info(f"Downloading raw dataset from {UCI_DATASET_URL}...")
        urllib.request.urlretrieve(UCI_DATASET_URL, RAW_DATA_PATH)
        logger.info(f"Saved raw dataset to {RAW_DATA_PATH}")
    else:
        logger.info(f"Raw dataset already exists at {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df)} raw records.")

    df["Batch ID"] = df["UDI"].astype(str)
    df["Machine ID"] = "M" + (df["UDI"] % 10 + 1).astype(str).str.zfill(2)
    df["Fabric type"] = df["Type"].map({"L": "Cotton", "M": "Polyester", "H": "Blended"})
    df["Operator"] = "OP" + (df["UDI"] % 20 + 1).astype(str).str.zfill(2)
    df["Shift"] = df["UDI"].apply(lambda x: ["Morning", "Evening", "Night"][x % 3])
    df["Production quantity"] = df["Rotational speed [rpm]"] * 0.7
    df["Production speed"] = df["Rotational speed [rpm]"]
    df["Waste quantity"] = (df["Torque [Nm]"] ** 2) / 15.0
    df["Machine age"] = df["Tool wear [min]"] / 20.0
    
    # Deterministic dates in the past
    base_date = pd.to_datetime("2026-01-01")
    df["Last maintenance date"] = df["UDI"].apply(
        lambda x: (base_date - pd.Timedelta(days=(x * 7) % 365)).strftime("%Y-%m-%d")
    )
    
    df["Humidity"] = df["Air temperature [K]"] - 230.0
    df["Temperature"] = df["Process temperature [K]"] - 280.0

    final_df = df[
        [
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
            "Machine failure",
        ]
    ]

    final_df.to_csv(HISTORICAL_DATA_PATH, index=False)
    logger.info(f"Saved {len(final_df)} proxy textile records to {HISTORICAL_DATA_PATH}")


if __name__ == "__main__":
    download_and_prepare()
