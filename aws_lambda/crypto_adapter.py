import os
import io
from datetime import datetime, timezone

import boto3
import pandas as pd
import requests


s3 = boto3.client("s3")

BUCKET = os.environ.get("BUCKET", "cda-data-lake-jaegun")
PREFIX = os.environ.get("PREFIX", "market/crypto")
COINS = os.environ.get("COINS", "bitcoin,ethereum,pepe").split(",")


def get_crypto_prices():
    ids = ",".join(COINS)

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ids,
        "vs_currencies": "usd",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()

    data = r.json()

    price_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    rows = []
    for coin_id, values in data.items():
        rows.append({
            "Symbol": coin_id.upper(),
            "coin_id": coin_id,
            "price_date": price_date,
            "Close_Price_USD": float(values["usd"]),
        })

    return pd.DataFrame(rows)


def read_existing_parquet(bucket, key):
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return pd.read_parquet(io.BytesIO(obj["Body"].read()))
    except s3.exceptions.NoSuchKey:
        return pd.DataFrame()


def write_parquet_to_s3(df, bucket, key):
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )


def lambda_handler(event, context):
    new_df = get_crypto_prices()

    year = new_df["price_date"].str[:4].iloc[0]
    key = f"{PREFIX}/year={year}/crypto_data.parquet"

    existing_df = read_existing_parquet(BUCKET, key)

    if not existing_df.empty:
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df

    df = (
        df.sort_values(["coin_id", "price_date"])
          .drop_duplicates(subset=["coin_id", "price_date"], keep="last")
    )

    write_parquet_to_s3(df, BUCKET, key)

    return {
        "statusCode": 200,
        "rows_written": len(df),
        "s3_key": key,
    }

if __name__ == "__main__":
    print(lambda_handler({}, None))