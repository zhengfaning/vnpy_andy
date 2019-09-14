from vnpy.app.cta_strategy import (
    CtaTemplate,
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


class Position:
    volumn: int = 0
    level: int = 0
    close_price: float = 0.0
    buy_price: float = 0
    safe_price: float = 0
    order_data = np.array([])
    # 形态预测出错修正,日后增设级别在3以上才执行
    last_close_info = None
    guard = None

    def __init__(self, strategy):
        self.strategy: MaLevelTrackStrategy = strategy
        # self.am = self.strategy.am
        self.ma_tag = self.strategy.ma_tag
        self.close_process = [self.close1, self.close_ma120]

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

    def close1(self, bar:BarData, calc_data):
        if self.volumn < 0:
            if bar.close_price > self.close_price:
                return self.strategy.cover(self.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达最低价{}".format(self.close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < self.close_price:
                return self.strategy.sell(self.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra={"reason": "平仓:到达最低价{}".format(self.close_price)})

    def close_ma120(self, bar:BarData, calc_data):
        if not (self.volumn < 0 and bar.close_price < self.safe_price or \
                self.volumn > 0 and bar.close_price > self.safe_price):
                return

        am = self.strategy.am
        rg = (bar.close_price / self.buy_price) - 1

        close_price = None
        if rg > 0.01 and self.volumn > 0:
            close_price = am.sma(120, array=False, length=120+1)
            if self.level < 5:
                self.level = 5
                return self.strategy.buy(bar.close_price, 50, type=OrderType.MARKET) 
        elif rg < -0.01 and self.volumn < 0:
            close_price = am.sma(120, array=False, length=120+1)
            if self.level < 5:
                self.level = 5
                return self.strategy.short(bar.close_price, 50, type=OrderType.MARKET) 
            

        for lvl in self.strategy.ma_level[-1:]:
            if len(self.order_data) < lvl:
                close_price = am.sma(lvl, array=False, length=lvl+1)
                break
        

        if close_price is None:
            lvl = self.strategy.ma_level[-1]
            close_price = am.sma(lvl, array=False, length=lvl+1)

        
        
        if self.volumn < 0:
            if bar.close_price > close_price:
                return self.strategy.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达MA均线价{}".format(close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < close_price:
                return self.strategy.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                       extra={"reason": "平仓:到达MA均线价{}".format(close_price)})

    
    def close2(self, bar:BarData, calc_data):
        
        if self.level > 0:
            self.order_data = np.append(self.order_data, bar.close_price)
            order_id = None
            offset = -40
            offset_m = int(offset / 2)

            
            deg_full = calc_regress_deg(self.strategy.am.close[-10 :], False)
            
            if len(self.order_data) > abs(offset * 1.5):
                y_fit = reg_util.regress_y_polynomial(self.order_data, zoom=True)
                deg_order_short = calc_regress_deg(y_fit[:abs(offset)], False)

            if self.volumn > 0:
                if deg_full < -0.01:
                    # if abs(deg_order_short) < abs(deg_full):
                        return self.strategy.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET, 
                                extra={"reason":"平仓:趋势趋弱,deg={}".format(deg_full)})


            elif self.volumn < 0:
                if deg_full > 0.01:
                    # if abs(deg_order_short) < abs(deg_full):
                        return self.strategy.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET, 
                        extra={"reason": "平仓:趋势趋弱,deg={}".format(deg_full)})

            # print("pos<0", deg_order_short, deg_full)


    def on_strategy(self, bar:BarData, calc_data):
        if self.volumn == 0:
            return 
        
        if self.level == 0:
            if self.volumn > 0 and bar.close_price > self.safe_price:
                self.level += 1
            elif self.volumn < 0 and bar.close_price < self.safe_price:
                self.level += 1

        offset = -40
        calc_nums = np.array(self.ma_tag[-offset:-1])
                # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        mean_val = np.mean(calc_nums)
        
        if self.level == 1 and std_val < 0.8:
            # self.strategy.ma_tag[-1] > 3
            # level += 1
            if self.volumn > 0 and mean_val > 3.8:
                self.level += 1
            elif self.volumn < 0 and mean_val < 1.2:
                self.level += 1

        order_id = None 

        for close_process in self.close_process:
            order_id = close_process(bar, calc_data)
            if order_id is not None:
                break

        return order_id
            # # print(deg)
            # if abs(deg_order_short) < abs(deg_full):
            #     order_id = self.strategy.cover(bar.close_price, 1) 
    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()


    def on_order(self, order: OrderData):
        if order.status == Status.ALLTRADED:
            # pre_volumn = 0
            if order.direction == Direction.LONG:
                if self.volumn == 0:
                    self.close_price = round(order.price * 0.998, 2)
                    self.safe_price = order.price * 1.005
                    self.buy_price = order.price
                    self.order_data = np.array([])
                    self.level = 0
                self.volumn += order.volume
                
            elif order.direction == Direction.SHORT:
                if self.volumn == 0:
                    self.close_price = round(order.price * 1.002, 2)
                    self.order_data = np.array([])
                    self.buy_price = order.price
                    self.safe_price = order.price * 0.995
                    self.level = 0
                self.volumn -= order.volume

            elif order.direction == Direction.NET:
                self.volumn = order.volume
            
 
''' 
    TODO: 加入每日时间识别
    TODO: 加入红绿十字星识别
    TODO: 加入十字星后,快速趋势判断购买
    TODO: 加入高吊线和低线识别
    TODO: 策略架构改进,多个策略并存
'''
class MaLevelTrackStrategy(CtaTemplate):
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
    
    
    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MaLevelTrackStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar, 1, self.on_1min_bar)
        self.am = ArrayManager(400)
        self.am3 = ArrayManager(150)
        self.bg3 = BarGenerator(self.on_bar, 3, self.on_3min_bar)
        self.am5 = ArrayManager(120)
        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.order_data = None
        self.positions = Position(self)
        self.std_range = IntervalGen(np.std,5)
        self.std_range3 = IntervalGen(np.std,5)        
        self.std_range5 = IntervalGen(np.std,5)
        self.pattern_record = PatternRecord()
        # self.pattern_record.set_expiry([KlinePattern.CDLEVENINGSTAR], 3)
        self.pattern_record.set_expiry(list(KlinePattern), 1)
        
        self.open_strategy = [self.open6]
        self.offset = 40
        self.ma120_track = None
        self.ma120_track_list = []
    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

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
                        if abs(diff / r[start_pos]) > window and d_tag - start_pos > 1:
                            end_tag = d_tag
                            
                elif now > r[pos]:
                    d_tag = pos
                    if u_tag:
                        diff = r[start_pos] - r[u_tag]
                        if abs(diff / r[start_pos]) > window and d_tag - start_pos > 1:
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
        # pattern_list = [KlinePattern.CDLEVENINGSTAR, KlinePattern.CDL2CROWS, KlinePattern.CDLCONCEALBABYSWALL, KlinePattern.CDLEVENINGDOJISTAR]
    #     pattern = self.am5.pattern(list(KlinePattern))
    #     if len(pattern) > 0:
    #         print(list(map(lambda x: (KLINE_PATTERN_CHINESE[x[0]],x[1]), pattern)))
    #         self.pattern_record.add_pattern(pattern)
    #         deg_full = calc_regress_deg(self.am.close[-40 :], False)
    #         print("deg:",deg_full)
        
    #     self.pattern_record.update()

    def open_v3(self, bar:BarData):
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

    def open_v1(self, bar:BarData):
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
    
    def open_v2(self, bar:BarData):
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

    
    def open2(self, bar:BarData, calc_data):
        deg = calc_data["deg20"]
        ma = self.ma_tag[-1]
        if deg > 0.5 and ma > 3 and self.am5.range[-1] > -0.002:
            return self.buy(bar.close_price, 1, type=OrderType.MARKET)
        elif deg < -0.5 and ma < 2 and self.am5.range[-1] < 0.002:
            return self.short(bar.close_price, 1, type=OrderType.MARKET)  

    def open1(self, bar:BarData, calc_data):
        
        mean = calc_data["mean30_10"]
        mean_val2 = calc_data["mean10"]
        # if std_val2 < 0.2: 
        if mean_val2 > 3.5 and mean_val2 >= (mean + 2):
                return self.buy(bar.close_price, 1, type=OrderType.MARKET)
        elif mean_val2 < 1.5 and mean_val2 <= (mean - 2):
                return self.short(bar.close_price, 1, type=OrderType.MARKET)

    # v形反转捕获
    def open6(self, bar:BarData, calc_data):
        
        deg1 = calc_data["deg40_20"]
        deg2 = calc_data["deg20_0"]
        kdj = calc_data["kdj"]

        atr = self.am.atr(40, length=42)


        

        if atr < 0.08:
            return

        if deg1 > 0 and deg2 > 0 or \
           deg1 < 0 and deg2 < 0:
            return
        
        if not (abs(deg1) > 0.15 and abs(deg2) > 0.1 and (abs(deg1) + abs(deg2)) > 0.3) :
            return

        close = self.am.close[-40:]
        min_val = np.min(close)
        max_val = np.max(close)
        mid_val =  max_val if deg1 > 0 else min_val
        mid_pos = np.where(close == mid_val)[0][0]

        if mid_pos < 10 or mid_pos > 30:
            return

        start_val = np.min(close[:mid_pos]) if deg1 > 0 else np.max(close[:mid_pos])
        start_pos = np.where(close == start_val)[0][0]
        l = mid_pos - start_pos
        



        # pos2 = np.where(close == min_val)[0][0]
        
        x_fit = reg_util.regress_y_polynomial(close[:mid_pos], zoom=True)
        deg1_remake = calc_regress_deg(x_fit[:abs(mid_pos)], False)
        y_fit = reg_util.regress_y_polynomial(close[mid_pos:], zoom=True)
        deg2_remake = calc_regress_deg(y_fit[:abs(mid_pos)], False)
        print(start_pos, mid_pos, deg1, deg2, deg1_remake, deg2_remake, l, start_val, mid_val)
        if deg2 < 0:
            if kdj[0] < 20 and kdj[1] < 10 and kdj[2] < 10:
            # if kdj[2] < 10:
                return self.short(bar.close_price, 1, type=OrderType.MARKET)
        else:
            if kdj[0] > 80 and kdj[1] > 90 and kdj[2] > 90:
            # if kdj[2] > 90:
                return self.buy(bar.close_price, 1, type=OrderType.MARKET)

        # print("找到大v形:", deg1, deg2 )



    def open5(self, bar:BarData, calc_data):
        
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

    def open_kline1(self, bar:BarData, calc_data):
        
        if KlinePattern.CDLEVENINGSTAR not in self.pattern_record:
            return
        # if std_val2 < 0.2: 
        deg = calc_regress_deg(self.am.close[-5:], False)
        print("kline_strategy",deg)
        if deg < -0.1:
            return self.short(bar.close_price, 1, type=OrderType.MARKET)
       
    def generate_data(self, bar:BarData):
        offset = -self.offset
        offset_m = int(offset / 2)
        calc_nums = np.array(self.ma_tag[-offset:-1])
        # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        std_val2 = np.std(np.array(self.ma_tag[-10:-1]))
        std_val3 = np.std(np.array(self.am.range[-30:-10]))
        ma = self.ma_tag[-1]
        
        mean_val = np.mean(calc_nums)
        mean_val2 = np.mean(np.array(self.ma_tag[-5:-1]))
        mean_val3 = np.mean(np.array(self.ma_tag[-20:-1]))
        mean_val4 = np.mean(np.array(self.ma_tag[-30:-5]))
        kdj_val = self.am.kdj()

        deg1 = calc_regress_deg(self.am.close[offset : offset_m], False)
        deg2 = calc_regress_deg(self.am.close[offset_m :], False)
        deg3 = calc_regress_deg(self.am.close[-10 :], False)
        deg_full = calc_regress_deg(self.am.close[offset :], False)

        wave = self.wave(self.am.close[-30:])
        wave_r_sum = np.sum(wave["range"])

        calc_data = (dict(
                kdj=[round(kdj_val["k"][-1],2),round(kdj_val["d"][-1],2),round(kdj_val["j"][-1],2)],
                cci_20=self.am.cci(20),rsi=self.am.rsi(20),adx=self.am.adx(20),boll=self.am.boll(20, 3.4),
                deg40_20=round(deg1,2), deg20_0=round(deg2,2), deg20_10=round(calc_regress_deg(self.am.close[-20:-10], False),2), deg10_0=round(deg3,2),
                deg30_15=round(calc_regress_deg(self.am.close[-30:-15], False),2), deg15_0=round(calc_regress_deg(self.am.close[-15:], False),2),deg_f=round(deg_full,2),
                atr=round(self.am.atr(10, length=15), 3), tr=round(self.am.atr(1, length=2), 3),atr_40=round(self.am.atr(40, length=42), 3),
                time=bar.datetime, price=bar.close_price, ma=round(ma, 2), 
                std_40=round(std_val, 2),mean40=round(mean_val,2), mean_std=np.mean(self.std_range.data[-5:]),
                std_10=round(std_val2,2), mean30_10=round(mean_val4,2), mean10=round(mean_val2,2),
                vol=self.am.volume[-1], std_range=self.std_range.data[-1:-5:-1], range=self.am.range[-1:-5:-1].tolist(),
                range_sum=np.sum(self.am.range[-5:]), 
                pattern=list(map(lambda x: KLINE_PATTERN_CHINESE[x], self.pattern_record.keys())),
                ma120t=self.ma120_track, 
                ma120t_list=self.ma120_track_list[-1:-10:-1], 
                ma120t_sort=sorted(self.ma120_track_list[-20:-1], key=abs),
                ma120t_sum=np.sum(self.ma120_track_list[-20:-1] + [self.ma120_track]), 
                ma120t_mean=np.mean(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                ma120t_std=np.std(self.ma120_track_list[-20:-1] + [self.ma120_track]),
                wave_cnt=len(wave), wave_r_sum=wave_r_sum, atr_mean=np.mean(self.am.atr(20, array=True,length=240)[-200:])
                ))

        return calc_data

    def on_strategy(self, bar: BarData):
        calc_data = self.generate_data(bar)
            
        order_id = None
        if self.pos == 0:
            for open_strategy in self.open_strategy:
                if order_id is not None:
                    break
                order_id = open_strategy(bar, calc_data)
        else:
            order_id = self.positions.on_strategy(bar, calc_data)

        
        if order_id is not None:
            offset = -self.offset
            offset_m = int(offset / 2)
            self.tracker["trade_info"].append((
                        self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, calc_data["deg40_20"], calc_data["deg20_0"]))
            self.request_order.extend(order_id)
        
        if self.tracker is not None:
            self.tracker["ma_tag_ls"].append(calc_data)
    
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
        
        
        
        self.on_strategy(bar)
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
            self.positions.on_order(order)
            if order.status == Status.ALLTRADED or order.status == Status.CANCELLED or order.status == Status.REJECTED:
                self.request_order.remove(order.vt_orderid)
        # if order.status == Status.ALLTRADED or order.status == Status.PARTTRADED:
        #     if order.direction == Direction.LONG:
        #         if self.positions.volumn == 0:
        #             self.positions.close_price = round(order.price * 0.995)
        #         self.positions.volumn += order.volume
        #     elif order.direction == Direction.SHORT:
        #         self.positions.volumn -= order.volume
        #     elif order.direction == Direction.NET:
        #         self.positions.volumn = order.volume

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
