from src.pipeline import process_production_data
batches, report, df, hist_df, _ = process_production_data('data/production/historical_production.csv')
print(f'OK: {len(batches)} batches')
print(f'Risk counts: {df["risk_level"].value_counts().to_dict()}')
