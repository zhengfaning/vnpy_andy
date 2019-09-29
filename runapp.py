from time import sleep
import sys
import json
import time, datetime
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import talib
from pytz import timezone
# from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.app.cta_strategy import (
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)
# import app as vnpy_app
from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine
from vnpy.app.cta_strategy.strategies.ma_trend_strategy import MaTrendStrategy
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.algo_trading import AlgoTradingApp,AlgoEngine
from vnpy.trader.constant import Direction, Offset
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.gateway.hbdm.hbdm_gateway import HbdmGateway,symbol_type_map
from vnpy.gateway.bitmex.bitmex_gateway import BitmexGateway
from vnpy.gateway.tiger.tiger_gateway import TigerGateway
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.algorithm import Algorithm
from vnpy.app.cta_strategy import CtaStrategyApp
from bokeh.io import output_file, show
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Label
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.palettes import d3, brewer, mpl
from bokeh.core.enums import colors
from bokeh.layouts import column, gridplot
from bokeh.models import WheelZoomTool, HoverTool, Plot, PanTool
from abu.UtilBu.ABuRegUtil import calc_regress_deg, regress_xy
palettes_colors = d3["Category20"][20]

# output_file("dark_minimal.html")
curdoc().theme = 'dark_minimal'
# from bokeh.models import Arrow, OpenHead, NormalHead, VeeHead


class StrategyApp:

    def __init__(self):
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.main_engine.add_gateway(HbdmGateway)
        self.main_engine.add_gateway(BitmexGateway)
        log_engine = self.main_engine.get_engine("log")
        self.event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
        self.main_engine.write_log("注册日志事件监听")
        self.main_engine.add_app(CtaStrategyApp)
        self.main_engine.add_app(AlgoTradingApp)



    def start_algo(self, setting):
        self.algo_engine.start_algo(setting)

    def run(self):
        pass


if __name__ == "__main__":
    app = StrategyApp()
