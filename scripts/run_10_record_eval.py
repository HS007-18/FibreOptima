import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import FibreOptimaPipeline

def run_evaluation():
    csv_dir = "downloads/test"
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    csv_files.sort()
    
    pipeline = FibreOptimaPipeline()
    
    print("| Batch | Predicted Waste | Anomaly | OOD | Confidence | OOD Reasons |")
    print("| ----- | --------------: | ------- | --- | ---------- | ----------- |")
    
    for filename in csv_files:
        filepath = os.path.join(csv_dir, filename)
        try:
            batches, _, _ = pipeline.process_file(filepath)
            for b in batches:
                # Truncate reasons for table readability
                reasons = "<br>".join(b.ood_reasons)
                if len(reasons) > 80:
                    reasons = reasons[:77] + "..."
                if not reasons:
                    reasons = "-"
                    
                print(f"| {b.record_id} | {b.predicted_waste_pct:.1f}% | {b.is_anomalous} | {b.is_ood} | {b.prediction_confidence} | {reasons} |")
        except Exception as e:
            print(f"| Error in {filename} | - | - | - | - | {e} |")

if __name__ == "__main__":
    run_evaluation()
