"""Generates synthetic textile production data for edge-case simulation testing.
Saves to data/production/synthetic_production.csv (separate from UCI proxy data).
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

num_records = 5000
batch_ids = [f"B-{i:05d}" for i in range(1, num_records + 1)]
machine_ids = [f"M-{i:02d}" for i in range(1, 11)]
fabric_types = ["Cotton", "Polyester", "Silk", "Denim", "Wool"]
operators = [f"Op-{i:02d}" for i in range(1, 21)]
shifts = ["Morning", "Evening", "Night"]

data = []
for i in range(num_records):
    b_id = batch_ids[i]
    m_id = random.choice(machine_ids)
    f_type = random.choice(fabric_types)
    op = random.choice(operators)
    sh = random.choice(shifts)
    prod_qty = np.random.uniform(500, 2000)
    prod_speed = np.random.uniform(100, 300)
    m_age = np.random.uniform(1, 15)
    last_maint = datetime.now() - timedelta(days=random.randint(1, 400))
    hum = np.random.uniform(30, 80) if random.random() > 0.05 else np.nan
    temp = np.random.uniform(20, 40)
    w_qty = prod_qty * np.random.uniform(0.01, 0.05)

    if random.random() < 0.05:
        w_qty = prod_qty * np.random.uniform(0.15, 0.30)
    if random.random() < 0.02:
        prod_qty = np.random.uniform(5000, 10000)
        w_qty = np.random.uniform(100, 200)
    if random.random() < 0.02:
        prod_qty = np.random.uniform(50, 100)
        w_qty = prod_qty * np.random.uniform(0.40, 0.60)
    if random.random() < 0.02:
        prod_speed = np.random.uniform(500, 800)
        w_qty = prod_qty * np.random.uniform(0.20, 0.40)
    if random.random() < 0.01:
        prod_qty = 0
        w_qty = 0

    data.append(
        [
            b_id,
            m_id,
            f_type,
            op,
            sh,
            prod_qty,
            prod_speed,
            w_qty,
            m_age,
            last_maint.strftime("%Y-%m-%d"),
            hum,
            temp,
        ]
    )

df = pd.DataFrame(
    data,
    columns=[
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
    ],
)

os.makedirs("data/production", exist_ok=True)
df.to_csv("data/production/synthetic_production.csv", index=False)
print("Saved synthetic dataset to data/production/synthetic_production.csv")
