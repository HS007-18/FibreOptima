import pandas as pd
import json
import os
import random

# Fixed seed for reproducibility
random.seed(42)

def generate_company_data():
    data_dir = os.path.join("data", "production")
    history_file = os.path.join(data_dir, "historical_production.csv")
    
    if not os.path.exists(history_file):
        print(f"File not found: {history_file}")
        return
        
    df = pd.read_csv(history_file)
    
    machines = df['Machine ID'].unique()
    machines = sorted([m for m in machines if str(m).startswith("M")])
    
    catalog = []
    maintenance = []
    
    for m in machines:
        m_data = df[df['Machine ID'] == m]
        
        max_speed = m_data['Production speed'].max()
        max_qty = m_data['Production quantity'].max()
        
        # Rated limits are usually slightly below the historical extreme maximums 
        # or exactly at a rounded maximum. Let's make it deterministic.
        rated_speed = round(max_speed * 0.95, -1)
        rated_capacity = round(max_qty * 0.95, -1)
        
        install_year = 2020 + (int(m.replace("M", "")) % 4)
        
        catalog.append({
            "machine_id": m,
            "machine_type": "Textile Loom" if int(m.replace("M", "")) % 2 == 0 else "Spinning Frame",
            "rated_capacity": float(rated_capacity),
            "rated_speed": float(rated_speed),
            "installation_date": f"{install_year}-01-15",
            "status": "Operational"
        })
        
        # Deterministic maintenance issues
        days_ago = random.randint(10, 200)
        issues = ["Bearing inspection", "Belt replacement", "Routine service", "Sensor calibration", "Motor alignment"]
        issue = issues[int(m.replace("M", "")) % len(issues)]
        
        maintenance.append({
            "machine_id": m,
            "maintenance_date": f"{days_ago} days ago",
            "days_ago": days_ago,
            "maintenance_type": "Preventive" if days_ago % 2 == 0 else "Corrective",
            "issue": issue,
            "note": "SIMULATED COMPANY DATA"
        })
        
    with open(os.path.join(data_dir, "machine_catalog.json"), "w") as f:
        json.dump(catalog, f, indent=2)
        
    with open(os.path.join(data_dir, "maintenance_log.json"), "w") as f:
        json.dump(maintenance, f, indent=2)
        
    print(f"Generated data for {len(machines)} machines.")

if __name__ == "__main__":
    generate_company_data()
