import app as vnpy_app
from time import sleep
import json
import handler
import script_handler
import time, datetime
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Exchange, Interval
from kdj import calc_kdj
import pandas as pd
import matplotlib.pyplot as plt
import draw_test
import func_test3
import numpy as np 
import talib
# from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.app.cta_strategy import (
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)

class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(200)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)


if __name__ == "__main__":
    rd = pd.date_range(start='2019-1-09', end='2019-1-10',periods=10)
    print(rd)
    print(pd.to_datetime(rd))
    req = HistoryRequest(
        exchange=Exchange.SMART,
        symbol="goog",
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,8,9,9),
        end=datetime.datetime(2019,8,10,4)
    )
    df_data = rq.rqdata_client.get_data("goog", begin="2019-08-09 09:00:00", end="2019-08-10 04:00:00")
    df = df_data[-100:]
    # df = df_data
    fig  = plt.figure()
    ax = fig.add_subplot(1,1,1)
    date = []
    for v in df.time.values:
        d = datetime.datetime.fromtimestamp(v / 1000)
        date.append(d)
    # dt = pd.DatetimeIndex(date)
    dt = date
    close = df.close.values
    ax.plot(dt,close)
    # print(df.close.values)
    sma5 = talib.SMA(close, timeperiod = 5) 
    ax.plot(dt,sma5)
    sma10 = talib.SMA(close, timeperiod = 10) 
    ax.plot(dt,sma10)
    v_list, p_list = func_test3.calc(close)
    for i in range(len(p_list)):
        p = p_list[i]
        ax.plot([dt[p]], [close[p]], 'o')
        ax.annotate(close[p], xy=(dt[p], close[p]))
    print(df.close.values)
    plt.show()
    # print(df.close)
    # for item in df.close:
    #     print(item)
    # draw_test.plot_candle_stick("google", df, True)
    # bar_data = rq.rqdata_client.query_history(req)

    # tb = TestBar()
    # for v in bar_data:
    #     tb.am.update_bar(v)


