
import pandas as pd
from datetime import time
import datetime
import pytz
from dateutil.tz import tzlocal
from pandas_market_calendars import get_calendar

def minute_to_session_label(calendar, date, direction='next'):
    holidays = calendar.holidays()
    current = pd.Timestamp(date, tz='UTC')
    l = holidays.rollback(pd.Timestamp(date, tz='UTC') - datetime.timedelta(days=1))
    r = holidays.rollforward(pd.Timestamp(date, tz='UTC') + datetime.timedelta(days=1))
    schedule = calendar.schedule(l, r)
    market_opens = schedule.market_open
    market_closes = schedule.market_close
    index = 1
    value = None
    if direction == 'previous':
        # t = pd.Timestamp(pd.Timestamp(date, tz='UTC') - datetime.timedelta(days=1))
        if current > market_opens[index] and current < market_closes[index]:
            value = current.date()
        else:
            value = l.date()
        # t = pd.Timestamp(date)
        # dt = t.date()
        # return holidays.rollback(dt)
    else:
        if current > market_opens[index] and current < market_closes[index]:
            value = current.date()
        else:
            value = r.date()
        # t = pd.Timestamp(date)
        # dt = t.date()
        # return holidays.rollforward(date)
    return pd.Timestamp(value)

# cal = get_calendar('NYSE')
calendar = get_calendar('NYSE')
# calendar = get_calendar('NYSE')
start_date = pd.Timestamp('2019-07-10') + datetime.timedelta(hours=13, minutes=31)
end_date = pd.Timestamp('2019-12-05')

start_date_v = minute_to_session_label(calendar, start_date, direction='previous')
end_date_v = minute_to_session_label(calendar, end_date, direction='previous')

schedule = calendar.schedule(start_date_v, end_date_v)
market_opens = schedule.market_open
market_closes = schedule.market_close
print(market_opens[0], market_opens[-1])
# o,c = calendar.open_and_close_for_session(end_date_v)
# minute_to_session_label = 计划最靠近的日期(下一个)
print(start_date_v,end_date_v)
