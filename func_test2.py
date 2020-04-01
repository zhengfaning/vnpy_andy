from vnpy.bcolz_table.minute_bars import BcolzMinuteBarWriter, BcolzMinuteBarReader
from pandas import DataFrame, Timestamp
from pandas_market_calendars import get_calendar
import os

TEST_CALENDAR_START = Timestamp('2014-06-02', tz='UTC')
TEST_CALENDAR_STOP = Timestamp('2015-12-31', tz='UTC')
US_EQUITIES_MINUTES_PER_DAY = 390

class TestCase:

    def __init__(self):
        self.trading_calendar = get_calendar('NYSE')
        self._schedule = self.trading_calendar.schedule(
            TEST_CALENDAR_START,
            TEST_CALENDAR_STOP
        )
        self.market_opens = self._schedule.market_open
        self.test_calendar_start = TEST_CALENDAR_START
        minute = self.market_opens[self.test_calendar_start]
        self.dest = './'
        

    def test_write_one_ohlcv_with_ratios(self):
            minute = self.market_opens[self.test_calendar_start]
            sid = 1
            data = DataFrame(
                data={
                    'open': [10.0],
                    'high': [20.0],
                    'low': [30.0],
                    'close': [40.0],
                    'volume': [50.0],
                },
                index=[minute],
            )

            # Create a new writer with `ohlc_ratios_per_sid` defined.
            writer_with_ratios = BcolzMinuteBarWriter(
                self.dest,
                self.trading_calendar,
                TEST_CALENDAR_START,
                TEST_CALENDAR_STOP,
                US_EQUITIES_MINUTES_PER_DAY,
                ohlc_ratios_per_sid={sid: 25},
            )
            writer_with_ratios.write_sid(sid, data)
            reader = BcolzMinuteBarReader(self.dest)

            open_price = reader.get_value(sid, minute, 'open')
            self.assertEquals(10.0, open_price)

            high_price = reader.get_value(sid, minute, 'high')
            self.assertEquals(20.0, high_price)

            low_price = reader.get_value(sid, minute, 'low')
            self.assertEquals(30.0, low_price)

            close_price = reader.get_value(sid, minute, 'close')
            self.assertEquals(40.0, close_price)

            volume_price = reader.get_value(sid, minute, 'volume')
            self.assertEquals(50.0, volume_price)

case = TestCase()
print('ok')