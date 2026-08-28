import pandas as pd
import random
import os

os.makedirs(os.path.join("downloads", "test"), exist_ok=True)

machines = [f"M{i:02d}" for i in range(1, 11)]
fabrics = ["Cotton", "Polyester", "Nylon", "Silk", "Wool"]
operators = [f"OP{i:02d}" for i in range(1, 6)]
shifts = ["Morning", "Evening", "Night"]

data = []
# Generate 9 valid records
for i in range(9):
    data.append({
        "Batch ID": f"B-DEMO-00{i+1}",
        "Machine ID": random.choice(machines),
        "Fabric type": random.choice(fabrics),
        "Operator": random.choice(operators),
        "Shift": random.choice(shifts),
        "Production quantity": round(random.uniform(900, 1500), 2),
        "Production speed": round(random.uniform(700, 1100), 2),
        "Waste quantity": round(random.uniform(10, 100), 2),
        "Machine age": round(random.uniform(1, 15), 1),
        "Last maintenance date": "2026-01-15",
        "Humidity": round(random.uniform(40, 60), 1),
        "Temperature": round(random.uniform(22, 28), 1)
    })

# Generate 1 DATA ISSUE record with unknown machine
data.append({
    "Batch ID": f"B-DEMO-010",
    "Machine ID": "M-101",
    "Fabric type": random.choice(fabrics),
    "Operator": random.choice(operators),
    "Shift": random.choice(shifts),
    "Production quantity": round(random.uniform(900, 1500), 2),
    "Production speed": round(random.uniform(700, 1100), 2),
    "Waste quantity": round(random.uniform(10, 100), 2),
    "Machine age": round(random.uniform(1, 15), 1),
    "Last maintenance date": "2026-01-15",
    "Humidity": round(random.uniform(40, 60), 1),
    "Temperature": round(random.uniform(22, 28), 1)
})

df = pd.DataFrame(data)
df.to_csv(os.path.join("downloads", "test", "11_final_demo.csv"), index=False)
print("Created downloads/test/11_final_demo.csv")
