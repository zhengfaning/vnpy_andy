
import time, datetime


from pandas_market_calendars import get_calendar



def get_date_range(start_date, end_date):
    calendar = get_calendar('NYSE')
    count = end.year - start.year 
    base_year = start.year
    pair = []
    for i in range(count + 1):
        year = base_year + i
        if i == 0:
            start_t = start
        else:
            start_t = datetime.datetime(year=year, month=1, day=1)
        
        if i == count:
            end_t = end
        else:
            end_t = datetime.datetime(year=year+1, month=1, day=1) - datetime.timedelta(seconds=1)
        
        schedule = calendar.schedule(start_t, end_t)
        pair.append((schedule.market_open[0], schedule.market_close[-1]))

start = datetime.datetime(2016, 5, 1)
end = datetime.datetime(2016, 6, 1)
pair = get_date_range(start, end)
print(pair)
        