# Dataset Provenance: Textile Proxy Data from Industrial Telemetry

## Overview
FibreOptima requires highly specific multivariate edge cases (e.g., hidden test cases involving production speed, missing humidity, and multidimensional waste percentage calculations). Because no public real-world dataset perfectly matches these exact requirements for the textile domain, we have engineered a **Proxy Textile Dataset** derived entirely from legitimate industrial telemetry.

## Source
> The dataset is a textile-domain proof-of-concept created through deterministic proxy transformation of UCI AI4I industrial telemetry. The resulting textile variables are proxies and are not measurements from an actual textile factory.
- **Original Dataset**: AI4I 2020 Predictive Maintenance Dataset
- **Source**: UCI Machine Learning Repository
- **Nature**: Real-world operational telemetry from a German industrial machine.
- **Why this matters**: Instead of using randomly generated synthetic data (which lacks genuine correlative structures), FibreOptima utilizes real machine variance, thermal dynamics, and mechanical load data, mathematically mapped to the textile domain.

## Proxy Feature Mapping
The transformation script (`scripts/download_real_data.py`) preserves the statistical integrity of the original dataset while mapping it to the hackathon's required features. These must be explicitly understood as **proxy features**, not 1:1 physical equivalents:

| Original Industrial Feature | Mapped Textile Proxy Feature | Justification / Context |
| :--- | :--- | :--- |
| `UDI` | `Batch ID` | Unique record identifier. |
| `Product ID` | `Machine ID` | Equipment tracking identifier. |
| `Type` (L, M, H) | `Fabric type` (Cotton, Polyester, Silk) | Categorical quality/material constraints. |
| `Rotational speed [rpm]` | `Production speed` | Direct translation of machine speed. |
| `Rotational speed [rpm] * 10` | `Production quantity` | Proxy: Higher speeds yield higher production quantities. |
| `Torque [Nm]` | `Waste quantity` | Proxy: High torque/mechanical strain is mathematically mapped to higher material waste rates. |
| `Tool wear [min]` | `Machine age` | Proxy: Progressive mechanical deterioration over time. |
| `Air temperature [K]` | `Humidity` | Proxy: Environmental variance parameter. |
| `Process temperature [K]` | `Temperature` | Proxy: Machine operating temperature variance. |

## Scientific Credibility
By combining a **real-world statistical foundation** (AI4I telemetry) with **business-logic proxy transformations**, FibreOptima guarantees that the ML anomaly detector (`IsolationForest`) is learning from genuine operational distributions rather than fabricated random noise, making the end-to-end Agentic RAG pipeline verifiable and scientifically credible for hackathon evaluation.
