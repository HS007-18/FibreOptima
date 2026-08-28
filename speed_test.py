import sys
from src.pipeline import FibreOptimaPipeline, process_production_data
import pandas as pd
import time

print("Loading data...")
df = pd.read_csv('data/production/historical_production.csv')
print(f"Loaded {len(df)} rows.")

pipeline = FibreOptimaPipeline(enable_rag=False)

start_time = time.time()
try:
    print("Starting process_dataframe...")
    # Process only 1000 rows to see speed
    subset = df.head(1000)
    batches, report = pipeline.process_dataframe(subset)
    print(f"Finished processing {len(batches)} batches in {time.time() - start_time:.2f} seconds.")
except Exception as e:
    import traceback
    traceback.print_exc()
