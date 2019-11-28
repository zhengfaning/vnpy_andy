from vnpy.trader.object import BarData

from vnpy.trader.utility import ArrayManager
from pytz import timezone
import datetime
import math


class ClockManager:
    eastern = timezone('US/Eastern')

    def __init__(self, start_time: datetime.time, end_time: datetime.time,
                 interval: datetime.timedelta = None, on_time_check=None):
        self.time_offset = datetime.timedelta(hours=start_time.hour, minutes=start_time.minute,
                                              seconds=start_time.second)
        et = datetime.timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second)
        self.total_time = et - self.time_offset
        self.on_time_check = on_time_check
        self.interval = interval

    # def convert_time(self, unix_time):
    #     return datetime.datetime.fromtimestamp(unix_time, self.eastern)

    def market_start(self):
        now = datetime.datetime.now(tz=self.eastern)
        return datetime.datetime(now.year,now.month,now.day) + self.time_offset

    def get_run_time(self, now:datetime.datetime):
        now_delay = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        rt = now_delay - self.time_offset
        return rt

    def on_bar(self, bar: BarData):
        if self.interval is None:
            return
        t = bar.datetime
        now = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        rt = now - self.time_offset
        if rt.total_seconds() % self.interval.total_seconds() == 0:
            if self.on_time_check is not None:
                scale = self.get_time_scale(t)
                for callback in self.on_time_check:
                    callback(scale, rt.total_seconds() / 60)

    def get_time_scale(self, t: datetime.datetime):
        now = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        rt = now - self.time_offset

        scale = rt.total_seconds() / self.total_time.total_seconds()
        return scale
