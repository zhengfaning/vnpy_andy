from __future__ import absolute_import
import os
import sys
moudle_path = os.path.abspath('.')
sys.path.insert(0,moudle_path)

from vnpy.trader.database import database_manager
import datetime
import pandas as pd
import numpy as np
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


symbol = 'goog'
exchange = Exchange.SMART
start_date = datetime.datetime(2019,11,14)
end_date = datetime.datetime(2019,11,14)
calendar = get_calendar('NYSE')
schedule = calendar.schedule(start_date, end_date)
start = schedule.market_open[0]
end = schedule.market_close[-1]
req = HistoryRequest(
    symbol=symbol,
    exchange=exchange,
    interval=Interval.MINUTE,
    start=start,
    end=end
)

data = rqdata_client.query_history(req)
print(data)

# data = database_manager.load_bar_data(
#         symbol, exchange, Interval.MINUTE, start_date, end_date
#     )
