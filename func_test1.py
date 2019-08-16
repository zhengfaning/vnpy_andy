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

def test1():
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
    print(dt)
    print(close)
    ax.plot(dt,close)
    # print(df.close.values)
    sma5 = talib.SMA(close, timeperiod = 5) 
    ax.plot(dt,sma5)
    sma10 = talib.SMA(close, timeperiod = 10) 
    ax.plot(dt,sma10)
    v_list, p_list = func_test3.calc(close,0.0003)
    for i in range(len(p_list)):
        p = p_list[i]
        ax.plot([dt[p]], [close[p]], 'o')
        ax.annotate(close[p], xy=(dt[p], close[p]))
    
    plt.show()

class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(390)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

def test2():
    req = HistoryRequest(
        exchange=Exchange.SMART,
        symbol="goog",
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,8,9,9),
        end=datetime.datetime(2019,8,10,4)
    )
    
    bar_data = rq.rqdata_client.query_history(req)
    tb = TestBar()
    date = []
    for v in bar_data:
        tb.am.update_bar(v)
        date.append(v.datetime)

    dt = date
    close = tb.am.close_array
    rect1 = [0.14, 0.35, 0.77, 0.6] # [左, 下, 宽, 高] 规定的矩形区域 （全部是0~1之间的数，表示比例）
    rect2 = [0.14, 0.05, 0.77, 0.2]
    fig  = plt.figure()
    ax1 = plt.axes(rect1)
    ax2 = plt.axes(rect2)
    # ax1 = fig.add_subplot(2,1,1)
    print(dt)
    print(close)
    ax1.plot(dt,close)
    

    v_list, p_list = tb.am.wave()
    for i in range(len(p_list)):
        p = p_list[i]
        ax1.plot([dt[p]], [close[p]], 'o')
        ax1.annotate(close[p], xy=(dt[p], close[p]))
    print(close)
    sma120 = talib.SMA(close, timeperiod = 60) 
    ax1.plot(dt,sma120)
    # ax2 = fig.add_subplot(2,1,2)
    kdj_data = tb.am.kdj()
    ax2.plot(dt,kdj_data["k"], "r")
    ax2.plot(dt,kdj_data["d"], "b")
    ax2.plot(dt,kdj_data["j"], "y")
    

    # ax2 = fig.add_subplot(2,1,2)
    
    
    plt.show()

if __name__ == "__main__":
    test2()


