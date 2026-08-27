import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv('ai4i2020.csv')

# Use stratified split based on Machine failure to ensure balanced evaluation
train_df, eval_df = train_test_split(df, test_size=0.2, stratify=df['Machine failure'], random_state=42)

train_df.to_csv('data/production/historical_production.csv', index=False)
eval_df.to_csv('data/evaluation/stratified_evaluation.csv', index=False)

print(f"Train shape: {train_df.shape}")
print(f"Eval shape: {eval_df.shape}")
print(f"Train failure rate: {train_df['Machine failure'].mean():.4f}")
print(f"Eval failure rate: {eval_df['Machine failure'].mean():.4f}")
