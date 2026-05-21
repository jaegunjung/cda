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
DEFAULT_HISTORY_DAYS = int(os.environ.get("DEFAULT_HISTORY_DAYS", "5"))
CRYPTO_SYMBOL = {"bitcoin": "BTC", "ethereum": "ETH", "pepe": "PEPE"}
TARGET_COLUMNS = [
    "Crypto",
    "price_date",
    "Open_Price_USD",
    "Total_Volume_USD",
    "Market_Cap_USD",
]


def get_days_to_fetch(crypto, existing_df, today):
    if existing_df.empty:
        return DEFAULT_HISTORY_DAYS

    existing_crypto_df = existing_df[existing_df["Crypto"] == crypto]
    if existing_crypto_df.empty:
        return DEFAULT_HISTORY_DAYS

    latest_date = pd.to_datetime(existing_crypto_df["price_date"]).max().date()
    return max((today - latest_date).days + 1, 1)


def load_crypto_daily(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()

    data = r.json()

    prices = pd.DataFrame(data["prices"], columns=["time", "Open_Price_USD"])
    market_caps = pd.DataFrame(data["market_caps"], columns=["time", "Market_Cap_USD"])
    total_volumes = pd.DataFrame(data["total_volumes"], columns=["time", "Total_Volume_USD"])

    if not (
        len(prices) == len(market_caps) == len(total_volumes)
        and (prices["time"] == market_caps["time"]).all()
        and (market_caps["time"] == total_volumes["time"]).all()
    ):
        raise ValueError(f"Mismatched CoinGecko time series for {coin_id}")

    df = pd.concat(
        [
            prices[["time", "Open_Price_USD"]],
            total_volumes["Total_Volume_USD"],
            market_caps["Market_Cap_USD"],
        ],
        axis=1,
    )
    df["price_date"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    df["Crypto"] = CRYPTO_SYMBOL.get(coin_id, coin_id.upper())

    return df[TARGET_COLUMNS]


def get_crypto_prices(existing_df):
    today = datetime.now(timezone.utc).date()

    rows = []
    for coin_id in COINS:
        coin_id = coin_id.strip()
        if not coin_id:
            continue

        crypto = CRYPTO_SYMBOL.get(coin_id, coin_id.upper())
        days = get_days_to_fetch(crypto, existing_df, today)
        rows.append(load_crypto_daily(coin_id, days))

    if not rows:
        return pd.DataFrame(columns=TARGET_COLUMNS)

    return pd.concat(rows, ignore_index=True)


def normalize_crypto_df(df):
    if df.empty:
        return pd.DataFrame(columns=TARGET_COLUMNS)

    df = df.copy()

    if "Date" in df.columns and "price_date" not in df.columns:
        df["price_date"] = df["Date"]

    for column in TARGET_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[TARGET_COLUMNS]
    df = df.dropna(
        subset=[
            "Crypto",
            "price_date",
            "Open_Price_USD",
            "Total_Volume_USD",
            "Market_Cap_USD",
        ]
    )

    df["price_date"] = pd.to_datetime(df["price_date"]).dt.strftime("%Y-%m-%d")
    return (
        df.sort_values(["Crypto", "price_date"])
        .drop_duplicates(subset=["Crypto", "price_date"], keep="last")
        .reset_index(drop=True)
    )


def filter_new_rows(new_df, existing_df):
    if existing_df.empty:
        return new_df

    existing_keys = set(zip(existing_df["Crypto"], existing_df["price_date"]))
    new_keys = list(zip(new_df["Crypto"], new_df["price_date"]))
    return new_df[[key not in existing_keys for key in new_keys]]


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
    year = datetime.now(timezone.utc).strftime("%Y")
    key = f"{PREFIX}/year={year}/crypto_data.parquet"

    existing_df = normalize_crypto_df(read_existing_parquet(BUCKET, key))
    new_df = normalize_crypto_df(get_crypto_prices(existing_df))
    rows_to_add = filter_new_rows(new_df, existing_df)

    if rows_to_add.empty:
        print("No new crypto rows to upload")
        return {
            "statusCode": 200,
            "rows_uploaded": 0,
            "s3_key": key,
        }

    df = pd.concat([existing_df, rows_to_add], ignore_index=True)

    df = (
        normalize_crypto_df(df)
        .sort_values(["Crypto", "price_date"])
        .drop_duplicates(subset=["Crypto", "price_date"], keep="last")
    )

    write_parquet_to_s3(df, BUCKET, key)

    return {
        "statusCode": 200,
        "rows_uploaded": len(rows_to_add),
        "rows_in_parquet": len(df),
        "s3_key": key,
    }

if __name__ == "__main__":
    print(lambda_handler({}, None))
