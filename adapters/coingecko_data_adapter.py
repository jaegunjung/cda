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

    df = pd.DataFrame(data['prices'], columns=['time', 'price'])

    # Convert epoch time to regular datetime
    df['Date'] = pd.to_datetime(df['time']*.001, unit='s', utc=True)
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S%z').str[:22] + ':' + df['Date'].dt.strftime('%z').str[3:]
    df = df.rename(columns={'price': 'Open_Price_USD'})
    df['Crypto'] = CRYPTO_SYMBOL[crypto]

    return df[['Crypto', 'Date', 'Open_Price_USD']][:-1]  # last record is not the open price.


def calc_days(crypto):
    """
    Calculate a number of days to load
    :param crypto: the cryptocurrency such as bitcoin
    :return:
    """
    qry = """    
    select DATEDIFF(DAY, MAX([Date]), GETUTCDATE()) as days from CryptoDaily where Crypto = '{}'
    """.format(CRYPTO_SYMBOL[crypto])
    df = ut.query_db(qry)
    days = 0
    if not df.empty:
        days = df['days'].iloc[0]
    return days


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
        days = calc_days(crypto)
    if days > 0:
        df = load_crypto_daily(crypto, currency, days)
        ut.df_to_db(df, 'CryptoDaily')


if __name__ == '__main__':
    # ut.time_to_run(process_cripto_daily, 'bitcoin', 'usd', True)  # Initial load
    ut.time_to_run(process_cripto_daily, 'bitcoin', 'usd')
