
import pandas as pd
import time
import datetime
import pytz
from dateutil.tz import tzlocal
from trading_calendars import get_calendar


calendar = get_calendar('XNYS')

start_date = '2017-04-10'  
end_date = '2018-01-05'

start_date_v = calendar.minute_to_session_label(pd.Timestamp(start_date, tz='UTC'), direction='previous')
end_date_v = calendar.minute_to_session_label(pd.Timestamp(end_date, tz='UTC'), direction='previous')

slicer = calendar.schedule.index.slice_indexer(
    start_date_v,
    end_date_v,
)
schedule = calendar.schedule[slicer]
market_opens = schedule.market_open
market_closes = schedule.market_close
o,c = calendar.open_and_close_for_session(end_date_v)
# minute_to_session_label = 计划最靠近的日期(下一个)
print(start_date_v,end_date_v)
