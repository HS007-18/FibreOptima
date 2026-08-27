import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.settings import SETTINGS


def generate_synthetic_data(n_batches: int = 150, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)

    machines = [f"M{str(i).zfill(2)}" for i in range(1, 11)]
    fabrics = ["Cotton", "Polyester", "Blend", "Wool", "Silk"]
    operators = [f"OP{str(i).zfill(3)}" for i in range(1, 21)]
    shifts = ["Morning", "Evening", "Night"]

    base_waste_rates = {
        ("M01", "Cotton"): 4.2,
        ("M01", "Polyester"): 3.8,
        ("M02", "Cotton"): 5.1,
        ("M02", "Blend"): 4.5,
        ("M03", "Wool"): 6.2,
        ("M03", "Silk"): 7.8,
        ("M04", "Cotton"): 3.9,
        ("M04", "Polyester"): 3.5,
        ("M05", "Blend"): 4.8,
        ("M06", "Cotton"): 5.5,
        ("M07", "Cotton"): 6.1,
        ("M08", "Polyester"): 3.2,
        ("M09", "Wool"): 5.9,
        ("M10", "Silk"): 8.1,
    }

    machine_speeds = {
        "M01": 1000, "M02": 950, "M03": 1100, "M04": 1050,
        "M05": 900, "M06": 1150, "M07": 1080, "M08": 980,
        "M09": 1020, "M10": 1200,
    }

    data = []
    start_date = datetime(2024, 1, 1)

    for i in range(n_batches):
        machine = np.random.choice(machines)
        fabric = np.random.choice(fabrics)

        base_rate = base_waste_rates.get((machine, fabric), 5.0)
        noise = np.random.normal(0, 1.2)
        waste_pct = max(0.5, base_rate + noise)

        prod_qty = np.random.lognormal(6.5, 0.5)
        prod_qty = int(np.clip(prod_qty, 50, 2000))

        waste_qty = int(prod_qty * waste_pct / 100)

        speed = machine_speeds[machine] + np.random.normal(0, 50)
        speed = max(500, int(speed))

        machine_age = np.random.randint(0, 15)

        maint_days_ago = np.random.randint(1, 90)
        last_maint = start_date + timedelta(days=i * 2) - timedelta(days=maint_days_ago)

        humidity = np.clip(np.random.normal(65, 10), 30, 95)
        temp = np.clip(np.random.normal(24, 3), 15, 35)

        data.append({
            "Batch ID": f"B{str(1000 + i).zfill(4)}",
            "Machine ID": machine,
            "Fabric Type": fabric,
            "Operator": np.random.choice(operators),
            "Shift": np.random.choice(shifts),
            "Production Quantity": prod_qty,
            "Production Speed": speed,
            "Waste Quantity": waste_qty,
            "Machine Age": machine_age,
            "Last Maintenance Date": last_maint.strftime("%Y-%m-%d"),
            "Humidity": round(humidity, 1),
            "Temperature": round(temp, 1),
        })

    df = pd.DataFrame(data)

    df.loc[5, "Batch ID"] = df.loc[3, "Batch ID"]
    df.loc[10, "Production Quantity"] = 0
    df.loc[10, "Waste Quantity"] = 15
    df.loc[15, "Humidity"] = np.nan
    df.loc[20, "Humidity"] = -5
    df.loc[25, "Waste Quantity"] = -10
    df.loc[30, "Machine Age"] = -2

    return df


def generate_challenge_cases() -> pd.DataFrame:
    cases = [
        {
            "Batch ID": "TC01_HIGH_PROD",
            "Machine ID": "M01",
            "Fabric Type": "Cotton",
            "Operator": "OP001",
            "Shift": "Morning",
            "Production Quantity": 1000,
            "Production Speed": 1000,
            "Waste Quantity": 50,
            "Machine Age": 5,
            "Last Maintenance Date": "2024-11-15",
            "Humidity": 65.0,
            "Temperature": 24.0,
        },
        {
            "Batch ID": "TC02_LOW_PROD_HIGH_WASTE",
            "Machine ID": "M02",
            "Fabric Type": "Polyester",
            "Operator": "OP002",
            "Shift": "Evening",
            "Production Quantity": 100,
            "Production Speed": 950,
            "Waste Quantity": 20,
            "Machine Age": 3,
            "Last Maintenance Date": "2024-11-20",
            "Humidity": 60.0,
            "Temperature": 23.0,
        },
        {
            "Batch ID": "TC03_NEW_MACHINE",
            "Machine ID": "M99",
            "Fabric Type": "Cotton",
            "Operator": "OP003",
            "Shift": "Night",
            "Production Quantity": 500,
            "Production Speed": 1100,
            "Waste Quantity": 45,
            "Machine Age": 0,
            "Last Maintenance Date": "2024-12-01",
            "Humidity": 70.0,
            "Temperature": 25.0,
        },
        {
            "Batch ID": "TC04_MAINT_OVERDUE",
            "Machine ID": "M03",
            "Fabric Type": "Wool",
            "Operator": "OP004",
            "Shift": "Morning",
            "Production Quantity": 800,
            "Production Speed": 1100,
            "Waste Quantity": 95,
            "Machine Age": 8,
            "Last Maintenance Date": "2024-09-01",
            "Humidity": 75.0,
            "Temperature": 26.0,
        },
        {
            "Batch ID": "TC05_MISSING_HUMIDITY",
            "Machine ID": "M04",
            "Fabric Type": "Cotton",
            "Operator": "OP005",
            "Shift": "Evening",
            "Production Quantity": 1200,
            "Production Speed": 1050,
            "Waste Quantity": 55,
            "Machine Age": 4,
            "Last Maintenance Date": "2024-11-10",
            "Humidity": np.nan,
            "Temperature": 24.0,
        },
        {
            "Batch ID": "TC06_ZERO_PROD",
            "Machine ID": "M05",
            "Fabric Type": "Blend",
            "Operator": "OP006",
            "Shift": "Night",
            "Production Quantity": 0,
            "Production Speed": 0,
            "Waste Quantity": 10,
            "Machine Age": 6,
            "Last Maintenance Date": "2024-10-15",
            "Humidity": 68.0,
            "Temperature": 22.0,
        },
        {
            "Batch ID": "TC07_DUPLICATE",
            "Machine ID": "M06",
            "Fabric Type": "Cotton",
            "Operator": "OP007",
            "Shift": "Morning",
            "Production Quantity": 600,
            "Production Speed": 1150,
            "Waste Quantity": 35,
            "Machine Age": 7,
            "Last Maintenance Date": "2024-11-01",
            "Humidity": 72.0,
            "Temperature": 25.0,
        },
        {
            "Batch ID": "TC08_HIGH_SPEED",
            "Machine ID": "M07",
            "Fabric Type": "Cotton",
            "Operator": "OP008",
            "Shift": "Evening",
            "Production Quantity": 700,
            "Production Speed": 1500,
            "Waste Quantity": 65,
            "Machine Age": 5,
            "Last Maintenance Date": "2024-11-25",
            "Humidity": 80.0,
            "Temperature": 27.0,
        },
    ]
    return pd.DataFrame(cases)


if __name__ == "__main__":
    import os
    os.makedirs("data/production", exist_ok=True)
    os.makedirs("data/evaluation", exist_ok=True)

    print("Generating synthetic production data...")
    hist_df = generate_synthetic_data(150)
    hist_df.to_csv("data/production/historical_production.csv", index=False)
    print(f"Generated {len(hist_df)} historical batches -> data/production/historical_production.csv")

    # Generate holdout
    print("Generating temporal holdout...")
    holdout_df = generate_synthetic_data(50, seed=100)
    holdout_df.to_csv("data/evaluation/temporal_holdout.csv", index=False)

    print("Generating challenge cases...")
    challenge_df = generate_challenge_cases()
    challenge_df.to_csv("data/evaluation/adversarial_cases.csv", index=False)
    print(f"Generated {len(challenge_df)} challenge cases -> data/evaluation/adversarial_cases.csv")