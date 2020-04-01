import pandas_market_calendars as mcal
import pandas as pd
import time
import datetime
import pytz
import numpy as np
from dateutil.tz import tzlocal
from trading_calendars import get_calendar
import datetime

nyse = mcal.get_calendar('NYSE')

start_date = '2017-04-10'  
end_date = '2018-01-05'

schedule = nyse.schedule(start_date, start_date)
schedule = nyse.schedule(start_date, end_date)
holidays = nyse.holidays()
xxx1 = holidays.rollforward(start_date)
xxx2 = holidays.rollback(end_date)
t = pd.Timestamp(end_date, tz='UTC')

t = pd.Timestamp(t.to_pydatetime() - datetime.timedelta(days=1))
valid_days = nyse.valid_days(start_date, end_date)
valid_days2 = pd.date_range(start_date, end_date, freq=nyse.holidays(), normalize=True, tz=nyse.tz, closed='left')
print(schedule.market_open[-1])
print(valid_days[-1])
# one
START_DATE = pd.Timestamp('2014-01-06', tz='utc')
END_DATE = pd.Timestamp('2014-01-10', tz='utc')
# US Stock Exchanges (includes NASDAQ)

schedule = nyse.schedule(start_date='2019-10-30', end_date='2019-12-02')
market_opens = schedule.market_open
market_closes = schedule.market_close
xxx = market_opens.values.astype('datetime64[m]').astype(np.int64).tolist()

# two
schedule = nyse.schedule(start_date='2019-10-30', end_date='2019-12-02')

print(schedule)
# 获取本地时区
local_tz = tzlocal()
# 遍历计划,替换时区
for index, row in schedule.iterrows():
    print(index)
    t1 = row['market_open']
    nt1 = t1.astimezone(local_tz)
    print(t1)
    print(row['market_close'])
