from __future__ import absolute_import
import os
import sys
moudle_path = os.path.abspath('.')
sys.path.insert(0,moudle_path)

from vnpy.trader.setting import SETTINGS,get_settings
SETTINGS['database.driver'] = "bcolz"
SETTINGS['database.database'] = "bcolz_meta.db"

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
import numpy as np

US_EQUITIES_MINUTES_PER_DAY = 390
d = ['open', 'high', 'low']
ds = [1,4,6]
dct = dict(zip(d, map(lambda x:x+1, ds)))
print(dct)

class Store:
    def __init__(self, rootdir):
        super().__init__()
        self.calendar = get_calendar('NYSE')
        self.dest = rootdir
        if not os.path.exists(self.dest):
            os.makedirs(self.dest)
    
    def parse_time(self, data):
        return data[0].datetime,data[-1].datetime
    
    def write_data(self, data):
        start,end = self.parse_time(data)
        start = start.astimezone (pytz.utc)
        end = end.astimezone (pytz.utc)
        start_date = minute_to_session_label(self.calendar, start)
        end_date = minute_to_session_label(self.calendar, end)
        ndata = list(map(lambda x: {'open':x.open_price, 'high':x.high_price,'low':x.low_price,'close':x.close_price,'volume':x.volume},data))
        index = list(map(lambda x: x.datetime.astimezone(pytz.utc),data))
        df = pd.DataFrame(ndata, index=index)
        
        # dt = local_tz.localize(start, is_dst=None)

        
        self.writer = BcolzMinuteBarWriter(
            self.dest,
            self.calendar,
            start_date,
            end_date,
            US_EQUITIES_MINUTES_PER_DAY,
        )
        self.writer.write_sid(1, df)
        # self.reader = BcolzMinuteBarReader(self.dest)
        
        

        


symbol = 'fb'
exchange = Exchange.SMART
interval = Interval.MINUTE
start_date = datetime.datetime(2019,11,13,14,30, tzinfo=pytz.utc)
end_date = datetime.datetime(2019,12,6,20,0, tzinfo=pytz.utc)
x = pd.Timestamp(start_date)
calendar = get_calendar('NYSE')
schedule = calendar.schedule(start_date, end_date)


# for s in schedule.iterrows():
#     rr = pd.date_range(s[1].market_open, s[1].market_close, freq='1min')
#     i = s[1].market_close - s[1].market_open
#     print(i)
#     print(rr)
def test():
    shape = 10, 1
    out = np.full(shape, np.nan)
    print(out)

def write():
    req = HistoryRequest(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.MINUTE,
        start=start_date,
        end=end_date
    )

    data = rqdata_client.query_history(req)
    database_manager.save_bar_data(data)

def read():
    data = database_manager.load_bar_data(symbol, exchange, interval, start_date, end_date)
    print(data)

def diff():
    req = HistoryRequest(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.MINUTE,
        start=start_date,
        end=end_date
    )

    data = rqdata_client.query_history(req)
    print(data)

# write()
read()
# store.write_data(data)

# data = database_manager.load_bar_data(
#         symbol, exchange, Interval.MINUTE, start_date, end_date
#     )
