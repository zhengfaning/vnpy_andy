from trading_calendars import get_calendar
import pandas as pd

START_DATE = pd.Timestamp('2014-01-06', tz='utc')
END_DATE = pd.Timestamp('2014-01-10', tz='utc')
# US Stock Exchanges (includes NASDAQ)
calendar = get_calendar('XNYS')
sessions = calendar.sessions_in_range(START_DATE, END_DATE)
minutes = calendar.minutes_for_sessions_in_range(
    START_DATE, END_DATE,
)
start_date = calendar.first_session
end_date = calendar.last_session

# London Stock Exchange
london_calendar = get_calendar('XLON')
# Toronto Stock Exchange
toronto_calendar = get_calendar('XTSE')
# Tokyo Stock Exchange
tokyo_calendar = get_calendar('XTKS')
# Frankfurt Stock Exchange
frankfurt_calendar = get_calendar('XFRA')

# US Futures
us_futures_calendar = get_calendar('us_futures')
# Chicago Mercantile Exchange
cme_calendar = get_calendar('CMES')
# Intercontinental Exchange
ice_calendar = get_calendar('IEPA')
# CBOE Futures Exchange
cfe_calendar = get_calendar('XCBF')
# Brazilian Mercantile and Futures Exchange
bmf_calendar = get_calendar('BVMF')