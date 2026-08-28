import os
import sys
import pandas as pd

sys.path.append(os.path.abspath('.'))
from src.pipeline import FibreOptimaPipeline
from src.database.company_db import CompanyDatabase

# Output Directories
dirs = [
    os.path.abspath('downloads/test'),
    os.path.expanduser('~/Downloads/test')
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

db = CompanyDatabase()
pipeline = FibreOptimaPipeline(enable_ml=True, enable_rag=False, company_db=db)

# Base list of 10 machines
base_machines = [f"M{i:02d}" for i in range(1, 11)]

def make_10_machine_rows(overrides_fn):
    rows = []
    for idx, m_id in enumerate(base_machines):
        row = {
            "Batch ID": f"B-{m_id}-{100 + idx}",
            "Machine ID": m_id,
            "Fabric type": ["Cotton", "Polyester", "Nylon", "Silk", "Wool"][idx % 5],
            "Operator": f"OP0{(idx % 5) + 1}",
            "Shift": ["Morning", "Evening", "Night"][idx % 3],
            "Production quantity": 1400.0,
            "Production speed": 1200.0,
            "Waste quantity": 45.0,
            "Machine age": 4.5,
            "Last maintenance date": "2026-01-15",
            "Humidity": 70.0,
            "Temperature": 26.0
        }
        # Apply scenario override per row
        row = overrides_fn(row, idx, m_id)
        rows.append(row)
    return rows

# Define 10 Scenarios (Each containing ALL 10 Machines M01-M10)
scenarios = []

# 1. Standard Factory Operations
def s1(row, idx, m_id):
    return row
scenarios.append(("01_factory_standard_baseline.csv", "Standard Factory Operations (In-Distribution Normal)", s1))

# 2. TC1: High Production with High Absolute Waste (Normal %)
def s2(row, idx, m_id):
    row["Production quantity"] = 1600.0
    row["Waste quantity"] = 64.0  # Exactly 4.0% waste
    return row
scenarios.append(("02_tc1_high_prod_high_abs_waste.csv", "TC1: High Production + High Absolute Waste (Normal %)", s2))

# 3. TC2: Low Production with High Waste %
def s3(row, idx, m_id):
    if idx < 3:
        row["Production quantity"] = 200.0
        row["Waste quantity"] = 100.0  # 50% waste!
    return row
scenarios.append(("03_tc2_low_prod_high_waste_pct.csv", "TC2: Low Production + High Waste % (High Risk)", s3))

# 4. TC3: Unseen / New Machine ID
def s4(row, idx, m_id):
    if idx == 0:
        row["Machine ID"] = "M99"
        row["Batch ID"] = "B-M99-100"
    return row
scenarios.append(("04_tc3_new_unseen_machines.csv", "TC3: Unseen Machine ID M99 (Fallback Baselines)", s4))

# 5. TC4: Maintenance Overdue Fleet
def s5(row, idx, m_id):
    if m_id in ["M01", "M04", "M09"]:
        row["Last maintenance date"] = "2024-09-01"  # > 150 days overdue
    return row
scenarios.append(("05_tc4_maintenance_overdue_fleet.csv", "TC4: Overdue Maintenance Fleet (> 150 Days)", s5))

# 6. TC5: Missing Humidity Telemetry
def s6(row, idx, m_id):
    if idx % 2 == 0:
        row["Humidity"] = None
    return row
scenarios.append(("06_tc5_missing_humidity_telemetry.csv", "TC5: Missing Humidity Telemetry (KNN Imputation)", s6))

# 7. TC6: Zero Production (Data Issue)
def s7(row, idx, m_id):
    if idx == 5:
        row["Production quantity"] = 0.0
        row["Production speed"] = 0.0
        row["Waste quantity"] = 15.0
    return row
scenarios.append(("07_tc6_zero_production_data_issues.csv", "TC6: Zero Production Quantity (Data Issue Guard)", s7))

# 8. TC7: Duplicate Batch Records
def s8(row, idx, m_id):
    if idx == 3:
        row["Batch ID"] = "B-M01-100"  # Duplicate of Row 1
    return row
scenarios.append(("08_tc7_duplicate_batch_records.csv", "TC7: Duplicate Batch Record IDs (Validation Warning)", s8))

# 9. TC8: Extreme Speed OOD
def s9(row, idx, m_id):
    if idx % 3 == 0:
        row["Production speed"] = 3500.0  # OOD > 2886 RPM limit
        row["Humidity"] = 88.0
    return row
scenarios.append(("09_tc8_extreme_speed_ood.csv", "TC8: Abnormally High Production Speed (OOD Safety Alert)", s9))

# 10. Capacity Overload Fleet
def s10(row, idx, m_id):
    row["Production quantity"] = 2100.0  # Rated capacity 1800 -> 116.7% util
    return row
scenarios.append(("10_factory_capacity_overload.csv", "Capacity Overload Fleet (> 100% Rated Utilization)", s10))


print("=================================================================")
print("GENERATING 10 TEST CSV FILES (EACH CONTAINING ALL 10 MACHINES)")
print("=================================================================")

summary_report = []

for filename, desc, overrides_fn in scenarios:
    rows = make_10_machine_rows(overrides_fn)
    df = pd.DataFrame(rows)
    
    # Save to both target directories
    for d in dirs:
        filepath = os.path.join(d, filename)
        df.to_csv(filepath, index=False)
        
    # Process through pipeline to verify expected output
    batches, _ = pipeline.process_dataframe(df)
    
    normal_c = sum(1 for b in batches if b.risk_level == "NORMAL")
    warn_c   = sum(1 for b in batches if b.risk_level == "WARNING")
    high_c   = sum(1 for b in batches if b.risk_level == "HIGH RISK")
    issue_c  = sum(1 for b in batches if b.risk_level == "DATA ISSUE")
    ood_c    = sum(1 for b in batches if getattr(b, "is_ood", False))
    anom_c   = sum(1 for b in batches if getattr(b, "ml_flag", False))
    
    valid_waste = [b.waste_pct for b in batches if b.waste_pct is not None and b.risk_level != "DATA ISSUE"]
    avg_w = (sum(valid_waste) / len(valid_waste)) if valid_waste else 0.0
    
    summary_report.append({
        "file": filename,
        "desc": desc,
        "total_rows": len(rows),
        "machines": ", ".join(sorted(list({r['Machine ID'] for r in rows}))),
        "normal": normal_c,
        "warning": warn_c,
        "high_risk": high_c,
        "data_issue": issue_c,
        "ood_count": ood_c,
        "anom_count": anom_c,
        "avg_waste_pct": round(avg_w, 2)
    })
    
    print(f"\nSaved: {filename}")
    print(f"   Scenario: {desc}")
    print(f"   Machines Included ({len(rows)} rows): {', '.join(sorted(list({r['Machine ID'] for r in rows})))}")
    print(f"   Pipeline Output: Normal={normal_c}, Warning={warn_c}, High Risk={high_c}, Data Issue={issue_c}, OOD={ood_c}, Avg Waste={avg_w:.2f}%")

# Print complete summary to console
print("\n" + "=" * 65)
print("10 TEST CSV FILES CREATED SUCCESSFULLY IN downloads/test/")
print("=" * 65)
