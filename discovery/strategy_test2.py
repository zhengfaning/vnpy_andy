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

    tracker = {"ma_tag":[], "var":[], "var1":[], "var2":[], "trade_info":[]}
    strategy = Kdj120MaStrategy(object(), "test_strategy", "goog", {"ma_window":30, "wave_window":wave_window, "bar_min":1, "tracker":tracker})

    for data in bar_data:
        strategy.on_bar(data)
    
    
    

if __name__ == "__main__":
    test1()


