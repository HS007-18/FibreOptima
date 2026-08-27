# Data Architecture

## Overview
FibreOptima is designed to detect abnormal industrial operating patterns from real production-machine data, statistically contextualize the anomaly, retrieve relevant technical knowledge using Agentic RAG, and produce an evidence-backed investigation. 

This architecture maintains a strict boundary between operational ML data and the knowledge corpus.

## Architectural Layers

```text
REAL AI4I DATA
      │
      ├── Operational features
      │     ├─ Rotational speed
      │     ├─ Torque
      │     ├─ Temperatures (Air/Process)
      │     ├─ Tool wear
      │     └─ Product type
      │
      ▼
VALIDATION LAYER
      │ (Ensures data schema correctness without hallucinating missing fields)
      ▼
FEATURE ENGINEERING
      │ (Scales features, computes derivations, strictly prevents label leakage)
      ▼
STATISTICAL CONTEXT
      │ (Maintains baseline distributions of historical production data)
      ▼
LOCAL ML ANOMALY MODEL
      │ (Unsupervised/Semi-supervised anomaly detection, e.g., Isolation Forest)
      ▼
ANOMALY SCORE + FEATURE CONTRIBUTIONS
      │
      ├─────────────────────┐
      ▼                     ▼
STATISTICAL EVIDENCE     AGENTIC RAG
                          │
                    SOPs / Manuals /
                    Maintenance /
                    Process Knowledge
                          │
                          ▼
                    AI INVESTIGATION
                          │
                          ▼
                 FINAL EXPLANATION
                 + Evidence
                 + Recommendation
```

### 1. Data Layer
The base of the system, consuming real external datasets.
- **Production Data (`data/production/historical_production.csv`)**: 80% of the AI4I dataset used to build baselines and train unsupervised ML models.
- **Evaluation Data (`data/evaluation/stratified_evaluation.csv`)**: 20% of the AI4I dataset, used *only* for the final evaluation of the model pipeline. Never used to fit scalers or train the model.

### 2. Feature Layer
Extracts variables relevant to industrial anomaly detection without fabricating data.
- **Used Variables**: Product Type, Air Temperature, Process Temperature, Rotational Speed, Torque, Tool Wear.
- **Excluded Variables**: Machine Failure (Reserved entirely for the Evaluation Layer).

### 3. Statistical Intelligence
Provides the mathematical context (mean, std dev, quantiles) for normal operations, serving as the first-order contextual layer before ML.

### 4. ML Intelligence
A local, GPU-capable anomaly detection model.
- **Model**: Local anomaly detection (e.g., Isolation Forest, Autoencoder, or One-Class SVM).
- **Purpose**: Identifies multidimensional operational feature combinations that are mathematically anomalous, outputting an Anomaly Score.

### 5. RAG Knowledge Layer
An independent corpus of documents completely separated from the ML training data.
- **Corpus Contents**: Maintenance manuals, operating procedures, theoretical parameters.
- **Engine**: A vector index queried by the Agent based on the specific variables flagged by the ML model.

### 6. Agent Reasoning Layer
The Agent acts as the final investigator. It strictly distinguishes between:
- **OBSERVED**: What the telemetry actually reports.
- **STATISTICAL**: How unusual the observation is based on historical baselines.
- **ML**: Whether the specific multidimensional combination is anomalous.
- **RAG EVIDENCE**: Technical documentation retrieved based on the anomaly features.
- **INFERENCE**: Synthesizing the above into a human-readable conclusion without inventing causal links.
