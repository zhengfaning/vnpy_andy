import pandas_market_calendars as mcal
import pandas as pd
import time
import datetime
import pytz
from dateutil.tz import tzlocal
print(time.timezone)
print(time.tzname)
START_DATE = pd.Timestamp('2014-01-06', tz='utc')
END_DATE = pd.Timestamp('2014-01-10', tz='utc')
# US Stock Exchanges (includes NASDAQ)
nyse = mcal.get_calendar('NYSE')
print(nyse.tz)
# 名字
name = nyse.name
# 时区
tz = nyse.tz
holidays = nyse.holidays()
print(holidays.holidays[-5:])
# 获取范围内有效日期
print(nyse.valid_days(start_date='2016-12-20', end_date='2017-01-10'))
print(nyse.open_time)
print(nyse.close_time)
calendar=nyse
schedule = nyse.schedule(start_date='2019-10-30', end_date='2019-12-02')
# slicer = calendar.schedule.index.slice_indexer(
#     self.start_session,
#     self.end_session,
# )
# 相等于
schedule = nyse.schedule(start_date='2019-10-30', end_date='2019-12-02')
market_opens = schedule.market_open
market_closes = schedule.market_close


# 计划
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
