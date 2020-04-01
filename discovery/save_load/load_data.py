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

class Store:
    def __init__(self, rootdir):
        super().__init__()
        self.calendar = get_calendar('NYSE')
        self.dest = rootdir
        if not os.path.exists(self.dest):
            os.makedirs(self.dest)
    
    def parse_time(self, data):
        return data[0].datetime,data[-1].datetime
    
    def read_data(self, start, end):

        self.reader = BcolzMinuteBarReader(self.dest)
        start = start.astimezone (pytz.utc)
        end = end.astimezone (pytz.utc)
        start = pd.Timestamp(start, tz='UTC')
        end = pd.Timestamp(end, tz='UTC')
        data = self.reader.load_raw_arrays(['open', 'high', 'low', 'close', 'volume'], start, end, [1])
        print(data)

    def find_position_of_minute(self, market_opens, market_closes, minute_val, minutes_per_day, forward_fill):
        """
        Finds the position of a given minute in the given array of market opens.
        If not a market minute, adjusts to the last market minute.

        Parameters
        ----------
        market_opens: numpy array of ints
            Market opens, in minute epoch values.

        market_closes: numpy array of ints
            Market closes, in minute epoch values.

        minute_val: int
            The desired minute, as a minute epoch.

        minutes_per_day: int
            The number of minutes per day (e.g. 390 for NYSE).

        forward_fill: bool
            Whether to use the previous market minute if the given minute does
            not fall within an open/close pair.

        Returns
        -------
        int: The position of the given minute in the market opens array.

        Raises
        ------
        ValueError
            If the given minute is not between a single open/close pair AND
            forward_fill is False.  For example, if minute_val is 17:00 Eastern
            for a given day whose normal hours are 9:30 to 16:00, and we are not
            forward filling, ValueError is raised.
        """
        

        market_open_loc = \
            np.searchsorted(market_opens, minute_val, side='right') - 1
        market_open = market_opens[market_open_loc]
        market_close = market_closes[market_open_loc]

        if not forward_fill and ((minute_val - market_open) >= minutes_per_day):
            raise ValueError("Given minute is not between an open and a close")

        delta = int(minute_val - market_open, market_close - market_open)

        return (market_open_loc * minutes_per_day) + delta

        


symbol = 'goog'
exchange = Exchange.SMART
start_date = datetime.datetime(2019,11,14)
end_date = datetime.datetime(2019,11,15)
datetime.timedelta
calendar = get_calendar('NYSE')
schedule = calendar.schedule(start_date, end_date)
start = schedule.market_open[0]
end = schedule.market_close[-1]
# end_date = minute_to_session_label(calendar, end_date)
# start = start_date + datetime.timedelta(calendar.open_time)


# req = HistoryRequest(
#     symbol=symbol,
#     exchange=exchange,
#     interval=Interval.MINUTE,
#     start=start_date,
#     end=end_date
# )

# data = rqdata_client.query_history(req)

path = os.path.abspath('./test_data')

store = Store(path)

store.read_data(start, end)

# data = database_manager.load_bar_data(
#         symbol, exchange, Interval.MINUTE, start_date, end_date
#     )
