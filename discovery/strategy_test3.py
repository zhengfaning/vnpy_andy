import app as vnpy_app
from time import sleep
import sys
import json
import handler
import script_handler
import time, datetime
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.gateway.hbdm.hbdm_gateway import HbdmGateway,symbol_type_map
from vnpy.gateway.bitmex.bitmex_gateway import BitmexGateway

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.algorithm import Algorithm
import pandas as pd
import matplotlib
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
from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine
from vnpy.app.cta_strategy.strategies.kdj_120ma_strategy import Kdj120MaStrategy
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.algo_trading import AlgoTradingApp
from vnpy.trader.constant import Direction, Offset
from bokeh.io import output_file, show
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Label
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.palettes import d3, brewer, mpl
from bokeh.core.enums import colors
from bokeh.layouts import column, gridplot
from bokeh.models import WheelZoomTool
palettes_colors = d3["Category20"][20]

# output_file("dark_minimal.html")
# curdoc().theme = 'dark_minimal'
# from bokeh.models import Arrow, OpenHead, NormalHead, VeeHead


matplotlib.rcParams['font.sans-serif'] = ['SimHei'] 
matplotlib.rcParams['font.family']='sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False

g_plot_mark = {
    Direction.LONG:"^",
    Direction.SHORT:"v",
    Direction.NET:">",
}

g_mark_color = {
    Offset.OPEN:colors.named.red,
    Offset.CLOSE:colors.named.green,
    Offset.CLOSETODAY:colors.named.green,
    Offset.CLOSEYESTERDAY:colors.named.green
}
class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(390)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

def download(stock_name):
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()
    backtester_engine.run_downloading(stock_name, Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,22,5))
    print("download 完成")

def test1():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()

    # backtester_engine.run_downloading("goog.SMART", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,10,5))
    strategy_name = "Kdj120MaStrategy"
    stock_name = "amd.SMART"
    # contracts = engine.get_all_contracts()

    backtester_engine.run_backtesting(strategy_name,
                                 stock_name,
                                 Interval.MINUTE,
                                 datetime.datetime(2019,7,15,20),
                                 datetime.datetime(2019,8,19,5),
                                 rate=0.29/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"ma_window":30, "wave_window":0.05, "bar_min":1}      # 策略设置
                                 )
    
    result_df = backtester_engine.get_result_df()
    bar_data = backtester_engine.backtesting_engine.history_data
    
    date_index = {}
    close = []
    date = []
    for i,v in enumerate(bar_data):
        bar:BarData = v
        date_index[bar.datetime] = i
        date.append(bar.datetime)
        close.append(bar.close_price)


    # print(result_df.columns.values)
    df = pd.DataFrame(result_df, columns=["date","trade_count","start_pos","end_pos","turnover","commission","slippage", "trading_pnl", "holding_pnl","total_pnl","net_pnl"])
    calculate_statistics = backtester_engine.get_result_statistics()
    df = df.rename(columns={        
        "date": "日期",
        "trade_count":"成交笔数",
        "start_pos":"开盘持仓",  
        "end_pos":"收盘持仓",    
        "turnover":"成交额",     
        "commission":"手续费",   
        "slippage":"滑点",       
        "trading_pnl":"交易盈亏",
        "holding_pnl":"持仓盈亏",
        "total_pnl":"总盈亏",    
        "net_pnl":"净盈亏"})
    print(df)
    rect1 = [0.14, 0.35, 0.77, 0.6] # [左, 下, 宽, 高] 规定的矩形区域 （全部是0~1之间的数，表示比例）
    rect2 = [0.14, 0.05, 0.77, 0.2]
    fig  = plt.figure(figsize=(42,10), dpi=100)
    ax1 = plt.axes(rect1)
    ax2 = plt.axes(rect2)
    close = np.array(close)
    sma5 = talib.SMA(close, timeperiod = 5)
    sma10 = talib.SMA(close, timeperiod = 10)
    sma20 = talib.SMA(close, timeperiod = 20)
    sma120 = talib.SMA(close, timeperiod = 120)

    ax1.plot(close)

    ax1.plot(sma5, "-", linewidth=0.5)
    ax1.plot(sma10, "-", linewidth=0.5)
    ax1.plot(sma20, "-", linewidth=0.5)
    ax1.plot(sma120, "-", linewidth=0.5)

    
    for trade_list in result_df.trades:
        for item in trade_list:
            time = item.datetime
            p = date_index[time]
            direction: Direction = item.direction
            price = item.price
            offset:Offset = item.offset
            mark = g_plot_mark[direction]
            color = g_mark_color[offset]
            ax1.plot(p, price, mark, color=color)
            s="{}{}:{}".format(offset.value, direction.value, price)
            ax1.annotate(s, xy=(p, price))
            # ax1.annotate(s,xy=(p+5, price+0.7),xytext=(p,price),arrowprops=dict(arrowstyle="->",connectionstyle="arc3",color="r"))

    plt.show()

    # log_engine = main_engine.get_engine("log")
    # event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)

    # gate = HbdmGateway(event_engine)

    # setting = {
    #     "API Key": "mjlpdje3ld-701b9727-9ae52956-3ef1e",
    #     "Secret Key": "b4df4824-124ec192-55786af1-a397a",
    #     "会话数": 3,
    #     "代理地址": "127.0.0.1",
    #     "代理端口": "1080",
    # }
    # gate.connect(setting)
    # time.sleep(8)
    # print(symbol_type_map)
    # if len(symbol_type_map) <= 0:
    #     return

    # req = HistoryRequest(
    #     exchange=Exchange.HUOBI,
    #     symbol="BCH190830",
    #     interval=Interval.MINUTE,
    #     start=datetime.datetime(2019,8,1,0),
    #     end=datetime.datetime(2019,8,17,16)
    # )
    # bar_data = gate.query_history(req)

    # strategy = Kdj120MaStrategy(object(), "test_strategy", "goog", {"ma_window":10, "wave_window":0.05, "bar_min":3})
def test2():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()

    # backtester_engine.run_downloading("goog.SMART", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,10,5))
    strategy_name = "MultiTimeframeStrategy"
    # strategy_name = "MaLevelTrackStrategy"
    # stock_name = "BCH190830.HUOBI"
    stock_name = "amd.SMART"
    # stock_name = "XBTUSD.BITMEX"
    start_date = datetime.datetime(2019,7,1,20)
    end_date = datetime.datetime(2019,8,22,12)
    # start_date = datetime.datetime(2019,7,15,20)
    # end_date = datetime.datetime(2019,8,22,12)
    wave_window = 0.0001
    # contracts = engine.get_all_contracts()

    # tracker = {"bar_data":[], "trade_info":[]}
    tracker = {"bar_data":[], "trade_info":[], "ma_tag":[], "var":[], "var1":[], "var2":[], "trade_info":[], "ma_tag_ls":[]}
    backtester_engine.run_backtesting(strategy_name,
                                 stock_name,
                                 Interval.MINUTE,
                                 start_date,
                                 end_date,
                                 rate=2.9/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"ma_window":120, "wave_window":wave_window, "bar_min":1, "tracker":tracker}      # 策略设置
                                 )
    
    result_df = backtester_engine.get_result_df()
    bar_data = []
    if "bar_data" in tracker:
        bar_data = tracker["bar_data"]
    if len(bar_data) == 0:
        bar_data = backtester_engine.backtesting_engine.history_data
    
    date_index = {}
    close = []
    date = {}
    dt = []
    high = []
    low = []
    for i,v in enumerate(bar_data):
        bar:BarData = v
        date_index[bar.datetime] = i
        date[i] = bar.datetime.strftime("%m/%d %H:%M")
        close.append(bar.close_price)
        high.append(bar.high_price)
        low.append(bar.low_price)
        dt.append(i)

    dt_w = []
    data_w = []
    for item in tracker["trade_info"]:
        for value in item["wave"]:
            i_v = list(value.items())[0]
            index = date_index[i_v[0]]
            # v = close[index]
            dt_w.append(index)
            data_w.append(i_v[1])

    # print(result_df.columns.values)
    df = pd.DataFrame(result_df, columns=["date","trade_count","start_pos","end_pos","turnover","commission","slippage", "trading_pnl", "holding_pnl","total_pnl","net_pnl"])
    calculate_statistics = backtester_engine.get_result_statistics()
    df = df.rename(columns={        
        "date": "日期",
        "trade_count":"成交笔数",
        "start_pos":"开盘持仓",  
        "end_pos":"收盘持仓",    
        "turnover":"成交额",     
        "commission":"手续费",   
        "slippage":"滑点",       
        "trading_pnl":"交易盈亏",
        "holding_pnl":"持仓盈亏",
        "total_pnl":"总盈亏",    
        "net_pnl":"净盈亏"})
    print(df)
    tooltip_x = []
    tooltip_y = []
    tooltip_desc = []

    if "ma_tag_ls" in tracker:
        for item in tracker["ma_tag_ls"]:
            index = date_index[item[0]]
            tooltip_x.append(int(index))
            tooltip_y.append(item[1])
            desc = "{}  {:.2f}  {:.2f}".format(item[2], item[3], item[4])
            tooltip_desc.append(desc)


    source = ColumnDataSource(data=dict(
        x=tooltip_x,
        y=tooltip_y,
        desc=tooltip_desc,
    ))

    TOOLTIPS = [
        ("index", "$index"),
        ("(x,y)", "($x, $y)"),
        ("desc", "@desc"),
    ]

    plot = figure(aspect_scale=0.3, match_aspect=False,plot_width=1100, plot_height=450,x_axis_label="date", y_axis_label="high", tooltips=TOOLTIPS,
                   tools="pan,reset,save,wheel_zoom,xwheel_zoom,ywheel_zoom")
    close = np.array(close)
    high = np.array(high)
    low = np.array(low)
    plot.xaxis.major_label_overrides = date
    # plot.line(x = dt, y = close, color=palettes_colors[0], line_width=1.5, source=source)
    plot.circle("x", "y", color=palettes_colors[0], size=7, source=source)
    
    sma1 = talib.SMA(close, timeperiod = 2)
    # sma_x = talib.SMA(close, timeperiod = 5)
    w,w_pos = Algorithm.wave(close, wave_window)
    # plot.circle(x=w_pos, y=w, color=colors.named.black, legend="all wave")

    plot.circle(x=dt_w, y=data_w, color=colors.named.black, legend="wave")

    sma5 = talib.SMA(close, timeperiod = 5)
    sma10 = talib.SMA(close, timeperiod = 10)
    sma20 = talib.SMA(close, timeperiod = 30)
    sma120 = talib.SMA(close, timeperiod = 60)
    
    plot.line(x=dt, y=sma5, color=palettes_colors[5], legend="ma5")
    plot.line(x=dt, y=sma10, color=palettes_colors[2], legend="ma10")
    plot.line(x=dt, y=sma20, color=palettes_colors[8], legend="ma30")
    plot.line(x=dt, y=sma120, color=palettes_colors[12], legend="ma60")

    if result_df is not None:
        for trade_list in result_df.trades:
            for item in trade_list:
                time = item.datetime
                p = None
                if time in date_index:
                    p = date_index[time]
                else:
                    p = date_index[np.where(date_index > time)][0]
                # p = date_index[time]
                direction: Direction = item.direction
                price = item.price
                offset:Offset = item.offset
                mark = g_plot_mark[direction]
                color = g_mark_color[offset]
                if direction == Direction.LONG:
                    plot.triangle(x=p, y=price, color=color, size=10)
                else:
                    plot.inverted_triangle(x=p, y=price, color=color, size=10)
                text = Label(x=p, y=price, text="{}".format(price), x_offset = 6, y_offset=-7)
                plot.add_layout(text)

    plot.legend.location = "top_right"
    plot.legend.click_policy="hide"
    show(plot)


def test3():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()

    # backtester_engine.run_downloading("goog.SMART", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,10,5))
    strategy_name = "Kdj120MaStrategy"
    stock_name = "goog.SMART"
    # contracts = engine.get_all_contracts()

    backtester_engine.run_backtesting(strategy_name,
                                 stock_name,
                                 Interval.MINUTE,
                                 datetime.datetime(2019,7,15,20),
                                 datetime.datetime(2019,8,10,5),
                                 rate=0.29/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"ma_window":30, "wave_window":0.05, "bar_min":2}      # 策略设置
                                 )
    
    result_df = backtester_engine.get_result_df()
    bar_data = backtester_engine.backtesting_engine.history_data
    
    date_index = {}
    close = []
    date = []
    for i,v in enumerate(bar_data):
        bar:BarData = v
        date_index[bar.datetime] = i
        date.append(bar.datetime)
        close.append(bar.close_price)


    # print(result_df.columns.values)
    df = pd.DataFrame(result_df, columns=["date","trade_count","start_pos","end_pos","turnover","commission","slippage", "trading_pnl", "holding_pnl","total_pnl","net_pnl"])
    calculate_statistics = backtester_engine.get_result_statistics()
    df = df.rename(columns={        
        "date": "日期",
        "trade_count":"成交笔数",
        "start_pos":"开盘持仓",  
        "end_pos":"收盘持仓",    
        "turnover":"成交额",     
        "commission":"手续费",   
        "slippage":"滑点",       
        "trading_pnl":"交易盈亏",
        "holding_pnl":"持仓盈亏",
        "total_pnl":"总盈亏",    
        "net_pnl":"净盈亏"})
    print(df)
    rect1 = [0.14, 0.35, 0.77, 0.6] # [左, 下, 宽, 高] 规定的矩形区域 （全部是0~1之间的数，表示比例）
    rect2 = [0.14, 0.05, 0.77, 0.2]
    fig  = plt.figure(figsize=(42,10), dpi=100)
    ax1 = plt.axes(rect1)
    ax2 = plt.axes(rect2)
    close = np.array(close)
    sma5 = talib.SMA(close, timeperiod = 5)
    sma10 = talib.SMA(close, timeperiod = 10)
    sma20 = talib.SMA(close, timeperiod = 20)
    sma120 = talib.SMA(close, timeperiod = 120)

    ax1.plot(close)

    ax1.plot(sma5, "-", linewidth=0.5)
    ax1.plot(sma10, "-", linewidth=0.5)
    ax1.plot(sma20, "-", linewidth=0.5)
    ax1.plot(sma120, "-", linewidth=0.5)

    
    for trade_list in result_df.trades:
        for item in trade_list:
            time = item.datetime
            p = date_index[time]
            direction: Direction = item.direction
            price = item.price
            offset:Offset = item.offset
            mark = g_plot_mark[direction]
            color = g_mark_color[offset]
            ax1.plot(p, price, mark, color=color)
            s="{}{}:{}".format(offset.value, direction.value, price)
            ax1.annotate(s, xy=(p, price))
            # ax1.annotate(s,xy=(p+5, price+0.7),xytext=(p,price),arrowprops=dict(arrowstyle="->",connectionstyle="arc3",color="r"))
    plt.show()

def test4():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()

    # backtester_engine.run_downloading("goog.SMART", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,10,5))
    strategy_name = "MaLevelTrackStrategy"
    stock_name = "amd.SMART"
    wave_window = 0.001
    # contracts = engine.get_all_contracts()

    # tracker = {"bar_data":[], "trade_info":[]}
    tracker = {"ma_tag":[], "var":[], "var1":[], "var2":[]}
    backtester_engine.run_backtesting(strategy_name,
                                 stock_name,
                                 Interval.MINUTE,
                                 datetime.datetime(2019,7,15,20),
                                 datetime.datetime(2019,8,19,5),
                                 rate=2.9/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"ma_window":30, "wave_window":wave_window, "bar_min":1, "tracker":tracker}      # 策略设置
                                 )
    
    result_df = backtester_engine.get_result_df()
    
    if "bar_data" in tracker and len(bar_data) > 0:
        bar_data = tracker["bar_data"]
    else:
        bar_data = backtester_engine.backtesting_engine.history_data
    
    date_index = {}
    close = []
    date = {}
    dt = []
    high = []
    low = []
    for i,v in enumerate(bar_data):
        bar:BarData = v
        date_index[bar.datetime] = i
        date[i] = bar.datetime.strftime("%m/%d %H:%M")
        close.append(bar.close_price)
        high.append(bar.high_price)
        low.append(bar.low_price)
        dt.append(i)


    plot = figure(aspect_scale=0.3, match_aspect=False,plot_width=1100, plot_height=450,x_axis_label="date", y_axis_label="high",
                   tools="pan,reset,save,wheel_zoom,xwheel_zoom,ywheel_zoom")

    # list_data = []
    # for array in tracker["ma_tag"]:
    #     list_data.append(array[-1])
    # x_data = range(len(list_data))
    # y_data = list_data
    # plot.line(x=list(x_data), y=y_data)

    # list_data = []
    # for array in tracker["var"]:
    #     list_data.append(array)
    # x_data = range(len(list_data))
    # y_data = list_data
    # plot.circle(x=list(range(len(tracker["var"]))), y=tracker["var"], legend="var 10")
    # plot.circle(x=list(range(len(tracker["var1"]))), y=tracker["var1"], legend="var 5")
    # plot.circle(x=list(range(len(tracker["var2"]))), y=tracker["var2"], legend="var 3")

    plot.line(x = dt, y = close, color=palettes_colors[0], line_width=1.5)

    c_i = 5
    close = np.array(close)
    for i in [5,10,20,30,60]:
        ma_val = talib.SMA(close, timeperiod = i)
        plot.line(x=dt, y=ma_val, color=palettes_colors[c_i], legend="ma"+str(i))
        c_i += 1



    if result_df is not None:
        for trade_list in result_df.trades:
            for item in trade_list:
                time = item.datetime
                p = None
                if time in date_index:
                    p = date_index[time]
                else:
                    p = date_index[np.where(date_index > time)][0]
                # p = date_index[time]
                direction: Direction = item.direction
                price = item.price
                offset:Offset = item.offset
                mark = g_plot_mark[direction]
                color = g_mark_color[offset]
                if direction == Direction.LONG:
                    plot.triangle(x=p, y=price, color=color, size=10)
                else:
                    plot.inverted_triangle(x=p, y=price, color=color, size=10)
                text = Label(x=p, y=price, text="{}".format(price), x_offset = 6, y_offset=-7)
                plot.add_layout(text)

    plot.legend.location = "top_right"
    plot.legend.click_policy="hide"
    show(plot)

def download2():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(HbdmGateway)

    setting = {
        "API Key": "mjlpdje3ld-701b9727-9ae52956-3ef1e",
        "Secret Key": "b4df4824-124ec192-55786af1-a397a",
        "会话数": 3,
        "代理地址": "127.0.0.1",
        "代理端口": "1080",
    }

    main_engine.connect(setting, "HBDM")
    sleep(10)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()
    backtester_engine.run_downloading("BCH190830.HUOBI", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,22,12))
    print("download 完成")

def download3():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(BitmexGateway)

    setting = {
        "ID": "jhrmZrfaxqD-wmHpVXBjhlBe",
        "Secret": "QZdRHN-XVyEHnutgbVpRP29JtJgGAlATHXC1gVUGM7f8Xu7f",
        "会话数": 3,
        "服务器": "REAL",
        "代理地址": "127.0.0.1",
        "代理端口": "1080",
    }

    main_engine.connect(setting, "BITMEX")
    sleep(10)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()
    backtester_engine.run_downloading("XBTUSD.BITMEX", Interval.MINUTE, datetime.datetime(2019,7,1,20), datetime.datetime(2019,7,10,10))
    print("download 完成")

if __name__ == "__main__":
    # download("amd.SMART")
    test2()
    # download3()


