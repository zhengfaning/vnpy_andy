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


US_EQUITIES_MINUTES_PER_DAY = 390

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
        
        

        


symbol = 'goog'
exchange = Exchange.SMART
start_date = datetime.datetime(2019,11,25,20)
end_date = datetime.datetime(2019,12,3,20)



req = HistoryRequest(
    symbol=symbol,
    exchange=exchange,
    interval=Interval.MINUTE,
    start=start_date,
    end=end_date
)

data = rqdata_client.query_history(req)
row_data = list(map(lambda x: {'index':x.datetime.astimezone(pytz.utc), 'open':x.open_price, 'high':x.high_price,'low':x.low_price,'close':x.close_price,'volume':x.volume},data))
# index = list(map(lambda x: x.datetime.astimezone(pytz.utc),data))
df = pd.DataFrame(row_data)
df.set_index(['index'], inplace=True)
select_data = df.truncate(datetime.datetime(2019,11,25,20), datetime.datetime(2019,11,28,20))
print(select_data)
print(df)

# path = os.path.abspath('./test_data')
# if os.path.exists(path):
#     shutil.rmtree(path)

# store = Store(path)

# store.write_data(data)

# data = database_manager.load_bar_data(
#         symbol, exchange, Interval.MINUTE, start_date, end_date
#     )
