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
from vnpy.trader.constant import Direction, Offset
from bokeh.io import output_file, show
from bokeh.plotting import figure
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
    sleep(20)
    backtester_engine = main_engine.add_app(CtaBacktesterApp)
    backtester_engine.init_engine()
    
    start_date = datetime.datetime(2018,8,10,20)
    end_date = datetime.datetime.now()
    while start_date < end_date:
        try:
            next_date = start_date + datetime.timedelta(10)
            backtester_engine.run_downloading("ETHUSD.BITMEX", Interval.MINUTE, start_date, next_date)
            sleep(90)
            start_date = next_date
        except Exception as e:
            print(e)
            print("等待120秒后继续")
            sleep(120)
    
    # backtester_engine.run_downloading("XBTUSD.BITMEX", Interval.MINUTE, datetime.datetime(2019,7,1,20), datetime.datetime(2019,7,10,10))
    print("download 完成")

if __name__ == "__main__":
    # download("baba.SMART")
    # test3()
    download3()


