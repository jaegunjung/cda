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

import pandas as pd
import utils as ut


def get_max_id(Symbol):
    qry = """    
    select MAX(ID) as max_id 
    from Transactions where Symbol = '{}'
    """.format(Symbol)
    df = ut.query_db(qry)
    mx_id = 0
    if not df.empty and df['max_id'].iloc[0]:
        mx_id = df['max_id'].iloc[0]
    return mx_id


def load_excel_btc_transaction(tbl, ifile, sheet_name, cols_to_read, nrows, Symbol):
    df = pd.read_excel(ifile, sheet_name=sheet_name, usecols=cols_to_read, nrows=nrows)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['Symbol'] = Symbol
    for col in ['Date']:
        df[col] = pd.to_datetime(df[col])
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S') + "+00:00"
    return df


def proc_btc_transaction():
    tbl = 'Transactions'
    ifile = r"D:\Documents\my_business\BTC\BTC_anlaysis_v1.xlsx"
    sheet_name = "BTC_trnsctn"
    Symbol = 'BTC'
    cols_to_read = ['Date', 'type', 'amount', 'price', 'fee']
    nrows = 141  # Update 141 to a newer one. 141 is the last row minus 1.
    df = load_excel_btc_transaction(tbl, ifile, sheet_name, cols_to_read, nrows, Symbol)
    mx_id = get_max_id(Symbol)
    df = df[df.index > mx_id - 1]
    if not df.empty:
        print(df)
        ut.df_to_db(df, tbl)


if __name__ == '__main__':
    proc_btc_transaction()
