# This file is part of cda
#
# cda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cda.  If not, see <http://www.gnu.org/licenses/>.

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import utils as ut
from datetime import datetime, timedelta
import numpy as np


def extract_table_data(table, column_header=True):
    table_data = []
    for row in table.find_all('tr'):
        row_data = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
        table_data.append(row_data)
    if column_header:
        return pd.DataFrame(table_data[1:], columns=table_data[0])
    else:
        return pd.DataFrame(table_data)


def process_numeric_column(df, col):
    return df[col].replace('[\$,]', '', regex=True).astype(float)


def process_percentage_column(df, col):
    return df[col].apply(lambda x: float(re.sub(r'%', '', x)))


def process_integer_column(df, col):
    return df[col].apply(lambda x: int(re.sub(r'[^0-9]', '', x)))


def process_green_days_column(df, col):
    return df[col].apply(lambda x: float(re.search(r'\((\d+)%\)', x).group(1)))


def process_price_prediction_column(df, col):
    return pd.to_numeric(df[col].replace('[\$,]', '', regex=True).str.extract(r'([\d.]+)')[0])


def clean_changelly_today_df(df):
    for col in ['Circulating_Supply_BTC', 'Fear_Greed_Index']:
        df[col] = process_integer_column(df, col)

    for col in ['Change_24h_perc', 'Change_7d_perc', 'Volatility_perc']:
        df[col] = process_percentage_column(df, col)

    for col in ['Price_USD', 'Market_Cap_USD', 'Trading_Volume_USD', 'All_Time_High',
                'All_Time_Low', 'SMA_50d_USD', 'SMA_200d_USD']:
        df[col] = process_numeric_column(df, col)

    df['GreenDays_30d_perc'] = process_green_days_column(df, 'GreenDays_30d_perc')
    df['Price_Pred_7d_USD'] = process_price_prediction_column(df, 'Price_Pred_7d_USD')
    df['RSI_14d'] = df['RSI_14d'].astype(float)
    return df


def changelly_btc_forecast_grabber(last_rec_dy, last_annual):
    """
    The changelly website provides bitcoin forecast price values with multiple tables.
    As of 12/6/2023, There are 13 tables as follows.

    Table 1 = Today's overall metrics
    Table 2 = Daily forecast for 30 days
    Table 3 = Annual forecast for 10 years
    Table 4 - 12 = Monthly forecast. One table per year.
    Table 13 = Table 3 (We will not extract.)

    It will return Table 1, Table 2, Table 3, and Table 4 - 12 as one table.

    :param last_rec_dy: the last day processed to check whether to need to process
    :param last_annual: last annual forecast. If it is same, no addtional records in DB will be made.
    :return: (today, daily, annual, monthly)
    """
    Crypto = 'BTC'
    url = 'https://changelly.com/blog/bitcoin-price-prediction/'

    tdy_idx, dly_idx, ann_idx = 0, 1, 2
    mo_beg_idx, mo_end_idx = 3, 11

    # Send a GET request to the website
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize outputs
    today = daily = annual = monthly = pd.DataFrame()

    # Read post date
    date_span = soup.find('span', class_='post-date')
    if not date_span:
        raise Exception("No element with class 'post-date' found.")
    date_text = date_span.text
    date_object = pd.to_datetime(date_text, utc=True)
    if date_object <= last_rec_dy:
        print('No update in the website. Skip the processing.')
        return today, daily, annual, monthly

    # If the post date is older than the current UTC date, skip.
    if pd.Timestamp(date_object).date() < pd.Timestamp(datetime.utcnow() + timedelta(hours=-3)).date():
        raise Exception("Website has not been updated.")
    date_pred = date_object.strftime('%Y-%m-%d %H:%M:%S%z')[:22] + ':' + date_object.strftime('%z')[3:]

    # Find all tables on the page
    tables = soup.find_all('table')
    if not tables:
        raise Exception("No tables found on the webpage.")

    # Extract data from each table and create Pandas DataFrames
    df_mos = []
    for idx, table in enumerate(tables[:-1]):  # Exclude the last table
        if idx == tdy_idx:
            df = extract_table_data(table, column_header=False)
            df = df.T.rename(columns=df.T.iloc[0]).iloc[1:]
            df = df.rename(
                columns={'Bitcoin Price': 'Price_USD', 'Bitcoin Price Change 24h': 'Change_24h_perc',
                         'Bitcoin Price Change 7d': 'Change_7d_perc', 'Bitcoin Market cap': 'Market_Cap_USD',
                         'Bitcoin Circulating Supply': 'Circulating_Supply_BTC',
                         'Bitcoin Trading Volume': 'Trading_Volume_USD',
                         'Bitcoin All time high': 'All_Time_High', 'Bitcoin All time low': 'All_Time_Low',
                         'Bitcoin Price Prediction 7d': 'Price_Pred_7d_USD',
                         'Bitcoin Fear-Greed Index': 'Fear_Greed_Index', 'Bitcoin Sentiment': 'Sentiment',
                         'Bitcoin Volatility': 'Volatility_perc', 'Bitcoin Green Days': 'GreenDays_30d_perc',
                         'Bitcoin 50-Day SMA': 'SMA_50d_USD', 'Bitcoin 200-Day SMA': 'SMA_200d_USD',
                         'Bitcoin 14-Day RSI': 'RSI_14d'})
            df = clean_changelly_today_df(df)
            df['Date_Pred'] = date_pred
            df['Crypto'] = Crypto
            today = df.copy()
        else:
            df = extract_table_data(table)
            df['Date_Pred'] = date_pred
            df['Crypto'] = Crypto
        if idx == dly_idx:
            df['Date'] = pd.to_datetime(df['Date'])
            # If the first date is not equal to post date + 1, skip.
            # Changelly sometimes delaying updating the first date especially early day in UTC.
            # The post date is same as the first date. Commenting out the checking below for now. (12/9/2023)
            # if pd.Timestamp(date_object).date() + timedelta(days=1) != pd.Timestamp(df['Date'].iloc[0]).date():
            #     print("Table for 30 days forecast has not been updated.")
            #     continue

            # Use the value from the post date as the starting point and add one day to each subsequent row
            df['Date'] = df['Date'].iloc[0] + pd.to_timedelta(df.index, unit='D')

            # Format the datetime column as a string
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S') + "+00:00"
            df['Close_Price_USD'] = process_numeric_column(df, 'Price')
            df['Change_perc'] = process_percentage_column(df, 'Change')
            daily = df[['Crypto', 'Date_Pred', 'Date', 'Close_Price_USD', 'Change_perc']].copy()
        elif idx == ann_idx:
            df = df.rename(
                columns={'Minimum Price': 'Min_Close_Price_USD', 'Average Price': 'Avg_Close_Price_USD',
                         'Maximum Price': 'Max_Close_Price_USD'})
            for col in ['Min_Close_Price_USD', 'Avg_Close_Price_USD', 'Max_Close_Price_USD']:
                df[col] = process_numeric_column(df, col)
            df['Year'] = pd.to_datetime(df['Year'])
            # If the first year must be the current year
            if date_object.year != df['Year'].iloc[0].year:
                raise Exception("Table for 10 years yearly forecast has not been updated.")

            # Use the value from the post date as the starting point and add one day to each subsequent row
            for i in df.index:
                df.at[i, 'Year'] = df['Year'].iloc[0] + pd.DateOffset(years=i)
            if (last_annual == df[last_annual.columns]).all().all():
                print("10 year annual forecast has not been updated.")
                continue
            annual = df.copy()
        if mo_beg_idx <= idx <= mo_end_idx:
            df_mos.append(df)
        print(f"Table {idx + 1}:")
        print(df)
        print("\n---\n")

    if df_mos:
        monthly = pd.concat(df_mos, ignore_index=True)

        # Sometimes min, avg, max are not ordered correctly.
        for col in ['Minimum Price', 'Average Price', 'Maximum Price']:
            monthly[col] = process_numeric_column(monthly, col)
        monthly['Min_Close_Price_USD'] = np.minimum.reduce([monthly['Minimum Price'], monthly['Average Price'], monthly['Maximum Price']], axis=0)
        monthly['Avg_Close_Price_USD'] = np.median([monthly['Minimum Price'], monthly['Average Price'], monthly['Maximum Price']], axis=0)
        monthly['Max_Close_Price_USD'] = np.maximum.reduce([monthly['Minimum Price'], monthly['Average Price'], monthly['Maximum Price']], axis=0)
        monthly.drop(['Minimum Price', 'Average Price', 'Maximum Price'], axis=1, inplace=True)
        monthly['Month'] = pd.to_datetime(monthly['Month'])

        # Use the value from the post date as the starting point and add one day to each subsequent row
        for i in monthly.index:
            monthly.at[i, 'Month'] = monthly['Month'].iloc[0] + pd.DateOffset(months=i)
    return today, daily, annual, monthly


def upload_to_db(today, daily, annual, monthly):
    if not today.empty:
        ut.df_to_db(today, 'ChangellyDailyMetrics')
    if not daily.empty:
        ut.df_to_db(daily, 'Changelly30dDailyPred')
    if not annual.empty:
        ut.df_to_db(annual, 'Changelly10yYearlyPred')
    if not monthly.empty:
        ut.df_to_db(monthly, 'Changelly10yMonthlyPred')


def changelly_forecast_grabber(Crypto, last_rec_dy, last_annual):
    if Crypto == 'BTC':
        return changelly_btc_forecast_grabber(last_rec_dy, last_annual)


def check_db(Crypto):
    qry1 = """
    SELECT max(Date_Pred) as last_rec_day
    FROM ChangellyDailyMetrics
    where Crypto = '{}'
    """.format(Crypto)
    df1 = ut.query_db(qry1)
    last_rec_dy = '1900-01-01 00:00:00.0000000 +00:00'
    if not df1.empty:
        last_rec_dy = df1['last_rec_day'].iloc[0]

    qry2 = """
    SELECT convert(date, [Year]) as [Year], Min_Close_Price_USD, Avg_Close_Price_USD, Max_Close_Price_USD
    FROM Changelly10yYearlyPred
    where Date_Pred = (select max(Date_Pred) from Changelly10yYearlyPred) and Crypto = '{}'
    """.format(Crypto)
    df2 = ut.query_db(qry2)
    last_annual = pd.DataFrame()
    if not df2.empty:
        last_annual = df2
    return last_rec_dy, last_annual


def process_changelly_forecast():
    for Crypto in ['BTC']:
        last_rec_dy, last_annual = check_db(Crypto)
        today, daily, annual, monthly = changelly_forecast_grabber(Crypto, last_rec_dy, last_annual)
        upload_to_db(today, daily, annual, monthly)


if __name__ == '__main__':
    ut.time_to_run(process_changelly_forecast)
