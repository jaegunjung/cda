import pandas as pd

file = "export\market\crypto\year=2026\crypto_data.parquet"
df = pd.read_parquet(file)
print(df.head())