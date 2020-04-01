from __future__ import absolute_import
import os
import sys
moudle_path = os.path.abspath('.')
sys.path.insert(0,moudle_path)

from vnpy.trader.database import database_manager
import datetime
import pandas as pd
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.utility import extract_vt_symbol
from vnpy.trader.rqdata import rqdata_client
from vnpy.trader.object import HistoryRequest
from pandas_market_calendars import get_calendar
from vnpy.bcolz_table.minute_bars import BcolzMinuteBarWriter, BcolzMinuteBarReader, minute_to_session_label
import shutil
from dateutil.tz import tzlocal
import pytz
from typing import List, Optional, Sequence, Type

US_EQUITIES_MINUTES_PER_DAY = 390
        


symbol = 'goog'
exchange = Exchange.SMART
start_date = datetime.datetime(2019,11,25,20)
end_date = datetime.datetime(2019,12,3,20)

def from_bar(bar):
    """
    Generate DbBarData object from BarData.
    """
    db_bar = dict(
        index = bar.datetime,
        volume = bar.volume,
        open_int = bar.open_interest,
        open = bar.open_price,
        high = bar.high_price,
        low = bar.low_price,
        close = bar.close_price
    )

    return db_bar

req = HistoryRequest(
    symbol=symbol,
    exchange=exchange,
    interval=Interval.MINUTE,
    start=start_date,
    end=end_date
)

def get_date_range(start_date: datetime.datetime, end_date: datetime.datetime):
    calendar = get_calendar('NYSE')
    count = end_date.year - start_date.year 
    base_year = start_date.year
    pair = []
    for i in range(count + 1):
        year = base_year + i
        if i == 0:
            start_t = start_date
        else:
            start_t = datetime.datetime(year=year, month=1, day=1)
        
        if i == count:
            end_t = end_date
        else:
            end_t = datetime.datetime(year=year+1, month=1, day=1) - datetime.timedelta(seconds=1)
        
        schedule = calendar.schedule(start_t, end_t)
        pair.append((schedule.market_open[0], schedule.market_close[-1]))
    return pair

data = rqdata_client.query_history(req)

ds = [from_bar(i) for i in data]
df = pd.DataFrame(ds)
df.set_index(['index'], inplace=True)
start = df.index[0]
end = df.index[-1]

pair = get_date_range(start, end)
# row_data = list(map(lambda x: {'index':x.datetime.astimezone(pytz.utc), 'open':x.open_price, 'high':x.high_price,'low':x.low_price,'close':x.close_price,'volume':x.volume},data))
# # index = list(map(lambda x: x.datetime.astimezone(pytz.utc),data))
# df = pd.DataFrame(row_data)
# df.set_index(['index'], inplace=True)
for p in pair:
    year = p[0].year
    trun_data = df.truncate(p[0], p[1])
# select_data = df.truncate(datetime.datetime(2019,11,25,20), datetime.datetime(2019,11,28,20))




print(select_data)
print(df)
