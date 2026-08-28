import os
import pandas as pd
import random
import numpy as np

def generate_test_csvs():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "downloads", "test")
    os.makedirs(output_dir, exist_ok=True)
    
    machines = [f"M{i:02d}" for i in range(1, 11)]
    fabrics = ["Cotton", "Polyester", "Nylon", "Silk", "Wool"]
    operators = [f"OP{i:02d}" for i in range(1, 6)]
    shifts = ["Morning", "Evening", "Night"]
    
    scenarios = [
        ("01_normal_operations", 10, False, False),
        ("02_high_speed_cotton", 10, True, False), # High speed, potential waste
        ("03_machine_m03_stress", 5, True, True),  # M03 high speed, high humidity
        ("04_old_machines", 8, False, False),      # Focusing on older machines
        ("05_perfect_batch", 12, False, False),    # Very low waste
        ("06_maintenance_overdue", 10, False, True),# High waste due to temperature
        ("07_synthetic_fabrics", 15, False, False),
        ("08_night_shift_anomalies", 10, True, True),
        ("09_capacity_push", 5, True, False),
        ("10_mixed_random", 20, False, False)
    ]
    
    for filename, num_rows, high_speed, extreme_env in scenarios:
        data = []
        for i in range(num_rows):
            machine = random.choice(machines)
            if "m03" in filename: machine = "M03"
            if "old" in filename: machine = random.choice(["M01", "M02", "M03"])
            if "synthetic" in filename: fabric = random.choice(["Polyester", "Nylon"])
            else: fabric = random.choice(fabrics)
            
            shift = "Night" if "night" in filename else random.choice(shifts)
            
            # Base logic
            prod_qty = random.uniform(800, 1500)
            rated_speed = 850
            
            prod_speed = random.uniform(700, rated_speed)
            if high_speed:
                prod_speed = random.uniform(rated_speed, 1100)
                
            temp = random.uniform(22, 28)
            hum = random.uniform(40, 60)
            if extreme_env:
                temp = random.uniform(30, 35)
                hum = random.uniform(70, 85)
                
            # Waste simulation
            base_waste = random.uniform(0.02, 0.08)
            if high_speed: base_waste += 0.05
            if extreme_env: base_waste += 0.07
            if fabric == "Silk": base_waste += 0.03
            
            waste_qty = prod_qty * base_waste
            
            data.append({
                "Batch ID": f"B-{filename.split('_')[0]}-{random.randint(1000, 9999)}",
                "Machine ID": machine,
                "Fabric type": fabric,
                "Operator": random.choice(operators),
                "Shift": shift,
                "Production quantity": round(prod_qty, 2),
                "Production speed": round(prod_speed, 2),
                "Waste quantity": round(waste_qty, 2),
                "Machine age": round(random.uniform(1, 15), 1),
                "Last maintenance date": "2026-01-15",
                "Humidity": round(hum, 1),
                "Temperature": round(temp, 1)
            })
            
        df = pd.DataFrame(data)
        filepath = os.path.join(output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False)
        print(f"Created: {filepath}")

if __name__ == "__main__":
    generate_test_csvs()
