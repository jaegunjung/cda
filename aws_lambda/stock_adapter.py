import os
import io
import time

import boto3
import pandas as pd
import requests


s3 = boto3.client("s3")

BUCKET = os.environ.get("BUCKET", "cda-data-lake-jaegun")
PREFIX = os.environ.get("PREFIX", "market/stock")
PARQUET_FILE_NAME = os.environ.get("PARQUET_FILE_NAME", "market_data.parquet")
SYMBOLS = os.environ.get(
    "SYMBOLS",
    "SPY,^GSPC,DIA,^DJI,AMZN,ENVX,AAPL,VFIAX,TSLA,QQQ,META,GOOG,NVDA",
).split(",")
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY") or os.environ.get("alpha_vantage_api_key")
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "1.1"))
RATE_LIMIT_SLEEP_SECONDS = float(os.environ.get("RATE_LIMIT_SLEEP_SECONDS", "15"))
RATE_LIMIT_RETRIES = int(os.environ.get("RATE_LIMIT_RETRIES", "3"))
SKIP_MISSING_SYMBOLS = os.environ.get("SKIP_MISSING_SYMBOLS", "true").lower() == "true"
TARGET_COLUMNS = [
    "Symbol",
    "price_date",
    "Open_Price_USD",
    "High_Price_USD",
    "Low_Price_USD",
    "Close_Price_USD",
    "Adj_Close_Price_USD",
    "Volume",
]


class AlphaVantageDailyLimitError(Exception):
    pass


def is_daily_limit_message(message):
    if not message:
        return False

    message = message.lower()
    return "standard api rate limit is 25 requests per day" in message


def request_stock_daily(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY,
    }

    for attempt in range(RATE_LIMIT_RETRIES + 1):
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()

        data = r.json()
        time_series = data.get("Time Series (Daily)")
        if time_series:
            return time_series

        message = data.get("Information") or data.get("Note")
        if is_daily_limit_message(message):
            raise AlphaVantageDailyLimitError(f"Alpha Vantage daily API limit reached while requesting {symbol}: {message}")

        if message and attempt < RATE_LIMIT_RETRIES:
            print(f"Alpha Vantage throttled {symbol}; retrying after {RATE_LIMIT_SLEEP_SECONDS} seconds")
            time.sleep(RATE_LIMIT_SLEEP_SECONDS)
            continue

        if SKIP_MISSING_SYMBOLS:
            print(f"Skipping {symbol}: missing daily time series: {data}")
            return None

        raise ValueError(f"Missing daily time series for {symbol}: {data}")


def parse_stock_daily(symbol, time_series):
    rows = []
    for price_date, values in time_series.items():
        close_price = float(values["4. close"])
        rows.append({
            "Symbol": symbol,
            "price_date": price_date,
            "Open_Price_USD": float(values["1. open"]),
            "High_Price_USD": float(values["2. high"]),
            "Low_Price_USD": float(values["3. low"]),
            "Close_Price_USD": close_price,
            "Adj_Close_Price_USD": close_price,
            "Volume": int(values["5. volume"]),
        })

    return rows


def get_stock_prices():
    if not API_KEY:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY environment variable")

    rows = []

    for index, symbol in enumerate(SYMBOLS):
        symbol = symbol.strip()
        if not symbol:
            continue

        if index > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

        time_series = request_stock_daily(symbol)
        if not time_series:
            continue

        rows.extend(parse_stock_daily(symbol, time_series))

    return pd.DataFrame(rows, columns=TARGET_COLUMNS)


def normalize_stock_df(df):
    if df.empty:
        return pd.DataFrame(columns=TARGET_COLUMNS)

    df = df.copy()

    if "Date" in df.columns and "price_date" not in df.columns:
        df["price_date"] = df["Date"]

    for column in TARGET_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[TARGET_COLUMNS]
    df = df.dropna(subset=TARGET_COLUMNS)
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.strftime("%Y-%m-%d")

    return (
        df.sort_values(["Symbol", "price_date"])
        .drop_duplicates(subset=["Symbol", "price_date"], keep="last")
        .reset_index(drop=True)
    )


def filter_new_rows(new_df, existing_df):
    if existing_df.empty:
        return new_df

    existing_keys = set(zip(existing_df["Symbol"], existing_df["price_date"]))
    new_keys = list(zip(new_df["Symbol"], new_df["price_date"]))
    return new_df[[key not in existing_keys for key in new_keys]]


def read_existing_parquet(bucket, key):
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return pd.read_parquet(io.BytesIO(obj["Body"].read()))
    except s3.exceptions.NoSuchKey:
        return pd.DataFrame()


def read_existing_parquet_prefix(bucket, prefix):
    frames = []
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for item in response.get("Contents", []):
        key = item["Key"]
        if not key.endswith(".parquet"):
            continue

        obj = s3.get_object(Bucket=bucket, Key=key)
        frames.append(pd.read_parquet(io.BytesIO(obj["Body"].read())))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def get_stock_parquet_key(year):
    return f"{PREFIX}/year={year}/{PARQUET_FILE_NAME}"


def get_stock_partition_prefix(year):
    return f"{PREFIX}/year={year}/"


def read_existing_stock_year(year):
    key = get_stock_parquet_key(year)
    df = read_existing_parquet(BUCKET, key)
    if not df.empty:
        return normalize_stock_df(df)

    prefix = get_stock_partition_prefix(year)
    return normalize_stock_df(read_existing_parquet_prefix(BUCKET, prefix))


def read_existing_stock_years(years):
    frames = []

    for year in years:
        df = read_existing_stock_year(year)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=TARGET_COLUMNS)

    return normalize_stock_df(pd.concat(frames, ignore_index=True))


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
    try:
        new_df = normalize_stock_df(get_stock_prices())
    except AlphaVantageDailyLimitError as exc:
        print(str(exc))
        return {
            "statusCode": 429,
            "error": str(exc),
            "rows_uploaded": 0,
        }

    if new_df.empty:
        print("No stock rows returned from data provider")
        return {
            "statusCode": 200,
            "rows_uploaded": 0,
            "s3_key": None,
        }

    uploads = []
    years = sorted(new_df["price_date"].str[:4].unique())
    existing_all_df = read_existing_stock_years(years)
    rows_to_upload = filter_new_rows(new_df, existing_all_df)

    if rows_to_upload.empty:
        print("No new stock rows to upload")
        return {
            "statusCode": 200,
            "rows_uploaded": 0,
            "uploads": [
                {
                    "year": year,
                    "rows_uploaded": 0,
                    "s3_key": get_stock_parquet_key(year),
                }
                for year in years
            ],
        }

    for year, year_new_df in rows_to_upload.groupby(rows_to_upload["price_date"].str[:4]):
        key = get_stock_parquet_key(year)

        existing_df = read_existing_stock_year(year)
        rows_to_add = filter_new_rows(year_new_df, existing_df)

        if rows_to_add.empty:
            print(f"No new stock rows to upload for {year}")
            uploads.append({
                "year": year,
                "rows_uploaded": 0,
                "rows_in_parquet": len(existing_df),
                "s3_key": key,
            })
            continue

        df = pd.concat([existing_df, rows_to_add], ignore_index=True)

        df = (
            normalize_stock_df(df)
            .sort_values(["Symbol", "price_date"])
            .drop_duplicates(subset=["Symbol", "price_date"], keep="last")
        )

        print(rows_to_add)

        # write_parquet_to_s3(df, BUCKET, key)

        uploads.append({
            "year": year,
            "rows_uploaded": len(rows_to_add),
            "rows_in_parquet": len(df),
            "s3_key": key,
        })

    return {
        "statusCode": 200,
        "rows_uploaded": sum(upload["rows_uploaded"] for upload in uploads),
        "uploads": uploads,
    }


if __name__ == "__main__":
    print(lambda_handler({}, None))
