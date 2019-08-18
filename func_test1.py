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
from vnpy.gateway.hbdm.hbdm_gateway import HbdmGateway,symbol_type_map
from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine
from bokeh.models import Label,LabelSet,ColumnDataSource

# from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.app.cta_strategy import (
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from bokeh.embed import file_html
from bokeh.resources import CDN

years = mdates.YearLocator()   # every year
months = mdates.MonthLocator()  # every month
years_fmt = mdates.DateFormatter('%Y')

class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(500)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

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


def test2():
    req = HistoryRequest(
        exchange=Exchange.SMART,
        symbol="goog",
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,8,3,9),
        end=datetime.datetime(2019,8,10,4)
    )
    
    bar_data = rq.rqdata_client.query_history(req)
    # bar_data = bar_data[-200:]
    tb = TestBar()
    date = []
    for v in bar_data:
        tb.am.update_bar(v)
        date.append(v.datetime)

    dt = tb.am.time_array
    close = tb.am.close_array
    rect1 = [0.14, 0.35, 0.77, 0.6] # [左, 下, 宽, 高] 规定的矩形区域 （全部是0~1之间的数，表示比例）
    rect2 = [0.14, 0.05, 0.77, 0.2]
    fig  = plt.figure(figsize=(42,10), dpi=100)
    ax1 = plt.axes(rect1)
    ax2 = plt.axes(rect2)
    # ax1 = fig.add_subplot(2,1,1)

    def format_date(x,pos=None):
    # 由于前面股票数据在 date 这个位置传入的都是int
    # 因此 x=0,1,2,...
    # date_tickers 是所有日期的字符串形式列表
        print(x)
        if x<0 or x>len(dt)-1:
            return ''
        print(dt[int(x)])
        return dt[int(x)]
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(6))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    ax1.plot(close)
    # ax1.plot(dt,close)
    ax1.grid(True)
    # datemin = np.datetime64(dt[0], 'Y')
    # datemax = np.datetime64(dt[-1], 'Y') + np.timedelta64(1, 'Y')
    # ax1.set_xlim(datemin, datemax)
    ax1.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    # ax1.format_ydata = lambda x: '$%1.2f' % x  # format the price.
    ax1.grid(True)
    # fig.autofmt_xdate()
    # v_list, p_list = tb.am.wave()
    # for i in range(len(p_list)):
    #     p = p_list[i]
    #     ax1.plot([p], [close[p]], 'o')
    #     ax1.annotate(close[p], xy=(p, close[p]))

    sma120 = talib.SMA(close, timeperiod = 120) 
    # ax2 = fig.add_subplot(2,1,2)
    kdj_data = tb.am.kdj()
    ax2.plot(kdj_data["k"], "r")
    ax2.plot(kdj_data["d"], "b")
    # ax2.plot(dt,kdj_data["j"], "y")
    # ax2 = fig.add_subplot(2,1,2)
    # plt.savefig('1.png')
    plt.show()



def test3():
    event_engine = EventEngine()
    gate = HbdmGateway(event_engine)

    setting = {
        "API Key": "mjlpdje3ld-701b9727-9ae52956-3ef1e",
        "Secret Key": "b4df4824-124ec192-55786af1-a397a",
        "会话数": 3,
        "代理地址": "127.0.0.1",
        "代理端口": "1080",
    }
    gate.connect(setting)
    time.sleep(3)
    print(symbol_type_map)
    if len(symbol_type_map) <= 0:
        return

    req = HistoryRequest(
        exchange=Exchange.HUOBI,
        symbol="BCH190830",
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,8,1,0),
        end=datetime.datetime(2019,8,17,16)
    )
    bar_data = gate.query_history(req)
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
    sma120 = talib.SMA(close, timeperiod = 120) 
    ax1.plot(dt,sma120)
    # ax2 = fig.add_subplot(2,1,2)
    kdj_data = tb.am.kdj()
    ax2.plot(dt,kdj_data["k"], "r")
    ax2.plot(dt,kdj_data["d"], "b")
    # gate.query_history(req)

def test4():
    from bokeh.io import output_file, show
    from bokeh.plotting import figure

    req = HistoryRequest(
            exchange=Exchange.SMART,
            symbol="goog",
            interval=Interval.MINUTE,
            start=datetime.datetime(2019,8,3,9),
            end=datetime.datetime(2019,8,10,4)
        )
    
    bar_data = rq.rqdata_client.query_history(req)
    # bar_data = bar_data[-200:]
    tb = TestBar()
    date = []
    for i,v in enumerate(bar_data):
        tb.am.update_bar(v)
        date.append(i)

    dt = tb.am.time_array
    close = tb.am.close_array
    #Create the time series plot
    plot = figure(plot_width=1800, plot_height=900, x_axis_label = 'date', y_axis_label = 'High Prices')

    plot.line(x = date, y = close)
    source = ColumnDataSource(data=dict(height=[66, 71, 72, 68, 58, 62],
                                    weight=[165, 189, 220, 141, 260, 174],
                                    names=['Mark', 'Amir', 'Matt', 'Greg',
                                           'Owen', 'Juan']))

    labels = LabelSet(x='weight', y='height', text='names', level='glyph',
                x_offset=5, y_offset=5, source=source, render_mode='canvas')

    citation = Label(x=70, y=70, x_units='screen', y_units='screen',
                    text='Collected by Luke C. 2016-04-01', render_mode='css',
                    border_line_color='black', border_line_alpha=1.0,
                    background_fill_color='white', background_fill_alpha=1.0)

    plot.add_layout(labels)
    plot.add_layout(citation)
    plot.triangle(x=100,y=1200)
    
    html = file_html(plot, CDN, "my plot")
    print(html)
    #Output the plot
    # output_file('pandas_time.html')
    show(plot)
if __name__ == "__main__":
    test4()


