import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import pytz
import requests

import utils as ut

START = '2013-04-27'  # The first available BTC-USD day - 1

# Standard API rate limit is 25 requests per day.
API_KEY = os.environ.get('alpha_vantage_api_key')

if not API_KEY:
    raise ValueError('Missing alpha_vantage_api_key environment variable')

def get_end_date():
    """
    Return tomorrow date in YYYY-MM-DD in EST.
    :return:
    """
    # Set the time zone to Eastern Standard Time (EST)
    est_timezone = pytz.timezone('US/Eastern')
    # Get the current date and time in UTC
    utc_now = datetime.utcnow()
    # Convert the UTC time to Eastern Standard Time (EST)
    est_now = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)
    # Add one day
    est_tomorrow = est_now + timedelta(days=1)
    # Extract the date part in 'YYYY-MM-DD' format
    formatted_date_tomorrow = est_tomorrow.strftime('%Y-%m-%d')
    return formatted_date_tomorrow


def find_latest_date(Symbol):
    qry = """
    SELECT CONVERT(VARCHAR, DATEADD(DAY, 1, max(Date)), 23) as latest_date
    FROM [cda].[dbo].[StockDaily]
    where Symbol = '{}'
    """.format(Symbol)
    df = ut.query_db(qry)
    latest_date = START
    if not df.empty and df['latest_date'].iloc[0]:
        latest_date = df['latest_date'].iloc[0]
    return latest_date


def process_stock_daily(symbols, output_dir: str = None) -> None:
    end = get_end_date()
    for Symbol in symbols:
        print(Symbol)
        start = find_latest_date(Symbol)
        start_dt = pd.to_datetime(start)

        n_days = ut.count_n_days(start, end)
        if n_days <= 0:
            print('No new data!')
            continue

        url = (
            f'https://www.alphavantage.co/query?'
            f'function=TIME_SERIES_DAILY&'
            f'symbol={Symbol}&'
            f'outputsize=compact&'
            f'apikey={API_KEY}'
        )

        r = requests.get(url)
        data = r.json()

        time.sleep(1)

        if 'Time Series (Daily)' not in data:
            print(f'Skipping {Symbol}: unexpected response: {data}')
            continue

        ts = data['Time Series (Daily)']

        rows = []

        for date_str, values in ts.items():
            close = float(values['4. close'])
            rows.append({
                'Date': pd.to_datetime(date_str),
                'Open_Price_USD': float(values['1. open']),
                'High_Price_USD': float(values['2. high']),
                'Low_Price_USD': float(values['3. low']),
                'Close_Price_USD': close,
                'Adj_Close_Price_USD': close,
                'Volume': int(values['5. volume']),
                'Symbol': Symbol
            })

        df = pd.DataFrame(rows)
        if df.empty:
            print('Empty df - No new data!')
            continue

        # Keep only rows newer than latest DB date
        df = df[df['Date'] >= start_dt]

        # Safety: remove duplicated rows inside dataframe
        df = df.drop_duplicates(subset=['Date', 'Symbol'])

        # Sort and reset index correctly
        df = df.sort_values('Date').reset_index(drop=True)

        if df.empty:
            print('No new rows after filtering by start date!')
            continue

        print(df.head())

        ut.df_to_db(df, 'StockDaily')
        if output_dir:
            export_symbol_csv(Symbol, output_dir)


_CSV_QRY = """
    SELECT
        CAST([Date] AS DATE)      AS date,
        [Open_Price_USD]          AS open_price_usd,
        [Close_Price_USD]         AS close_price_usd,
        [Adj_Close_Price_USD]     AS adj_close_price_usd,
        [Volume]                  AS total_volume_usd
    FROM [cda].[dbo].[StockDaily]
    WHERE [Symbol] = '{}'
    ORDER BY [Date] ASC
"""


def export_symbol_csv(symbol: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    df = ut.query_db(_CSV_QRY.format(symbol))
    filename = symbol.replace('^', '') + '.csv'
    df.to_csv(os.path.join(output_dir, filename), index=False)
    print(f'Exported: {filename} ({len(df)} rows)')


if __name__ == '__main__':
    with open('config/symbols.json') as f:
        cfg = json.load(f)
    symbols = cfg['stocks']
    output_dir = cfg.get('csv_output_dir') if '--export-csv' in __import__('sys').argv else None
    ut.time_to_run(process_stock_daily, symbols, output_dir=output_dir)
