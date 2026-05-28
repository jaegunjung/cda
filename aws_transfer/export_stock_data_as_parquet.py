import utils as ut
import os
import pandas as pd

S3_BUCKET = "cda-data-lake-jaegun"

symbols = ['SPY', "^GSPC", 'DIA', '^DJI', 'AMZN', 'ENVX', 'AAPL', 'VFIAX', 'TSLA', 'QQQ', 'META', 'GOOG', 'NVDA']

symbol_list = ", ".join([f"'{s}'" for s in symbols])

query = f"""
SELECT
  [Symbol],
  CAST([date] AS date) AS price_date,
  [Open_Price_USD],
  [High_Price_USD],
  [Low_Price_USD],
  [Close_Price_USD],
  [Adj_Close_Price_USD],
  [Volume]
FROM [cda].[dbo].[StockDaily]
WHERE [Symbol] IN ({symbol_list})
ORDER BY [date], [Symbol]
"""

df = ut.query_db(query)

df["price_date"] = pd.to_datetime(df["price_date"])

df["year"] = df["price_date"].dt.year
df["month"] = df["price_date"].dt.month.astype(str).str.zfill(2)

df["price_date"] = df["price_date"].dt.strftime("%Y-%m-%d")

for year, part in df.groupby("year"):
    local_dir = f"export/market/stock/year={year}"
    os.makedirs(local_dir, exist_ok=True)

    local_file = f"{local_dir}/market_data.parquet"

    part = part.drop(columns=["year"])

    part = (
        part.sort_values(["Symbol", "price_date"])
            .drop_duplicates(
                subset=["Symbol", "price_date"],
                keep="last"
            )
    )

    part.to_parquet(
        local_file,
        index=False,
        engine="pyarrow"
    )

    print(f"Created {local_file}")