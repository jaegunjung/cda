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

import datetime as dt
from typing import Callable


def datetag(year: bool = False) -> str:
    """
    Return datetag. For example, 0101_010000, or 230101_010000 if year = True
    :param year: If True, return with last two digits of year.
    :return: date_time string
    """
    form = "%y%m%d_%H%M%S" if year else "%m%d_%H%M%S"
    return dt.datetime.now().strftime(form)


def count_n_days(start: str, end: str) -> int:
    """
    Return no of days between end and start
    :param start: YYYY-MM-DD
    :param end: YYYY-MM-DD
    :return:
    """

    # Convert text to datetime objects
    start_date_obj = dt.datetime.strptime(start, '%Y-%m-%d')
    end_date_obj = dt.datetime.strptime(end, '%Y-%m-%d')

    # Calculate the difference in days
    return (end_date_obj - start_date_obj).days


def time_to_run(func: Callable, *args, **kwargs) -> None:
    """
    print time to take to run func in second
    :param func: function to call
    :param args: arguments
    :param kwargs: keyword arguments
    :return: None
    """
    beg_time = dt.datetime.now()
    func(*args, **kwargs)
    end_time = dt.datetime.now()
    print(f"{func.__name__} takes {(end_time - beg_time).seconds} seconds to complete.")
    return None
