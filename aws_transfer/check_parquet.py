import pandas as pd

file = "export\market\year=2026\market_data.parquet"
df = pd.read_parquet(file)
print(df.head())