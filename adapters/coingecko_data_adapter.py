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
import pandas as pd
import utils as ut

CRYPTO_SYMBOL = {'bitcoin': 'BTC'}


def load_crypto_daily(crypto: str = 'bitcoin', currency: str = 'usd', days: int = 5) -> pd.DataFrame:
    """
    Access data from internet and return the results as a dataframe.
    :param crypto: the cryptocurrency such as bitcoin
    :param currency: currency such as usd
    :param days: the number of days for historical data
    :return: df with symbol, date, and open price
    """

    # Construct the API URL for historical prices.
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {'vs_currency': currency, 'days': days, 'interval': 'daily'}
    response = requests.get(url, params=params)
    data = response.json()

    # Construct three dataframes
    prices = pd.DataFrame(data['prices'], columns=['time', 'price'])
    market_cap = pd.DataFrame(data['market_caps'], columns=['time', 'market_cap'])
    total_vol = pd.DataFrame(data['total_volumes'], columns=['time', 'total_volume'])

    # Merge them and process
    if (len(prices) == len(market_cap) == len(total_vol)) and \
        (prices['time'] == market_cap['time']).all() and (market_cap['time'] == total_vol['time']).all():
        df = pd.concat([prices, market_cap['market_cap'], total_vol['total_volume']], axis=1)
        # Convert epoch time to regular datetime
        df['Date'] = pd.to_datetime(df['time']*.001, unit='s', utc=True)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S%z').str[:22] + ':' + df['Date'].dt.strftime('%z').str[3:]
        df.drop(columns=['time'], inplace=True)
        df = df.rename(columns={'price': 'Open_Price_USD', 'market_cap': 'Market_Cap_USD',
                                'total_volume': 'Total_Volume_USD'})
        df['Crypto'] = CRYPTO_SYMBOL[crypto]

        return df[:-1]  # last record is not the open price.


def calc_days(crypto):
    """
    Calculate a number of days to load
    :param crypto: the cryptocurrency such as bitcoin
    :return:
    """
    qry = """    
    select DATEDIFF(DAY, MAX([Date]), GETUTCDATE()) as days, MAX([Date]) as max_rc_date 
    from CryptoDaily where Crypto = '{}'
    """.format(CRYPTO_SYMBOL[crypto])
    df = ut.query_db(qry)
    days = 0
    if not df.empty:
        days = df['days'].iloc[0]
        mx_rd_date = df['max_rc_date'].iloc[0]
    return days, mx_rd_date


def process_cripto_daily(crypto: str = 'bitcoin', currency: str = 'usd', init: bool = False) -> None:
    """
    Check DB and load price data for new days.
    :param crypto: the cryptocurrency such as bitcoin
    :param currency: currency such as usd
    :param init: Is it for the initial load?
    :return:
    """
    if init:
        days = 900000  # Data available from 2013-04-28. Up to 2023-12-03, there are 3870 days. It is more than enough.
    else:
        days, mx_rd_date = calc_days(crypto)
    if days > 0:
        df = load_crypto_daily(crypto, currency, days)
        df = df[df['Date'] > str(mx_rd_date)]
        ut.df_to_db(df, 'CryptoDaily')


if __name__ == '__main__':
    # ut.time_to_run(process_cripto_daily, 'bitcoin', 'usd', True)  # Initial load
    ut.time_to_run(process_cripto_daily, 'bitcoin', 'usd')
