# FibreOptima — Textile Waste Intelligence System

**V1 — 24-Hour Hackathon MVP**  
Rules + Statistics + Historical Contextual Analysis

---

## Overview

FibreOptima analyzes textile production data to detect abnormal waste batches, explain contributing factors, and recommend investigation actions.

### Core Workflow
```
CSV Upload → Validation → Waste % → Historical Baseline → Context Analysis
    → Risk Engine → Explanation → Recommendation → Dashboard
```

### Risk Levels
- **NORMAL** — Waste within expected historical context
- **WARNING** — Moderate abnormality or supporting risk signals
- **HIGH RISK** — Strong abnormality and/or multiple strong signals
- **DATA ISSUE** — Record cannot be safely evaluated

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Run tests
pytest tests/ -v
```

The app will open at `http://localhost:8501`

---

## Sample Data

The repository includes:
- `data/sample/production_data.csv` — 150 synthetic historical batches
- `data/test/challenge_cases.csv` — 8 explicit edge cases for validation

---

## Challenge Cases (Hidden Tests)

| TC | Scenario | Expected |
|----|----------|----------|
| TC01 | High production (1000kg) + high absolute waste (50kg) = 5% | NOT High Risk |
| TC02 | Low production (100kg) + high waste (20kg) = 20% | HIGH RISK |
| TC03 | New machine (M99) | Fallback baseline, limited-history flag |
| TC04 | Maintenance overdue (90+ days) | Signal + explanation |
| TC05 | Missing humidity | Imputed from context + quality flag |
| TC06 | Zero production | DATA ISSUE, no crash |
| TC07 | Duplicate batch ID | Detected, no double-count |
| TC08 | Abnormal speed (z-score > 2) | Speed anomaly + explanation |

---

## Architecture

```
src/
├── ingestion/loader.py       # CSV → normalized DataFrame
├── validation/validator.py   # Data quality checks
├── features/waste.py         # Waste %, maintenance age, speed deviation
├── analytics/                # Machine, Fabric, Shift, Operator analysis
├── baseline/baseline_engine.py  # Machine+Fabric baseline + fallback hierarchy
├── risk/risk_engine.py       # Risk classification
├── explanation/explainer.py  # Human-readable WHY
├── recommendation/recommender.py # Actionable WHAT TO CHECK
├── models/schemas.py         # Data classes
└── pipeline.py               # End-to-end processing

ui/
├── dashboard.py      # Command Center (KPIs, charts)
├── batch_detail.py   # Batch Investigation
├── analytics.py      # Machine/Fabric/Shift/Operator tabs
├── data_quality.py   # Quality report
└── components.py     # Reusable UI components

config/settings.py    # All configurable thresholds
```

---

## Configuration

All thresholds in `config/settings.py`:

```python
MIN_HISTORY = 8
WARNING_Z_THRESHOLD = 1.5
HIGH_RISK_Z_THRESHOLD = 2.5
MAINTENANCE_OVERDUE_DAYS = 30
SPEED_ANOMALY_Z_THRESHOLD = 2.0
MACHINE_AGE_WARNING_YEARS = 10
```

---

## Key Principles

1. **No ML in V1** — Rules + Statistics + Historical Context only
2. **Explainable** — Every WARNING/HIGH RISK has human-readable reasons
3. **Causality-safe** — "Possible contributing factor", never "caused by"
4. **Data-resilient** — Handles duplicates, missing values, zero production, invalid data
5. **ML-ready** — Architecture allows future ML layer without redesign

---

## Dashboard Pages

1. **Command Center** — KPIs, waste trend, risk distribution, top risk machines
2. **Risk Queue** — Filterable table of all batches with risk levels
3. **Batch Investigation** — Detailed view with WHY and WHAT TO CHECK
4. **Analytics** — Machine, Fabric, Shift, Operator analysis tabs
5. **Data Quality** — Validation report with issue details

---

## Development

```bash
# Format code
ruff check --fix .
black .

# Run all tests
pytest tests/ -v

# Generate fresh synthetic data
python scripts/generate_data.py
```

---

## V2 Roadmap (Post-MVP)

When sufficient labelled historical data exists:
- Isolation Forest for unsupervised anomaly detection
- Random Forest / Gradient Boosting for supervised risk prediction
- Feature pipeline shared with V1 engine
- Decision layer combines V1 signals + ML signals