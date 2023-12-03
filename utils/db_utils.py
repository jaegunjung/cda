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

from datetime import datetime
import pandas as pd
import sqlalchemy as sa
from contextlib import ExitStack

# Override default settings
try:
    from utils.settings_local import *
except ImportError:  # pragma nocover
    pass


CHUNK_SIZE = 10000


def con_to_mssql() -> sa.create_engine:
    """
    Establish connection using ODBC. If it is to read, use pyodbc. If the connection is to update database,
    use sqlalchemy's create_engine.
    :return: return a method of connection.
    """
    connection_uri = sa.engine.url.URL.create(
        "mssql+pyodbc",
        host=SERVER_NAME,
        database=DBNAME,
        query={"driver": 'ODBC Driver 17 for SQL Server'},
    )
    sql_engine = sa.create_engine(connection_uri)
    return sql_engine


CON = con_to_mssql()


def df_to_db(df: pd.DataFrame, table: str, cursor = None) -> None:
    """
    Save df to the database. It adds DateTmModified column.
    :param df: input pandas dataframe from test data
    :param table: DB table name to save to
    :param cursor: Use cursor in arg if passed in, otherwise create new cursor
    :return: None
    """
    # ExitStack() allows setting the context manager conditionally, in this case using arg cursor vs. new cursor
    with ExitStack() as stack:
        if not cursor:
            cursor = stack.enter_context(CON.raw_connection().cursor())
        cols = df.columns
        cursor.fast_executemany = True
        cursor.executemany("INSERT INTO {0} ({1}) VALUES ({2})".
                           format(table, ', '.join(cols.tolist()), ', '.join(['?']*len(df.columns))),
                           [tuple(l) for l in df.values])
    return None


def query_db(q: str):
    """
    Query and return the results as pandas dataframe.
    :param q: SQL query text string
    :return: pandas dataframe
    """
    with CON.raw_connection().cursor() as cursor:
        cursor.execute("set NOCOUNT ON")
    return pd.read_sql(q, CON)
