import utils as ut
import os
import pandas as pd

S3_BUCKET = "cda-data-lake-jaegun"

query = f"""
SELECT
  [Crypto],
  CAST([date] AS date) AS price_date,
  [Open_Price_USD],
  [Total_Volume_USD],
  [Market_Cap_USD]
FROM [cda].[dbo].[CryptoDaily]
ORDER BY [date], [Crypto]
"""

df = ut.query_db(query)

df["price_date"] = pd.to_datetime(df["price_date"])

df["year"] = df["price_date"].dt.year
df["month"] = df["price_date"].dt.month.astype(str).str.zfill(2)

df["price_date"] = df["price_date"].dt.strftime("%Y-%m-%d")

for year, part in df.groupby("year"):
    local_dir = f"export/market/crypto/year={year}"
    os.makedirs(local_dir, exist_ok=True)

    local_file = f"{local_dir}/crypto_data.parquet"

    part = part.drop(columns=["year"])

    part = (
        part.sort_values(["Crypto", "price_date"])
            .drop_duplicates(
                subset=["Crypto", "price_date"],
                keep="last"
            )
    )

    part.to_parquet(
        local_file,
        index=False,
        engine="pyarrow"
    )

    print(f"Created {local_file}")
