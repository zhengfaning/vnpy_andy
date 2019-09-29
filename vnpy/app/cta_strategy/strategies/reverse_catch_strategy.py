from vnpy.app.cta_strategy import (
    CtaTemplate,
    CtaSignal,
    TargetPosTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
import numpy as np
from functools import reduce
from abu.UtilBu.ABuRegUtil import calc_regress_deg
import abu.UtilBu.ABuRegUtil as reg_util
from vnpy.trader.object import Status
from vnpy.trader.utility import IntervalGen
from vnpy.trader.constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType, KlinePattern, KLINE_PATTERN_CHINESE
from dataclasses import dataclass, field
from  enum import Enum
import math
import pandas as pd
from functools import partial
import time, datetime
from pytz import timezone


eastern = timezone('US/Eastern')

def local_to_eastern(unix_time):
    return datetime.datetime.fromtimestamp(unix_time, eastern)


class PatternRecord:
    data = {}
    expiry = {}
    def __init__(self):
        pass

    def add_pattern(self, pattern_list):
        for item in pattern_list:
            self.data[item[0]] =dict(count=0,value=item[1])


    def update(self):
        discard = []
        for i in self.data.keys():
            self.data[i]["count"] += 1
            if i in self.expiry and self.data[i]["count"] > self.expiry[i]:
                discard.append(i)
        
        for item in discard:
            self.data.pop(item)

    def set_expiry(self, pattern_list, count):
        for item in pattern_list:
            self.expiry[item] = count

    def __contains__(self, item):
	    return item in self.data
    
    def __getitem__(self, i):
        return self.data[i]
    
    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()


class ClosePosType(Enum):
    SAFE_PRICE = 1
    TREND_CHANGE = 2


class BasePosition():
    volumn: int = 0
    close_price: float = 0.0
    buy_price: float = 0
    strategy = None

    def __init__(self, strategy):
        self.strategy = strategy

    def buy(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET):
        """
        Send buy order to open a long position.
        """
        return self.strategy.send_order(Direction.LONG, Offset.OPEN, price, volume, lock, type)

    def sell(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET):
        """
        Send sell order to close a long position.
        """
        return self.strategy.send_order(Direction.SHORT, Offset.CLOSE, price, volume, lock, type)

    def short(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET):
        """
        Send short order to open as short position.
        """
        return self.strategy.send_order(Direction.SHORT, Offset.OPEN, price, volume, lock, type)

    def cover(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET):
        """
        Send cover order to close a short position.
        """
        return self.strategy.send_order(Direction.LONG, Offset.CLOSE, price, volume, lock, type)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # pre_volumn = 0
        if trade.direction == Direction.LONG:
            if self.volumn == 0:
                self.on_vol_reset(trade)
            self.volumn += trade.volume
            
        elif trade.direction == Direction.SHORT:
            if self.volumn == 0:
                self.on_vol_reset(trade)
            self.volumn -= trade.volume

        elif trade.direction == Direction.NET:
            self.volumn = trade.volume

    def on_vol_reset(self, trade: TradeData):
        pass

    def on_order(self, order: OrderData):
        pass


class Ma120Position():

    order_data = np.array([])
    safe_price_offset = 0
    # 形态预测出错修正,日后增设级别在3以上才执行

    def __init__(self, strategy, setting):
        self.strategy: ReverseCatchStrategy = strategy
        self.safe_price_offset = setting["safe_price_offset"]
        self.ma_lvl = setting["ma_lvl"]
        # self.am = self.strategy.am
    
    def on_bar(self, bar:BarData, calc_data):
        self.order_data = np.append(self.order_data, bar)
        if not (self.volumn < 0 and bar.close_price < self.safe_price or \
                self.volumn > 0 and bar.close_price > self.safe_price):
                return

        am = self.strategy.am
        rg = (bar.close_price / self.buy_price) - 1

        close_price = None
        if rg > 0.01 and self.volumn > 0:
            close_price = am.sma(120)
            if self.level < 5:
                self.level = 5
                return self.strategy.buy(bar.close_price, 50, type=OrderType.MARKET) 
        elif rg < -0.01 and self.volumn < 0:
            close_price = am.sma(120)
            if self.level < 5:
                self.level = 5
                return self.strategy.short(bar.close_price, 50, type=OrderType.MARKET) 
            

        for lvl in self.ma_lvl[-1:]:
            if len(self.order_data) < lvl:
                close_price = am.sma(lvl, array=False, length=lvl+1)
                break
        

        if close_price is None:
            lvl = self.strategy.ma_level[-1]
            close_price = am.sma(lvl, array=False, length=lvl+1)

        
        
        if self.volumn < 0:
            if bar.close_price > close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.strategy.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达MA均线价{}".format(close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.strategy.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra={"reason": "平仓:到达MA均线价{}".format(close_price)})


    def on_order(self, order: OrderData):
        pass


    def on_vol_reset(self, trade: TradeData):

        if trade.direction == Direction.LONG:
            self.trade_price = trade.price
            self.order_data = np.array([])
            self.safe_price = trade.price
        elif trade.direction == Direction.SHORT:
            scale = 1 + self.closeout_offset
            self.close_price = round(trade.price * scale, 2)
            self.order_data = np.array([])
            self.trade_price = trade.price

class CloseoutPosition(BasePosition):
    volumn: int = 0
    level: int = 0
    closeout_price: float = 0.0
    trade_price: float = 0
    safe_price: float = 0
    order_data = np.array([])
    # 形态预测出错修正,日后增设级别在3以上才执行
    last_close_info = None
    guard = None

    def __init__(self, strategy, setting):
        self.strategy: ReverseCatchStrategy = strategy
        # self.am = self.strategy.am
        self.closeout_offset = setting["closeout_offset"]

    def set_closeout_price(self, price):
        self.closeout_price = price

    def set_closeout_offset(self, offset):
        self.closeout_offset = offset

    def on_bar(self, am:ArrayManager, bar:BarData, calc_data):
        if self.volumn < 0:
            if bar.close_price > self.closeout_price:
                calc_data["trade_close"] = "平仓:到达最低价{}".format(self.closeout_price)
                return self.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达最低价{}".format(self.close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < self.closeout_price:
                calc_data["trade_close"] = "平仓:到达最低价{}".format(self.close_price)
                return self.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra={"reason": "平仓:到达最低价{}".format(self.close_price)})

    def on_vol_reset(self, trade: TradeData):

        if trade.direction == Direction.LONG:
            scale = 1 - self.closeout_offset
            self.trade_price = trade.price
            self.close_price = round(trade.price * scale, 2)
            self.trade_price = trade.price
            self.order_data = np.array([])
        elif trade.direction == Direction.SHORT:
            scale = 1 + self.closeout_offset
            self.close_price = round(trade.price * scale, 2)
            self.order_data = np.array([])
            self.trade_price = trade.price


@dataclass
class MaTrendRecord:
    close = []
    std_val = 0
 
''' 
    TODO: 加入每日时间识别
    TODO: 加入红绿十字星识别
    TODO: 加入十字星后,快速趋势判断购买
    TODO: 加入高吊线和低线识别
    TODO: 策略架构改进,多个策略并存
'''

class ReverseCatchStrategy(CtaTemplate):
    author = "用Python的交易员"

    ma_level = [5, 10, 20, 30, 120]
    ma_tag = []
    bd = []
    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0
    request_order = []
    bar_identify = []
    volumn = 0
    kdj_record = []
    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]
    add_pos = False
    safe_price = None
    trend_record = MaTrendRecord

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(ReverseCatchStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar, 1, self.on_1min_bar)
        self.am = ArrayManager(200)
        self.am3 = ArrayManager(150)
        self.bg3 = BarGenerator(self.on_bar, 3, self.on_3min_bar)
        self.am5 = ArrayManager(120)
        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.order_data = None
        self.positions = CloseoutPosition(self, {"closeout_offset": 0.003})
        self.std_range = IntervalGen(np.std,5)
        self.std_range3 = IntervalGen(np.std,5)        
        self.std_range5 = IntervalGen(np.std,5)
        self.pattern_record = PatternRecord()
        # self.pattern_record.set_expiry([KlinePattern.CDLEVENINGSTAR], 3)
        self.pattern_record.set_expiry(list(KlinePattern), 1)
        self.ma_info = []
        
        five_min_open_5 = partial(self.reverse_shape_strategy, setting={"len":20, "atr":10, "atr_valve":0.8, "mid_sign":(7,14)})
        self.open_strategy = {
            "1":[five_min_open_5],
        }
        self.offset = 40
        self.ma120_track = None
        self.ma120_track_list = []
    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(5)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)
        self.bg3.update_tick(tick)
        self.bg5.update_tick(tick)

    def on_3min_bar(self, bar: BarData):
        self.am3.update_bar(bar)
        self.std_range3.update(self.am3.range[-1])
        if not self.am.inited or not self.trading:
            return   
        pattern = self.am3.pattern([KlinePattern.CDLEVENINGSTAR, KlinePattern.CDL2CROWS])
        
        if len(pattern) > 0:
            print(pattern)
            self.pattern_record.add_pattern(pattern)
            # deg = calc_regress_deg(self.am3.close[-20:])
    
    def wave(self, data, window = 0.0002):

            if len(data) <= 0:
                return 
            # r = array[::-1]
            result = { "value":[], "range":[],  "pos":[], "length":[]}
            r = data
            l = len(data) - 1
            now = r[0]
            # v_list.append(now)
            # p_list.append(0)
            pos = 1

            vol = 0
            u_tag = None
            d_tag = None
            end_tag = None
            start_pos = 0
            while pos < l:
                if math.isnan(now):
                    now = r[pos]
                    pos += 1
                    continue
                else:
                    start_pos = pos - 1
                    break

            while pos < l:

                if now < r[pos]:
                    u_tag = pos
                    if d_tag:
                        diff = r[start_pos] - r[d_tag]
                        if abs(diff / r[start_pos]) > window and d_tag - start_pos > 4:
                            end_tag = d_tag
                            
                elif now > r[pos]:
                    d_tag = pos
                    if u_tag:
                        diff = r[start_pos] - r[u_tag]
                        if abs(diff / r[start_pos]) > window and d_tag - start_pos > 4:
                            end_tag = u_tag

                if end_tag is not None:
                    result["range"].append(r[end_tag] / r[start_pos] - 1)
                    result["length"].append(end_tag - start_pos)
                    start_pos = end_tag
                    result["value"].append(r[end_tag])
                    result["pos"].append(end_tag)
                    end_tag = None

                vol += r[pos] - now
                now = r[pos]
                pos += 1
            return pd.DataFrame(result)

    
    def mode_identify(self, bar: BarData):
        self.bar_identify = []
        hl_scale = round(bar.high_price / bar.low_price - 1, 4)
        if hl_scale > 0.001:
            diff = bar.high_price - bar.low_price
            diff_up = bar.low_price + diff / 2 * 1.20
            diff_down = bar.low_price + diff / 2 * 0.80 
            close = bar.close_price
            if bar.open_price < diff_up and bar.open_price > diff_down and \
               bar.close_price < diff_up and bar.close_price > diff_down:
                if bar.close_price > bar.open_price:
                    print("绿十字星",bar.datetime, bar.high_price,bar.low_price,diff,diff_up,diff_down, bar.open_price, bar.close_price)
                else:
                    print("红十字星",bar.datetime, bar.high_price,bar.low_price,diff,diff_up,diff_down, bar.open_price, bar.close_price)
        

    def on_5min_bar(self, bar: BarData):
        self.std_range5.update(self.am5.range[-1])
        self.am5.update_bar(bar)
        if not self.am.inited or not self.trading:
            return   
        
        # self.on_strategy(self.am5, bar, self.open_strategy["5"])
        # pattern_list = [KlinePattern.CDLEVENINGSTAR, KlinePattern.CDL2CROWS, KlinePattern.CDLCONCEALBABYSWALL, KlinePattern.CDLEVENINGDOJISTAR]
    #     pattern = self.am5.pattern(list(KlinePattern))
    #     if len(pattern) > 0:
    #         print(list(map(lambda x: (KLINE_PATTERN_CHINESE[x[0]],x[1]), pattern)))
    #         self.pattern_record.add_pattern(pattern)
    #         deg_full = calc_regress_deg(self.am.close[-40 :], False)
    #         print("deg:",deg_full)
        
    #     self.pattern_record.update()

    def open_v3(self, am:ArrayManager, bar:BarData):
        std_val2 = np.std(np.array(self.ma_tag[-10:-1]))
        mean_val2 = np.mean(np.array(self.ma_tag[-10:-1]))
        mean = np.mean(np.array(self.ma_tag[-30:-10]))

        if std_val2 < 0.2: 
            if mean_val2 > 3:
                if mean_val2 >= (mean + 1):
                    return self.buy(bar.close_price, 1, type=OrderType.MARKET)
            elif mean_val2 < 2:
                if mean_val2 <= (mean - 1):
                    return self.short(bar.close_price, 1, type=OrderType.MARKET)

    def open_v1(self, am:ArrayManager, bar:BarData):
        offset = -40
        offset_m = int(offset / 2)
        calc_nums = np.array(self.ma_tag[-offset:-1])
        mean_val = np.mean(calc_nums)
        # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        if std_val < 1 and mean_val < 2 and self.ma_tag[-1] >= (mean_val + 2):
            return self.buy(bar.close_price, 1, type=OrderType.MARKET)
        elif std_val < 1 and mean_val > 3 and self.ma_tag[-1] <= (mean_val - 2):
            return self.short(bar.close_price, 1, type=OrderType.MARKET)
    
    def open_v2(self, am:ArrayManager, bar:BarData):
        std_val2 = np.std(np.array(self.ma_tag[-10:-1]))
        mean_val2 = np.mean(np.array(self.ma_tag[-10:-1]))
        mean = np.mean(np.array(self.ma_tag[-30:-10]))

        if std_val2 < 0.2:
            if mean_val2 > 2.5:
                if mean_val2 >= (mean + 1):
                    return self.buy(bar.close_price, 1, type=OrderType.MARKET)
            elif mean_val2 < 2.5:
                if mean_val2 <= (mean - 1):
                    return self.short(bar.close_price, 1, type=OrderType.MARKET)

    def ma_trend_strategy(self, am:ArrayManager, bar:BarData, calc_data, setting={"len":40, "atr":40, "atr_valve":0.09, "mid_sign":(10,30)}):
        
        # 60个bar后取消
        if self.trend_record.std_val is not None:
            if len(self.trend_record.close) >= 60:
                self.trend_record.close = []
                self.trend_record.std_val = None
            else:
                self.trend_record.close.append(bar.close_price)
            
            
        # 如果有新的bar,则覆盖
        ma5_std = self.ma_info[-1]["ma5"]
        if ma5_std <= 0.16:
            self.trend_record.close = []
            self.trend_record.std_val = ma5_std
            return
        

        if  self.trend_record.std_val is not None and \
            ma5_std > 0.8:
            y_fit = reg_util.regress_y_polynomial(self.trend_record.close, zoom=True)
            deg = calc_regress_deg(y_fit[:10], False)

            if deg < 0:
                # if k < 20 and d < 10 and j < 10:
                # if kdj[2] < 10:
                if self.pos == 0:
                    calc_data["trade_open"] = "开空,deg={}".format(deg)
                    return self.short(bar.close_price, 1, type=OrderType.MARKET)

            else:
                # if k > 80 and d > 90 and j > 90:
                # if kdj[2] > 90:
                if self.pos == 0:
                    calc_data["trade_open"] = "开多,deg={}".format(deg)
                    return self.buy(bar.close_price, 1, type=OrderType.MARKET)




    # v形反转捕获
    def reverse_shape_strategy(self, am:ArrayManager, bar:BarData, calc_data, setting={"len":40, "atr":40, "atr_valve":0.09, "mid_sign":(10,30)}):
        length = setting["len"]
        offset1 = int(-length)
        offset2 = int(-(length / 2))
        close = am.close
        deg1 = calc_regress_deg(close[offset1:offset2], False)
        deg2 = calc_regress_deg(close[offset2:], False)
        

        atr = self.am.atr(setting["atr"])
        atr_valve = setting["atr_valve"]
        if atr < atr_valve:
            return

        if deg1 > 0 and deg2 > 0 or \
           deg1 < 0 and deg2 < 0:
            return
        
        if not (abs(deg1) > 0.15 and abs(deg2) > 0.1 and (abs(deg1) + abs(deg2)) > 0.3) :
            return

        close = am.close[-length:]
        min_val = np.min(close)
        max_val = np.max(close)
        mid_val =  max_val if deg1 > 0 else min_val
        mid_pos = np.where(close == mid_val)[0][0]

        if mid_pos < setting["mid_sign"][0] or mid_pos > setting["mid_sign"][1]:
            return

        start_val = np.min(close[:mid_pos]) if deg1 > 0 else np.max(close[:mid_pos])
        start_pos = np.where(close == start_val)[0][0]
        l = mid_pos - start_pos
        
        # pos2 = np.where(close == min_val)[0][0]
        kdj = am.kdj()
        k = kdj["k"][-1]
        d = kdj["d"][-1]
        j = kdj["j"][-1]
        x_fit = reg_util.regress_y_polynomial(close[:mid_pos], zoom=True)
        deg1_remake = calc_regress_deg(x_fit[:abs(mid_pos)], False)
        y_fit = reg_util.regress_y_polynomial(close[mid_pos:], zoom=True)
        deg2_remake = calc_regress_deg(y_fit[:abs(mid_pos)], False)
        # print(start_pos, mid_pos, deg1, deg2, deg1_remake, deg2_remake, l, start_val, mid_val)
        cci = am.cci(20)
        ma60 = am.sma(60)
        if deg2 < 0:
            # if k < 20 and d < 10 and j < 10:
            # if kdj[2] < 10:
            
            if cci < -100 and bar.close_price < ma60:
                if self.pos == 0:
                   calc_data["trade_open"] = "开空,deg={},cci={}".format(deg2, cci)
                   return self.short(bar.close_price, 1, type=OrderType.MARKET)
                elif self.pos > 0:
                   order_id_cover = self.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET)
                   order_id_buy = self.short(bar.close_price, 1, type=OrderType.MARKET)
                   return order_id_cover.extend(order_id_buy)
        else:
            # if k > 80 and d > 90 and j > 90:
            # if kdj[2] > 90:
            if cci > 100 and bar.close_price > ma60:
                
                if self.pos == 0:
                    calc_data["trade_open"] = "开多,deg={},cci={}".format(deg2, cci)
                    return self.buy(bar.close_price, 1, type=OrderType.MARKET)
                elif self.pos < 0:
                    order_id_cover = self.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET)
                    order_id_buy = self.buy(bar.close_price, 1, type=OrderType.MARKET)
                    return order_id_cover.extend(order_id_buy)

        # print("找到大v形:", deg1, deg2 )

    def ma120_close(self, am:ArrayManager, bar:BarData, calc_data):
        
        if self.safe_price is None:
            return

        rg = (bar.close_price / self.buy_price) - 1

        close_price = None
        if rg > 0.01 and self.volumn > 0:
            close_price = am.sma(120)
        elif rg < -0.01 and self.volumn < 0:
            close_price = am.sma(120)
            

        for lvl in self.ma_lvl[-1:]:
            # if len(self.order_data) < lvl:
            close_price = am.sma(lvl)
            break
        

        if close_price is None:
            lvl = self.ma_level[-1]
            close_price = am.sma(lvl)

        
        
        if self.volumn < 0:
            if bar.close_price > close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.strategy.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达MA均线价{}".format(close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.strategy.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra={"reason": "平仓:到达MA均线价{}".format(close_price)})


    
    def add_position(self, am:ArrayManager, bar:BarData, calc_data, setting={}):

        if self.safe_price is None:
            return

        if not (self.volumn < 0 and bar.close_price < self.safe_price or \
                self.volumn > 0 and bar.close_price > self.safe_price):
            return

        am = self.am
        rg = (bar.close_price / self.trade_price) - 1

        close_price = None
        if rg > 0.01 and self.volumn > 0:
            close_price = am.sma(120)
            if not self.add_pos:
                self.add_pos = True
                return self.strategy.buy(bar.close_price, 50, type=OrderType.MARKET) 
        elif rg < -0.01 and self.volumn < 0:
            close_price = am.sma(120)
            if not self.add_pos:
                self.add_pos = True
                return self.strategy.short(bar.close_price, 50, type=OrderType.MARKET) 

    def reverse2_strategy(self, am:ArrayManager, bar:BarData, calc_data, setting={"len":40, "atr":40, "atr_valve":0.09, "mid_sign":(10,30)}):
        length = 30
        offset1 = -30
        offset2 = int(-10)
        close = am.close
        deg1 = calc_regress_deg(close[-30:-8], False)
        deg2 = calc_regress_deg(close[-8:], False)
        

        if deg1 > 0 and deg2 > 0 or \
           deg1 < 0 and deg2 < 0:
            return
        
        if not (abs(deg1) > 0.15 and abs(deg2) > 0.15 and (abs(deg1) + abs(deg2)) > 0.35) :
            return

        close = am.close[-length:]
        min_val = np.min(close)
        max_val = np.max(close)
        mid_val =  max_val if deg1 > 0 else min_val
        mid_pos = np.where(close == mid_val)[0][0]

        if mid_pos < setting["mid_sign"][0] or mid_pos > setting["mid_sign"][1]:
            return

        start_val = np.min(close[:mid_pos]) if deg1 > 0 else np.max(close[:mid_pos])
        start_pos = np.where(close == start_val)[0][0]
        l = mid_pos - start_pos

        # pos2 = np.where(close == min_val)[0][0]
        kdj = am.kdj()
        k = kdj["k"][-1]
        d = kdj["d"][-1]
        j = kdj["j"][-1]
        x_fit = reg_util.regress_y_polynomial(close[:mid_pos], zoom=True)
        deg1_remake = calc_regress_deg(x_fit[:abs(mid_pos)], False)
        y_fit = reg_util.regress_y_polynomial(close[mid_pos:], zoom=True)
        deg2_remake = calc_regress_deg(y_fit[:abs(mid_pos)], False)
        # print(start_pos, mid_pos, deg1, deg2, deg1_remake, deg2_remake, l, start_val, mid_val)
        cci = am.cci(20)
        ma60 = am.sma(60)
        if deg2 < 0:
            # if k < 20 and d < 10 and j < 10:
            # if kdj[2] < 10:
            
            if cci < -100 and bar.close_price < ma60:
                if self.pos == 0:
                   calc_data["trade_open"] = "开空,deg={},cci={}".format(deg2, cci)
                   return self.short(bar.close_price, 1, type=OrderType.MARKET)
                elif self.pos > 0:
                   calc_data["trade_close"] = "平多后做空仓,deg={},cci={}".format(deg2, cci)
                   order_id_cover = self.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET)
                   order_id_buy = self.short(bar.close_price, 1, type=OrderType.MARKET)
                   return order_id_cover.extend(order_id_buy)
        else:
            # if k > 80 and d > 90 and j > 90:
            # if kdj[2] > 90:
            if cci > 100 and bar.close_price > ma60:
                
                if self.pos == 0:
                    calc_data["trade_open"] = "开多,deg={},cci={}".format(deg2, cci)
                    return self.buy(bar.close_price, 1, type=OrderType.MARKET)
                elif self.pos < 0:
                    calc_data["trade_close"] = "平空后多仓,deg={},cci={}".format(deg2, cci)
                    order_id_cover = self.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET)
                    order_id_buy = self.buy(bar.close_price, 1, type=OrderType.MARKET)
                    return order_id_cover.extend(order_id_buy)



    def open5(self, am:ArrayManager, bar:BarData, calc_data):
        
        ma = self.ma_tag[-1]
        mean = calc_data["mean30_10"]
        atr = self.am.atr(10, array=True, length=20)
        tr = self.am.atr(1, array=True, length=11)
        # self.ma120_track
        ma120 = self.am.sma(120)
        # if std_val2 < 0.2: 
        mean_std = calc_data["mean_std"]
        if mean_std < 0.8 and tr[-1] > 0.1 and tr[-1] / tr[-10] > 3 and tr[-1] / atr[-1] >= 1.7 and tr[-10] / atr[-10] < 1:
            if np.sum(self.am.range[-10:]) > 0 and self.ma120_track > 0:
                return self.buy(bar.close_price, 1, type=OrderType.MARKET)
            elif self.ma120_track < 0:
                return self.short(bar.close_price, 1, type=OrderType.MARKET)

    def open_kline1(self, am:ArrayManager, bar:BarData, calc_data):
        
        if KlinePattern.CDLEVENINGSTAR not in self.pattern_record:
            return
        # if std_val2 < 0.2: 
        deg = calc_regress_deg(self.am.close[-5:], False)
        print("kline_strategy",deg)
        if deg < -0.1:
            return self.short(bar.close_price, 1, type=OrderType.MARKET)
       
    def generate_data(self, am:ArrayManager, bar:BarData):
        offset = -self.offset
        offset_m = int(offset / 2)
        calc_nums = np.array(self.ma_tag[-offset:-1])
        # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        std_val2 = np.std(np.array(self.ma_tag[-10:-1]))
        std_val3 = np.std(np.array(am.range[-30:-10]))
        ma = self.ma_tag[-1]
        
        mean_val = np.mean(calc_nums)
        mean_val2 = np.mean(np.array(self.ma_tag[-5:-1]))
        mean_val3 = np.mean(np.array(self.ma_tag[-20:-1]))
        mean_val4 = np.mean(np.array(self.ma_tag[-30:-5]))
        
        kdj_val = am.kdj()
        has_kdj_recore = False
        k = kdj_val["k"]
        d = kdj_val["d"]
        j = kdj_val["j"]
        if  (k[-1] > 75 and d[-1] > 75 and j[-1] > 75) or \
            (k[-1] < 25 and d[-1] < 25 and j[-1] < 75):
            if (j[-2] < k[-2] or j[-2] < d[-2]) and (j[-1] > k[-1] and j[-1] > d[-1]) \
                or \
            (j[-2] > k[-2] or j[-2] > d[-2]) and (j[-1] < k[-1] and j[-1] < d[-1]):
                has_kdj_recore = True
                t = local_to_eastern(bar.datetime.timestamp())
                self.kdj_record.append((t.strftime("%H:%M:%S"), round(k[-1], 3), round(d[-1], 3), round(j[-1], 3)))

        
        deg1 = calc_regress_deg(am.close[offset : offset_m], False)
        deg2 = calc_regress_deg(am.close[offset_m :], False)
        deg3 = calc_regress_deg(am.close[-10 :], False)
        deg_full = calc_regress_deg(am.close[offset :], False)

        wave = self.wave(am.close[-30:])
        wave_r_sum = np.sum(wave["range"])


        macd=am.macd(20,40, 16)
        calc_data = (dict(
                ma_info=self.ma_info[-1:],
                kdj=[round(kdj_val["k"][-1],2),round(kdj_val["d"][-1],2),round(kdj_val["j"][-1],2)],
                cci_20=am.cci(20),rsi=am.rsi(20),adx=am.adx(20),boll=am.boll(20, 3.4),
                macd=[round(macd[0],2),round(macd[1],2),round(macd[2],2)],
                deg40_20=round(deg1,2), deg20_0=round(deg2,2), deg20_10=round(calc_regress_deg(am.close[-20:-10], False),2), 
                deg30_10=round(calc_regress_deg(am.close[-30:-10], False),2),deg10_0=round(deg3,2),
                deg30_15=round(calc_regress_deg(am.close[-30:-15], False),2), deg15_0=round(calc_regress_deg(am.close[-15:], False),2),deg_f=round(deg_full,2),
                atr=round(am.atr(10, length=15), 3), tr=round(am.atr(1, length=2), 3),atr_40=round(am.atr(40, length=42), 3),
                time=bar.datetime, price=bar.close_price, ma=round(ma, 2), 
                std_40=round(std_val, 2),mean40=round(mean_val,2), mean_std=np.mean(self.std_range.data[-5:]),
                std_10=round(std_val2,2), mean30_10=round(mean_val4,2), mean10=round(mean_val2,2),
                vol=am.volume[-1], std_range=self.std_range.data[-1:-5:-1], range=am.range[-1:-5:-1].tolist(),
                range_sum=np.sum(am.range[-5:]), 
                pattern=list(map(lambda x: KLINE_PATTERN_CHINESE[x], self.pattern_record.keys())),
                ma120t=self.ma120_track, 
                ma120t_list=self.ma120_track_list[-1:-10:-1], 
                ma120t_sort=sorted(self.ma120_track_list[-20:-1], key=abs),
                ma120t_sum=np.sum(self.ma120_track_list[-20:-1] + [self.ma120_track]), 
                ma120t_mean=np.mean(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                ma120t_std=np.std(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                wave_cnt=len(wave), wave_r_sum=wave_r_sum, atr_mean=np.mean(am.atr(20, array=True,length=240)[-200:]),
                kdj_record=self.kdj_record[-10:],
                ))
        if self.ma_info[-1]["ma5"] <= 0.16:
            calc_data["kdj_key"] = True
        return calc_data

    def generate_3mindata(self, am:ArrayManager, bar:BarData):
        offset = -self.offset
        offset_m = int(offset / 2)
        calc_nums = np.array(self.ma_tag[-offset:-1])
        # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        std_val2 = np.std(np.array(self.ma_tag[-10:-1]))
        std_val3 = np.std(np.array(am.range[-30:-10]))
        ma = self.ma_tag[-1]
        
        mean_val = np.mean(calc_nums)
        mean_val2 = np.mean(np.array(self.ma_tag[-5:-1]))
        mean_val3 = np.mean(np.array(self.ma_tag[-20:-1]))
        mean_val4 = np.mean(np.array(self.ma_tag[-30:-5]))
        kdj_val = am.kdj()

        deg1 = calc_regress_deg(am.close[offset : offset_m], False)
        deg2 = calc_regress_deg(am.close[offset_m :], False)
        deg3 = calc_regress_deg(am.close[-10 :], False)
        deg_full = calc_regress_deg(am.close[offset :], False)

        wave = self.wave(am.close[-30:])
        wave_r_sum = np.sum(wave["range"])
        macd=am.macd(20,40, 16)
        calc_data = (dict(
                kdj=[round(kdj_val["k"][-1],2),round(kdj_val["d"][-1],2),round(kdj_val["j"][-1],2)],
                cci_20=am.cci(20),rsi=am.rsi(20),adx=am.adx(20),boll=am.boll(20, 3.4),
                macd=[round(macd[0],2),round(macd[1],2),round(macd[2],2)],
                deg40_20=round(deg1,2), deg20_0=round(deg2,2), deg20_10=round(calc_regress_deg(am.close[-20:-10], False),2), deg10_0=round(deg3,2),
                deg30_15=round(calc_regress_deg(am.close[-30:-15], False),2), deg15_0=round(calc_regress_deg(am.close[-15:], False),2),deg_f=round(deg_full,2),
                atr=round(am.atr(10, length=15), 3), tr=round(am.atr(1, length=2), 3),atr_40=round(am.atr(40, length=42), 3),
                time=bar.datetime, price=bar.close_price, ma=round(ma, 2), 
                std_40=round(std_val, 2),mean40=round(mean_val,2), mean_std=np.mean(self.std_range.data[-5:]),
                std_10=round(std_val2,2), mean30_10=round(mean_val4,2), mean10=round(mean_val2,2),
                vol=am.volume[-1], std_range=self.std_range.data[-1:-5:-1], range=am.range[-1:-5:-1].tolist(),
                range_sum=np.sum(am.range[-5:]), 
                pattern=list(map(lambda x: KLINE_PATTERN_CHINESE[x], self.pattern_record.keys())),
                ma120t=self.ma120_track, 
                ma120t_list=self.ma120_track_list[-1:-10:-1], 
                ma120t_sort=sorted(self.ma120_track_list[-20:-1], key=abs),
                ma120t_sum=np.sum(self.ma120_track_list[-20:-1] + [self.ma120_track]), 
                ma120t_mean=np.mean(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                ma120t_std=np.std(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                ma_info=list(map(lambda x:x["std"], self.ma_info[-1:])),
                wave_cnt=len(wave), wave_r_sum=wave_r_sum, atr_mean=np.mean(am.atr(20, array=True,length=240)[-200:])
                ))

        return calc_data

    def on_strategy(self, am:ArrayManager, bar: BarData, strategy_list, close_strategy_list, calc_data=None):
        
            
        order_id = None

        for open_strategy in strategy_list:
            if order_id is not None:
                break
            order_id = open_strategy(am, bar, calc_data)

        if order_id is None and self.pos != 0:
            for strategy in close_strategy_list:
                if order_id is not None:
                    break
                order_id = strategy(am, bar, calc_data)

        
        if order_id is not None:
            offset = -self.offset
            offset_m = int(offset / 2)
            self.tracker["trade_info"].append((
                        self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, calc_data["deg40_20"], calc_data["deg20_0"]))
            self.request_order.extend(order_id)
        
        if self.tracker is not None:
            self.tracker["ma_tag_ls"].append(calc_data)

    def ma_info_update(self, am:ArrayManager):
        
        ma_info = {}
        ma_data = []
        for i in self.ma_level:
            ma = am.sma(i)
            ma_info[i] = round(ma,2)
            ma_data.append(ma)
        
        data = []
        diff = ma_data[-1]
        for v in ma_data:
            data.append(round(v / diff, 6))

        ma_info["ma5"] = round(np.var(data)*1000000, 8)

        data = []
        diff = ma_data[-3]
        for v in ma_data[:-2]:
            data.append(round(v / diff, 6))

        ma_info["ma3"] = round(np.var(data)*1000000, 8)

        if len(self.ma_info) < 500:
            self.ma_info.append(ma_info)
        else:
            self.ma_info[:-1] = self.ma_info[1:]
            self.ma_info[-1] = ma_info

    
    def on_1min_bar(self, bar: BarData):
        self.am.update_bar(bar)
        am = self.am
        

        max_len = self.ma_level[-1] + 20
        data = self.am.close[-max_len:-1]
        ma_lvl = []
        for i in self.ma_level:
            ma = self.am.sma(i, True)[-1]
            ma_lvl.append(ma)
        
        
        l = len(ma_lvl)
        ma_lvl_tag = []
        now = bar.close_price
        direction = 1 if now > ma_lvl[0] else 0
        ma_lvl_tag.append(direction)
        for i in range(l-1):
            val = 1 if ma_lvl[i] > ma_lvl[i+1] else 0
            ma_lvl_tag.append(val)
        bincount_val = np.bincount(np.array(ma_lvl_tag))
        tag_val = 0
        if len(bincount_val) == 2:
            tag_val = bincount_val[1]

        if len(self.ma_tag) < 200:
            self.ma_tag.append(tag_val)
        else:
            self.ma_tag[:-1] = self.ma_tag[1:]
            self.ma_tag[-1] = tag_val
        if self.tracker is not None:
            self.tracker["bar_data"].append(bar)
        self.std_range.update(self.am.range[-1])

        ma120 = self.am.sma(120)
        
        if bar.close_price >= ma120:
            if self.ma120_track is None:
                self.ma120_track = 1
            elif self.ma120_track > 0:
                self.ma120_track += 1
            else:
                self.ma120_track_list.append(self.ma120_track)
                self.ma120_track = 1
        elif bar.close_price < ma120:
            if self.ma120_track is None:
                self.ma120_track = -1
            elif self.ma120_track < 0:
                self.ma120_track -= 1
            else:
                self.ma120_track_list.append(self.ma120_track)
                self.ma120_track = -1



        if not am.inited or not self.trading:
            return

        self.ma_info_update(am)
        calc_data = self.generate_data(am, bar)
        five_min_open_5 = partial(self.reverse_shape_strategy, setting={"len":20, "atr":10, "atr_valve":0.8, "mid_sign":(7,14)})
        open_strategy = [self.reverse_shape_strategy, self.add_position]
        close_strategy = [self.positions.on_bar, self.ma120_close]
        self.on_strategy(am, bar, open_strategy, close_strategy, calc_data)
            # median_val = np.median(calc_nums)
        
        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg3.update_bar(bar)
        self.bg5.update_bar(bar)
        self.bg.update_bar(bar)

        

    # def init_order_data(self):
    #     self.order_data = np.array([])
        

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        print("{}产生了{},价格为{},笔数为{},交易{},pos={}".format(order.datetime.strftime("%m/%d %H:%M:%S"), order.offset.value + order.direction.value,order.price, order.volume, order.status.value, self.pos))
        
        if order.vt_orderid in self.request_order:
            if order.status == Status.ALLTRADED or order.status == Status.CANCELLED or order.status == Status.REJECTED:
                self.request_order.remove(order.vt_orderid)


    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.vt_orderid in self.request_order:
            self.positions.on_trade(trade)
            if self.volumn == 0:
                self.add_pos = False
                
                if trade.direction == Direction.LONG:
                    self.safe_price = trade.price * 1.003
                    self.volumn += trade.volume
                elif trade.direction == Direction.SHORT:
                    self.safe_price = trade.price * 0.997
                    self.volumn -= trade.volume
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
