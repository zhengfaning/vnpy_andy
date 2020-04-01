import sys
# sys.path.append('../')

from time import sleep
import json
import time, datetime
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Exchange, Interval
# from kdj import calc_kdj
import pandas as pd
import matplotlib.pyplot as plt
# import draw_test
# import func_test3
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
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG
# from vnpy.app.cta_strategy.strategies.kdj_120ma_strategy import Kdj120MaStrategy
from vnpy.app.cta_strategy.strategies.kdj_120ma_strategy import Kdj120MaStrategy




class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(390)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)

def test1():

    req = HistoryRequest(
        exchange=Exchange.SMART,
        symbol="goog",
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,7,9,9),
        end=datetime.datetime(2019,8,16,4)
    )
    
    bar_data = rq.rqdata_client.query_history(req)
    print(bar_data)
    



