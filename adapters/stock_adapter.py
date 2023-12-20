import yfinance as yf
import utils as ut
from datetime import datetime, timedelta
import pytz

START = '2013-04-27'  # The first available BTC-USD day - 1


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


def process_stock_daily(symbols) -> None:
    end = get_end_date()
    for Symbol in symbols:
        start = find_latest_date(Symbol)
        n_days = ut.count_n_days(start, end)
        if n_days <= 0:
            print('No new data!')
            return
        df = yf.download(Symbol, start=start, end=end)
        df['Symbol'] = Symbol
        df.reset_index(inplace=True)
        df = df.rename(
            columns={'Open': 'Open_Price_USD',
                     'High': 'High_Price_USD',
                     'Low': 'Low_Price_USD',
                     'Close': 'Close_Price_USD',
                     'Adj Close': 'Adj_Close_Price_USD'})
        ut.df_to_db(df, 'StockDaily')


if __name__ == '__main__':
    symbols = ['^GSPC', '^DJI', 'AMZN', 'ENVX', 'AAPL', 'VFIAX', 'TSLA', 'QQQ', 'META', 'GOOG']
    ut.time_to_run(process_stock_daily, symbols)
