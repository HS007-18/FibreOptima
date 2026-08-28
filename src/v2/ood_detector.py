"""Out-Of-Distribution (OOD) Detector — V2.

Identifies operational values that fall outside the learned distribution bounds.
Operates completely independently from ML prediction and IsolationForest anomaly detection.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class OODDetector:
    def __init__(self, artifacts_dir: str = "models/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.stats: Dict[str, Any] = {}
        self.is_fitted = False
        
        # If artifact exists, load it
        self.metadata_path = os.path.join(self.artifacts_dir, "ood_metadata.json")
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                data = json.load(f)
                self.stats = data.get("statistics", {})
                self.is_fitted = True

    def fit(self, df: pd.DataFrame, num_cols: List[str], cat_cols: List[str]):
        """Fit OOD boundaries based strictly on training data."""
        self.stats = {
            "numerical": {},
            "categorical": {}
        }
        
        for col in num_cols:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(series) > 0:
                    self.stats["numerical"][col] = {
                        "min": float(series.min()),
                        "max": float(series.max()),
                        "mean": float(series.mean()),
                        "std": float(series.std()),
                    }
                    
        for col in cat_cols:
            if col in df.columns:
                unique_vals = df[col].dropna().unique().tolist()
                self.stats["categorical"][col] = unique_vals
                
        self.is_fitted = True

    def save(self):
        """Save statistics to artifact directory."""
        if not self.is_fitted:
            raise ValueError("OODDetector is not fitted.")
            
        os.makedirs(self.artifacts_dir, exist_ok=True)
        data = {
            "version": "1.0",
            "statistics": self.stats
        }
        with open(self.metadata_path, "w") as f:
            json.dump(data, f, indent=2)

    def detect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect if input dataframe rows are OOD.
        
        Currently assumes a single-row DataFrame for pipeline integration, 
        or processes the first row if multiple.
        """
        if not self.is_fitted:
            return {"is_ood": False, "ood_reasons": [], "prediction_confidence": "High"}
            
        if df.empty:
            return {"is_ood": False, "ood_reasons": [], "prediction_confidence": "High"}
            
        row = df.iloc[0]
        reasons = []
        
        # Check numerical bounds
        num_stats = self.stats.get("numerical", {})
        for col, stats in num_stats.items():
            if col in row and pd.notna(row[col]):
                val = float(row[col])
                c_min = stats["min"]
                c_max = stats["max"]
                c_mean = stats["mean"]
                c_std = stats["std"]
                
                # Check Min/Max
                if val < c_min or val > c_max:
                    reasons.append(f"{col} {val} is outside training range [{c_min}, {c_max}]")
                else:
                    # Check Z-score
                    if c_std > 0:
                        z_score = abs(val - c_mean) / c_std
                        if z_score > 3.0:
                            reasons.append(f"{col} {val} has z-score {z_score:.2f} (> 3.0)")
                            
        # Check categorical bounds
        cat_stats = self.stats.get("categorical", {})
        for col, allowed_vals in cat_stats.items():
            if col in row and pd.notna(row[col]):
                val = str(row[col])
                if val not in allowed_vals:
                    reasons.append(f"Unknown {col} '{val}'; not present in training data")
                    
        is_ood = len(reasons) > 0
        confidence = "Low" if is_ood else "High"
        
        return {
            "is_ood": is_ood,
            "ood_reasons": reasons,
            "prediction_confidence": confidence
        }
