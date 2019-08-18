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
from vnpy.trader.constant import Exchange, Interval
from kdj import calc_kdj
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
from vnpy.trader.constant import Direction, Offset

matplotlib.rcParams['font.sans-serif'] = ['SimHei'] 
matplotlib.rcParams['font.family']='sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False

g_plot_mark = {
    Direction.LONG:"^",
    Direction.SHORT:"v",
    Direction.NET:">",
}

g_mark_color = {
    Offset.OPEN:"darkred",
    Offset.CLOSE:"lightgreen",
    Offset.CLOSETODAY:"limegreen",
    Offset.CLOSEYESTERDAY:"palegreen"
}
class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(390)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

def test1():
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


    print(result_df.columns.values)
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


if __name__ == "__main__":
    test1()


