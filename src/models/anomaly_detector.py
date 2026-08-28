from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from src.schema.intelligence import AnomalyIntelligencePacket
from src.features.schema import NUMERICAL_FEATURES


class TextileAnomalyDetector:
    """Isolation Forest anomaly detector for FibreOptima."""

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.feature_names_: List[str] = []
        self.raw_means_: Dict[str, float] = {}
        self.raw_stds_: Dict[str, float] = {}
        self.raw_mins_: Dict[str, float] = {}
        self.raw_maxs_: Dict[str, float] = {}
        self.fitted_categories_: Dict[str, set] = {}

    def fit(self, X_train_raw: pd.DataFrame, preprocessor) -> "TextileAnomalyDetector":
        """Fit Isolation Forest model and store raw feature baseline stats."""
        engineered = preprocessor.named_steps["engineer"].transform(X_train_raw)
        for col in NUMERICAL_FEATURES:
            self.raw_means_[col] = float(engineered[col].mean())
            self.raw_stds_[col] = float(engineered[col].std())
            self.raw_mins_[col] = float(engineered[col].min())
            self.raw_maxs_[col] = float(engineered[col].max())

        # Extract fitted categories
        cat_cols = ["Machine ID", "Fabric type", "Operator", "Shift"]
        for col in cat_cols:
            if col in X_train_raw.columns:
                self.fitted_categories_[col] = set(X_train_raw[col].dropna().unique())

        X_processed = preprocessor.fit_transform(X_train_raw)
        self.model.fit(X_processed)
        
        column_transformer = preprocessor.named_steps["preprocessor"]
        self.feature_names_ = list(column_transformer.get_feature_names_out())
        return self

    def predict(self, X_processed: np.ndarray) -> np.ndarray:
        return self.model.predict(X_processed)

    def decision_function(self, X_processed: np.ndarray) -> np.ndarray:
        return self.model.decision_function(X_processed)

    def classify_risk(self, waste_pct: float, anomaly_score: float) -> Tuple[bool, bool, str]:
        """Classify operational risk by combining ML and business rule signals."""
        ml_flag = bool(anomaly_score < -0.05)
        biz_flag = bool(waste_pct > 15.0)

        if ml_flag and biz_flag:
            return biz_flag, ml_flag, "High Risk"
        if biz_flag:
            return biz_flag, ml_flag, "Warning"
        if ml_flag:
            return biz_flag, ml_flag, "Warning"
        if waste_pct > 8.0:
            return True, ml_flag, "Warning"
        return False, ml_flag, "Normal"

    def analyze_record(
        self, raw_record: pd.DataFrame, preprocessor
    ) -> AnomalyIntelligencePacket:
        """Run ML inference, business rules, and feature attribution on a record."""
        processed_df = preprocessor.transform(raw_record)
        score = float(self.decision_function(processed_df)[0])
        is_anom = bool(self.predict(processed_df)[0] == -1)

        record_id = (
            str(raw_record["Batch ID"].iloc[0])
            if "Batch ID" in raw_record.columns
            else "UNKNOWN"
        )

        # 1. Observed Telemetry
        observed = {}
        telemetry_cols = [
            "Fabric type",
            "Production quantity",
            "Production speed",
            "Waste quantity",
            "Machine age",
            "Humidity",
            "Temperature",
            "Operator",
            "Shift",
        ]
        for col in telemetry_cols:
            if col in raw_record.columns:
                val = raw_record[col].iloc[0]
                if isinstance(val, (np.integer, int)):
                    observed[col] = int(val)
                elif isinstance(val, (np.floating, float)):
                    observed[col] = float(val) if not pd.isna(val) else None
                else:
                    observed[col] = str(val) if not pd.isna(val) else "Missing"

        prod_qty = float(raw_record["Production quantity"].iloc[0]) if "Production quantity" in raw_record.columns else 0.0
        waste_qty = float(raw_record["Waste quantity"].iloc[0]) if "Waste quantity" in raw_record.columns else 0.0
        raw_waste_pct = float((waste_qty / prod_qty) * 100.0) if prod_qty > 0 else 0.0
        observed["Waste percentage"] = raw_waste_pct

        # 2. Business Logic & ML Risk Classification
        biz_flag, ml_flag, risk_class = self.classify_risk(raw_waste_pct, score)

        # 3. Statistical Deviations & OOD Detection
        engineered_record = preprocessor.named_steps["engineer"].transform(raw_record)
        z_scores = {}
        is_ood = False
        ood_reasons = []

        for feature in NUMERICAL_FEATURES:
            val = float(engineered_record[feature].iloc[0]) if not pd.isna(engineered_record[feature].iloc[0]) else 0.0
            mean = self.raw_means_.get(feature, 0.0)
            std = self.raw_stds_.get(feature, 1.0)
            z = float((val - mean) / std) if std > 0 else 0.0
            z_scores[feature] = z

            f_min = self.raw_mins_.get(feature, -float("inf"))
            f_max = self.raw_maxs_.get(feature, float("inf"))

            if val < f_min or val > f_max:
                is_ood = True
                ood_reasons.append(f"{feature} ({val:.1f}) is outside training range [{f_min:.1f}, {f_max:.1f}]")
            elif abs(z) > 3.0:
                is_ood = True
                ood_reasons.append(f"{feature} has absolute z-score > 3.0 ({z:.2f})")

        cat_cols = ["Machine ID", "Fabric type", "Operator", "Shift"]
        for col in cat_cols:
            if col in raw_record.columns:
                val = raw_record[col].iloc[0]
                if not pd.isna(val) and col in self.fitted_categories_:
                    if val not in self.fitted_categories_[col]:
                        is_ood = True
                        ood_reasons.append(f"Unseen {col}: {val}")

        prediction_confidence = "Low" if is_ood else "High"

        # 4. Feature Contributions (Attribution via Perturbation)
        contributions = {}
        baseline_score = score
        for i, fname in enumerate(self.feature_names_):
            perturbed = processed_df.copy()
            perturbed[0][i] = 0.0  # Set to scaled mean (0.0)
            perturbed_score = float(self.decision_function(perturbed)[0])
            contributions[fname] = abs(baseline_score - perturbed_score)

        total_contrib = sum(contributions.values()) if sum(contributions.values()) > 0 else 1.0
        contributions = {k: float(v / total_contrib) for k, v in contributions.items()}

        return AnomalyIntelligencePacket(
            record_id=record_id,
            is_anomalous=is_anom,
            anomaly_score=score,
            business_rule_flag=biz_flag,
            ml_anomaly_flag=ml_flag,
            risk_class=risk_class,
            observed_telemetry=observed,
            statistical_deviations=z_scores,
            feature_contributions=contributions,
            investigation_mode="Offline Evidence Engine",
            is_ood=is_ood,
            ood_reasons=ood_reasons,
            prediction_confidence=prediction_confidence,
        )
