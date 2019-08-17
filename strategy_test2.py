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
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG


class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(390)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

def test1():
    # event_engine = EventEngine()
    # main_engine = MainEngine(event_engine)
    # log_engine = main_engine.get_engine("log")
    # event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
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
    time.sleep(8)
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

    strategy = Kdj120MaStrategy(object(), "test_strategy", "goog", {"ma_window":10, "wave_window":0.05, "bar_min":3})

    # req = HistoryRequest(
    #     exchange=Exchange.SMART,
    #     symbol="goog",
    #     interval=Interval.MINUTE,
    #     start=datetime.datetime(2019,7,9,9),
    #     end=datetime.datetime(2019,8,16,4)
    # )
    
    # bar_data = rq.rqdata_client.query_history(req)

    date = []
    for v in bar_data:
        strategy.on_bar(v)
        date.append(v.datetime)

    # print("calc=",strategy.calc)
    # print("bull_count={},bear_count={},king={}".format(strategy.bull_count, strategy.bear_count, strategy.king_count))
    print(strategy.report)
    # sys.exit(1)
    # dt = date
    # close = strategy.am.close_array
    # rect1 = [0.14, 0.35, 0.77, 0.6] # [左, 下, 宽, 高] 规定的矩形区域 （全部是0~1之间的数，表示比例）
    # rect2 = [0.14, 0.05, 0.77, 0.2]
    # fig  = plt.figure()
    # ax1 = plt.axes(rect1)
    # ax2 = plt.axes(rect2)
    # ax1 = fig.add_subplot(2,1,1)
    # print(dt)
    # print(close)
    # ax1.plot(dt,close)
    

    # v_list, p_list = strategy.am.wave()
    # for i in range(len(p_list)):
    #     p = p_list[i]
    #     ax1.plot([dt[p]], [close[p]], 'o')
    #     ax1.annotate(close[p], xy=(dt[p], close[p]))
    # print(close)
    # sma120 = talib.SMA(close, timeperiod = 60) 
    # ax1.plot(dt,sma120)
    # # ax2 = fig.add_subplot(2,1,2)
    # kdj_data = strategy.am.kdj()
    # ax2.plot(dt,kdj_data["k"], "r")
    # ax2.plot(dt,kdj_data["d"], "b")
    # ax2.plot(dt,kdj_data["j"], "y")
    

    # ax2 = fig.add_subplot(2,1,2)
    
    
    # plt.show()

if __name__ == "__main__":
    test1()


