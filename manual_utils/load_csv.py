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


def load_csv(ifile):
    daily = pd.read_csv(ifile)
    daily['Crypto'] = 'BTC'
    for col in ['Date', 'Date_Pred']:
        daily[col] = pd.to_datetime(daily[col])
        daily[col] = daily[col].dt.strftime('%Y-%m-%d %H:%M:%S') + "+00:00"
    ut.df_to_db(daily, 'Changelly30dDailyPred')
    return


if __name__ == '__main__':
    ifile = r".\BTC_changelly_forecast.csv"
    load_csv(ifile)