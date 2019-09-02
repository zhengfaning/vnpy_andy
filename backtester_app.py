from time import sleep
import sys
import json
import time, datetime
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import talib
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
from vnpy.app.cta_strategy.strategies.kdj_120ma_strategy import Kdj120MaStrategy
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.algo_trading import AlgoTradingApp,AlgoEngine
from vnpy.trader.constant import Direction, Offset
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.gateway.hbdm.hbdm_gateway import HbdmGateway,symbol_type_map
from vnpy.gateway.bitmex.bitmex_gateway import BitmexGateway
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.algorithm import Algorithm

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

g_tools="pan,xwheel_zoom,ywheel_zoom,reset,wheel_zoom"

class BacktesterApp:
    
    wave_window = 0.0001
    tracker = {"bar_data":[], "trade_info":[], "ma_tag":[], "var":[], "var1":[], "var2":[], "ma_tag_ls":[]}
    plot = figure(aspect_scale=0.3, match_aspect=False,plot_width=1100, plot_height=450,x_axis_label="date", y_axis_label="high", tools=g_tools)
    plot_second = figure(output_backend="webgl", plot_width=1800, plot_height=200,x_axis_label="date", y_axis_label="high", tools=g_tools)
    def __init__(self):
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.main_engine.add_gateway(HbdmGateway)
        self.main_engine.add_gateway(BitmexGateway)
        log_engine = self.main_engine.get_engine("log")
        self.event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
        self.main_engine.write_log("注册日志事件监听")
        self.backtester_engine = self.main_engine.add_app(CtaBacktesterApp)
        self.backtester_engine.init_engine()
        self.algo_engine:AlgoEngine = self.main_engine.add_app(AlgoTradingApp)
        self.algo_engine.init_engine()
        self.close = None
    
    def init_plot(self, aspect_scale=0.3, match_aspect=False,width=1100, height=450, TOOLTIPS=None):
        # tools="pan,tap,crosshair,reset,save,wheel_zoom,xwheel_zoom,ywheel_zoom"
        self.plot = figure(aspect_scale=aspect_scale, output_backend="webgl", match_aspect=match_aspect,plot_width=width, plot_height=height,x_axis_label="date", y_axis_label="high", tooltips=TOOLTIPS, tools=g_tools)
        
    
    def start_algo(self, setting):
        self.algo_engine.start_algo(setting)

    def download(self, stock_name, start_date, end_date):
        self.backtester_engine.run_downloading(stock_name, Interval.MINUTE, start_date, end_date)
        print("download 完成")
    
    def download_hbdm(self, stock_name, start_date, end_date):

        setting = {
            "API Key": "mjlpdje3ld-701b9727-9ae52956-3ef1e",
            "Secret Key": "b4df4824-124ec192-55786af1-a397a",
            "会话数": 3,
            "代理地址": "127.0.0.1",
            "代理端口": "1080",
        }

        self.main_engine.connect(setting, "HBDM")
        sleep(10)
        self.backtester_engine.run_downloading(stock_name + ".HUOBI", Interval.MINUTE, start_date, end_date)
        print("download 完成")


    def download_Bitmex(self, stock_name, start_date, end_date):
        setting = {
            "ID": "jhrmZrfaxqD-wmHpVXBjhlBe",
            "Secret": "QZdRHN-XVyEHnutgbVpRP29JtJgGAlATHXC1gVUGM7f8Xu7f",
            "会话数": 3,
            "服务器": "REAL",
            "代理地址": "127.0.0.1",
            "代理端口": "1080",
        }

        self.main_engine.connect(setting, "BITMEX")
        sleep(10)
        self.backtester_engine.run_downloading(stock_name + ".BITMEX", Interval.MINUTE, start_date, end_date)
        print("download 完成")
    
    def start_backtester(self, strategy, stock, start_date, end_date):
        self.strategy = strategy
        # self.stock = stock
        self.backtester_engine.run_backtesting(strategy,
                                 stock,
                                 Interval.MINUTE,
                                 start_date,
                                 end_date,
                                 rate=2.9/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"ma_window":120, "wave_window":self.wave_window, "bar_min":1, "tracker":self.tracker}      # 策略设置
                                 )
        bar_data = self.get_bar_data()
        self.date_index = {}
        self.close = []
        self.date = {}
        self.plot_index = []
        self.high = []
        self.low = []
        for i,v in enumerate(bar_data):
            bar:BarData = v
            self.date[i] = bar.datetime.strftime("%m/%d %H:%M")
            self.date_index[bar.datetime] = i
            self.close.append(bar.close_price)
            self.high.append(bar.high_price)
            self.low.append(bar.low_price)
            self.plot_index.append(i)
        
        

    def get_bar_data(self):
        bar_data = []
        if "bar_data" in self.tracker and len(self.tracker["bar_data"]) > 0:
            bar_data = self.tracker["bar_data"]
        if len(bar_data) == 0:
            bar_data = self.backtester_engine.backtesting_engine.history_data
        return bar_data
    
    def plot_wave(self):
        w,w_pos = Algorithm.wave(self.close, self.wave_window)
        self.plot.circle(x=w_pos, y=w, color=colors.named.black, legend="all wave")

    def statistics(self):
        result_df = self.backtester_engine.get_result_df()
        df = pd.DataFrame(result_df, columns=["date","trade_count","start_pos","end_pos","turnover","commission","slippage", "trading_pnl", "holding_pnl","total_pnl","net_pnl"])
        # calculate_statistics = self.backtester_engine.get_result_statistics()
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
    
    def plot_ma_tag(self):
        tooltip_x = []
        tooltip_y = []
        tooltip_desc = []
        deg_desc = []

        if "ma_tag_ls" not in self.tracker:
            return 

        for item in self.tracker["ma_tag_ls"]:
            index = self.date_index[item[0]]
            tooltip_x.append(int(index))
            tooltip_y.append(item[1])
            desc = "{}  {:.2f}  {:.2f} ".format(item[2], item[3], item[4])
            tooltip_desc.append(desc)
            deg_desc.append("{:.2f}  {:.2f}  {:.2f}".format(item[5], item[6], item[7]))


        source = ColumnDataSource(data=dict(
            x=tooltip_x,
            y=tooltip_y,
            desc=tooltip_desc,
            deg=deg_desc
        ))

        TOOLTIPS = [
            ("index", "$index"),
            ("price", "@y{0.00}"),
            ("desc", "@desc"),
            ("deg", "@deg"),
        ]
        hover = HoverTool(tooltips=TOOLTIPS)
        self.plot.add_tools(hover)
        # self.plot.tooltips = TOOLTIPS
        self.plot.circle("x", "y", color=palettes_colors[0], size=7, source=source, legend="point desc")
    
    def plot_ma_line(self, ma_param_list = [5, 10, 30, 60, 120]):
        c_i = 5
        close = np.array(self.close)
        for i in ma_param_list:
            ma_val = talib.SMA(close, timeperiod = i)
            self.plot.line(x=self.plot_index, y=ma_val, color=palettes_colors[c_i], legend="ma"+str(i))
            c_i += 1

    def plot_kdj(self, ma_param_list = [5, 10, 30, 60, 120]):

        close = np.array(self.close)
        high = np.array(self.high)
        low = np.array(self.low)
        kdj_val = Algorithm.kdj(high, low, close)
        self.plot_second.line(x=self.plot_index, y=kdj_val["k"], color=palettes_colors[0], legend="kdj")
        self.plot_second.line(x=self.plot_index, y=kdj_val["d"], color=palettes_colors[2], legend="kdj")
        self.plot_second.line(x=self.plot_index, y=kdj_val["j"], color=palettes_colors[3], legend="kdj")
            

            

    def plot_kline(self):
        self.plot.line(x = self.plot_index, y = self.close, color=palettes_colors[0], line_width=1.5, legend="kline")

    def plot_trade_wave(self):
        dt_w = []
        data_w = []
        for item in self.tracker["trade_info"]:
            for value in item["wave"]:
                i_v = list(value.items())[0]
                index = self.date_index[i_v[0]]
                # v = close[index]
                dt_w.append(index)
                data_w.append(i_v[1])
        self.plot.circle(x=dt_w, y=data_w, color=colors.named.black, legend="trade_info")

    def plot_trade_degline(self):
        # bar_data = self.get_bar_data()
        dt_index = []
        y_fit = []
        dt_index_full = []
        y_fit_full = []
        tooltip_desc = []
        for item in self.tracker["trade_info"]:
            i1 = self.date_index[item[0]]
            i2 = self.date_index[item[1]]
            i3 = self.date_index[item[2]]
            x = np.arange(i1, i2)
            m1,y = regress_xy(x, np.array(self.close[i1:i2]), zoom=False)
            x2 = np.arange(i2, i3)
            m2,y2 = regress_xy(x2, np.array(self.close[i2:i3]), zoom=False)
            dt_index.append([x[0], x2[0], x2[-1]])
            y_fit.append([y[0], y2[0], y2[-1]])

            x = np.arange(i1, i3)
            m3,y = regress_xy(x, np.array(self.close[i1:i3]), zoom=False)
            dt_index_full.append([x[0], x[-1]])
            y_fit_full.append([y[0], y[-1]])
            tooltip_desc.append("{:.2f}  {:.2f}  {:.2f}".format(np.rad2deg(m1.params[1]), np.rad2deg(m2.params[1]), np.rad2deg(m3.params[1])))
            
        
        source = ColumnDataSource(data=dict(
            xs=dt_index,
            ys=y_fit,
            deg=tooltip_desc,
        ))

        TOOLTIPS = [
            ("deg", "@deg"),
        ]

        hover = HoverTool(tooltips=TOOLTIPS)
        self.plot.add_tools(hover)
        self.plot.multi_line("xs", "ys", color=colors.named.black, source=source, legend="degline")
        self.plot.multi_line(xs=dt_index_full, ys=y_fit_full, color=colors.named.yellow, legend="degline_full")
        

    def plot_tarde_mark(self):
        result_df = self.backtester_engine.get_result_df()
        if result_df is not None:
            for trade_list in result_df.trades:
                for item in trade_list:
                    time = item.datetime
                    p = None
                    if time in self.date_index:
                        p = self.date_index[time]
                    else:
                        p = self.date_index[np.where(self.date_index > time)][0]
                    # p = date_index[time]
                    direction: Direction = item.direction
                    price = item.price
                    offset:Offset = item.offset
                    # mark = g_plot_mark[direction]
                    color = g_mark_color[offset]
                    if direction == Direction.LONG:
                        self.plot.triangle(x=p, y=price, color=color, size=10)
                    else:
                        self.plot.inverted_triangle(x=p, y=price, color=color, size=10)
                    text = Label(x=p, y=price, text="{}".format(price), x_offset = 6, y_offset=-7)
                    self.plot.add_layout(text)
    
    def show(self):
        self.plot.legend.location = "top_right"
        self.plot.legend.click_policy="hide"
        
        if self.strategy == "MaLevelTrackStrategy":
            self.plot_ma_tag()
            self.plot_trade_degline()
        elif self.strategy == "Kdj120MaStrategy":
            # self.plot_wave()
            self.plot_trade_wave()
        self.plot_kdj()
        self.plot_tarde_mark()
        self.plot.xaxis.major_label_overrides = self.date
        self.plot_second.xaxis.major_label_overrides = self.date
        # wheelzoomtool = WheelZoomTool()
        # self.plot.add_tools(wheelzoomtool)
        # self.plot_second.add_tools(wheelzoomtool)
        # wheelzoomtool = WheelZoomTool(dimensions="width")
        # self.plot.add_tools(wheelzoomtool)
        # self.plot_second.add_tools(wheelzoomtool)
        # wheelzoomtool = WheelZoomTool(dimensions="height")
        # self.plot.add_tools(wheelzoomtool)
        # self.plot_second.add_tools(wheelzoomtool)
        # pantool = PanTool()
        # self.plot.add_tools(pantool)
        # self.plot_second.add_tools(pantool)
    
        # plots_grid = gridplot([[self.plot],[self.plot_second]])
        # show(plots_grid)
        show(self.plot)




if __name__ == "__main__":

    strategy_test = BacktesterApp()
    start_date = datetime.datetime(2019,8,2,20)
    end_date = datetime.datetime(2019,9,2,20)
    stock = "fb.SMART"
    algo_setting= {
        "vt_symbol": "",
        "direction": Direction.LONG.value,
        "volume": 0.0,
        "offset": Offset.OPEN.value,
            
    }
    algo_setting["template_name"] = "ArbitrageAlgo"
    # strategy_test.start_algo(algo_setting)
    strategy_test.download(stock, start_date, end_date)
    strategy_test.start_backtester("MaLevelTrackStrategy", stock, start_date, end_date)
    # close = strategy_test.close
    # close = np.array(close)
    # calc_regress_deg(close)
    strategy_test.init_plot(width=1800, height=600)
    strategy_test.statistics()
    strategy_test.plot_kline()
    strategy_test.plot_ma_line([5, 10, 30, 60, 120])
    strategy_test.show()
    # download3()


