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
from abu.UtilBu.ABuRegUtil import calc_regress_deg
import abu.UtilBu.ABuRegUtil as reg_util
from vnpy.app.cta_strategy.strategies.ma_trend.analyse_wave import AnalyseWave
from vnpy.app.cta_strategy.strategies.ma_trend.data_creator.ma_dist import MaDistCreator
from vnpy.app.cta_strategy.strategies.ma_trend.data_creator.ma_info import MaInfoCreator
from vnpy.app.cta_strategy.strategies.ma_trend.data_creator.trend_info import TrendInfoCreator
from vnpy.app.cta_strategy.strategies.ma_trend.data_center import DataCenter
from vnpy.app.cta_strategy.strategies.ma_trend.time_manager import ClockManager
from vnpy.app.cta_strategy.trader_mgr import PositionStatus, TradeMgr
from vnpy.trader.utility import IntervalGen
from vnpy.trader.constant import Direction, Status, OrderType, KlinePattern, KLINE_PATTERN_CHINESE
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import datetime
from pytz import timezone
import math

eastern = timezone('US/Eastern')


def local_to_eastern(unix_time):
    return datetime.datetime.fromtimestamp(unix_time, eastern)


class State:

    def __init__(self, context):
        self.context = context

    def enter(self):
        pass

    def exit(self):
        pass

    def on_bar(self):
        pass


class LongProcess(State):
    def __init__(self, context):
        self.context = context

    def enter(self):
        pass

    def exit(self):
        pass

    def on_bar(self):
        pass


class ShortProcess(State):
    def __init__(self, context):
        self.context = context

    def enter(self):
        pass

    def exit(self):
        pass

    def on_bar(self):
        pass


class PatternRecord:
    data = {}
    expiry = {}

    def __init__(self):
        pass

    def add_pattern(self, pattern_list):
        for item in pattern_list:
            self.data[item[0]] = dict(count=0, value=item[1])

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


''' 
    TODO: 加入每日时间识别
    TODO: 加入红绿十字星识别
    TODO: 加入十字星后,快速趋势判断购买
    TODO: 加入高吊线和低线识别
    TODO: 策略架构改进,多个策略并存
'''


# 负责买入卖出的信息管理,仓位管理,资金管理,半仓,4分之1仓

class MaTrendStrategy(CtaTemplate):
    author = "用Python的交易员"

    ma_level = [10, 20, 30, 60, 120]

    request_order = []
    close_order = []

    volumn = 0
    kdj_record = []
    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]
    add_pos = False
    safe_price = None
    ma_info = pd.DataFrame()
    closeout_offset = 0.003
    trade_mgr: TradeMgr = None

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MaTrendStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar, 1, self.on_1min_bar, tz_info=eastern)
        self.am = ArrayManager(400)
        self.am3 = ArrayManager(150)
        self.bg3 = BarGenerator(self.on_bar, 3, self.on_3min_bar, tz_info=eastern)
        self.am5 = ArrayManager(100)
        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar, tz_info=eastern)
        self.trade_mgr = TradeMgr(self, setting["capital"], OrderType.MARKET, {})
        self.closeout_offset = 0.003
        self.clock = ClockManager(datetime.time(hour=9, minute=30), datetime.time(hour=16, minute=0))

        self.std_range = IntervalGen(np.std, 5)
        self.std_range3 = IntervalGen(np.std, 5)
        self.std_range5 = IntervalGen(np.std, 5)
        self.pattern_record = PatternRecord()
        # self.pattern_record.set_expiry([KlinePattern.CDLEVENINGSTAR], 3)
        self.pattern_record.set_expiry(list(KlinePattern), 1)
        self.offset = 40
        self.init_datacreator()

    def init_datacreator(self):
        self.data_center = DataCenter(component={"array_manager_1": self.am, "clock": self.clock})

        self.data_creator = {
            "ma_info": MaInfoCreator(self.data_center),
            "trend_info": TrendInfoCreator(self.data_center),
            "ma_dist": MaDistCreator(self.data_center)
        }
        self.ma_info = self.data_creator["ma_info"]
        self.data_center.connect("trend_info", self.on_new_trend)

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

    def on_5min_bar(self, bar: BarData):
        self.std_range5.update(self.am5.range[-1])
        self.am5.update_bar(bar)
        if not self.am.inited or not self.trading:
            return

    def closeout_strategy(self, am: ArrayManager, bar: BarData, calc_data):
        if self.trade_mgr.get_status() == PositionStatus.Short:
            if bar.close_price > self.closeout_price:
                calc_data["trade_close"] = "平仓:到达最低价{}".format(self.closeout_price)
                return self.trade_mgr.cover(bar.close_price)
                # return self.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                #                   extra={"reason": "平仓:到达最低价{}".format(self.closeout_price)})
        elif self.trade_mgr.get_status() == PositionStatus.Long:
            if bar.close_price < self.closeout_price:
                calc_data["trade_close"] = "平仓:到达最低价{}".format(self.closeout_price)
                return self.trade_mgr.sell(bar.close_price)
                # return self.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                #        extra={"reason": "平仓:到达最低价{}".format(self.closeout_price)})

    ''' 
        检测3个ma闭合,空仓状态时如果小于0.01则标记起点,随后检测4个ma的穿越,计算角度,并买入。
        根据时间和升幅进行加仓(急速提升的情况下,3ma的闭合间隙会加大),
        3个ma如果遭遇再次闭合,则根据情况卖出
        
    '''

    def on_new_trend(self, data):
        self.trend_context = data["trend_info"]

    def range_score(self, am: ArrayManager, length):
        r_data = am.range[-length:]

    def ma_trend_strategy(self, am: ArrayManager, bar: BarData, calc_data):
        context = self.trend_context
        if context == None:
            return

        deg = context["deg"]
        data = context["data"]
        sign = context["sign"]
        if self.pos == 0:
            ma120 = self.ma_info.info[120]

            deg120 = calc_regress_deg(ma120[-5:], False)
            if deg < 0:
                calc_data["trade_open"] = "开空,deg={}".format(deg)
                sign()
                ratio = 0.2 if deg120 < 0 else 0.1
                return self.trade_mgr.short(bar.close_price, ratio, {})
            elif deg > 0:
                calc_data["trade_open"] = "开多,deg={}".format(deg)
                sign()
                ratio = 0.2 if deg120 > 0 else 0.1
                return self.trade_mgr.buy(bar.close_price, ratio, {})

    def trend_reverse_close(self, am: ArrayManager, bar: BarData, calc_data):

        if self.trade_mgr.get_status() != PositionStatus.Empty:
            data = self.ma_info.info[-60:]
            length = len(data)
            close = (data[10] + data[20] + data[30]) / 3
            if length > 10:
                y_fit = reg_util.regress_y_polynomial(close[-10:], zoom=True)
                deg = calc_regress_deg(y_fit[:10], False)
            else:
                deg = calc_regress_deg(close[-10:], False)

            calc_data["trade_close_deg"] = deg
            if self.trade_mgr.get_status() == PositionStatus.Short:

                if deg > 0.01:
                    calc_data["trade_close"] = "平仓:趋势反转{}".format(deg)
                    return self.trade_mgr.cover(bar.close_price)
            elif self.trade_mgr.get_status() == PositionStatus.Long:
                if deg < -0.01:
                    calc_data["trade_close"] = "平仓:趋势反转{}".format(deg)
                    return self.trade_mgr.sell(bar.close_price)

    def ma_close(self, am: ArrayManager, bar: BarData, calc_data):

        if self.safe_price is None:
            return

        rg = (bar.close_price / self.trade_price) - 1

        close_price = None
        if rg > 0.01 and self.trade_mgr.get_status() == PositionStatus.Long:
            close_price = am.sma(120)
        elif rg < -0.01 and self.trade_mgr.get_status() == PositionStatus.Short:
            close_price = am.sma(120)

        for lvl in self.ma_level[-1:]:
            # if len(self.order_data) < lvl:
            close_price = am.sma(lvl)
            break

        if close_price is None:
            lvl = self.ma_level[-1]
            close_price = am.sma(lvl)

        if self.trade_mgr.get_status() == PositionStatus.Short:
            if bar.close_price > close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.trade_mgr.cover(bar.close_price)
                # return self.cover(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                #        extra= { "reason":"平仓:到达MA均线价{}".format(close_price)})

        elif self.trade_mgr.get_status() == PositionStatus.Long:
            if bar.close_price < close_price:
                calc_data["trade_close"] = "平仓:到达MA均线价{}".format(close_price)
                return self.trade_mgr.sell(bar.close_price)
                # return self.sell(bar.close_price, abs(self.volumn), type=OrderType.MARKET,
                #        extra={"reason": "平仓:到达MA均线价{}".format(close_price)})

    # 加仓算法
    def add_position(self, am: ArrayManager, bar: BarData, calc_data, setting={}):

        if self.safe_price is None:
            return

        if not (self.trade_mgr.get_status() == PositionStatus.Short and bar.close_price < self.safe_price or \
                self.trade_mgr.get_status() == PositionStatus.Long and bar.close_price > self.safe_price):
            return

        am = self.am
        rg = (bar.close_price / self.trade_price) - 1

        close_price = None
        if rg > 0.01 and self.trade_mgr.get_status() == PositionStatus.Long:
            close_price = am.sma(120)
            if not self.add_pos:
                self.add_pos = True
                # scale = 1 - 0.002
                # self.closeout_price = round(bar.close_price * scale, 2)
                return self.trade_mgr.buy(bar.close_price, 0.1, {})
        elif rg < -0.01 and self.trade_mgr.get_status() == PositionStatus.Short:
            close_price = am.sma(120)
            if not self.add_pos:
                self.add_pos = True
                # scale = 1 + 0.002
                # self.closeout_price = round(bar.close_price * scale, 2)
                return self.trade_mgr.short(bar.close_price, 0.1, {})

    def generate_data(self, am: ArrayManager, bar: BarData):
        offset = -self.offset
        offset_m = int(offset / 2)

        std_val3 = np.std(np.array(am.range[-30:-10]))

        kdj_val = am.kdj()
        has_kdj_recore = False
        k = kdj_val["k"]
        d = kdj_val["d"]
        j = kdj_val["j"]
        if (k[-1] > 75 and d[-1] > 75 and j[-1] > 75) or \
                (k[-1] < 25 and d[-1] < 25 and j[-1] < 75):
            if (j[-2] < k[-2] or j[-2] < d[-2]) and (j[-1] > k[-1] and j[-1] > d[-1]) \
                    or \
                    (j[-2] > k[-2] or j[-2] > d[-2]) and (j[-1] < k[-1] and j[-1] < d[-1]):
                has_kdj_recore = True
                t = bar.datetime
                self.kdj_record.append((t.strftime("%H:%M:%S"), round(k[-1], 3), round(d[-1], 3), round(j[-1], 3)))

        deg1 = calc_regress_deg(am.close[offset: offset_m], False)
        deg2 = calc_regress_deg(am.close[offset_m:], False)
        deg3 = calc_regress_deg(am.close[-10:], False)
        deg_full = calc_regress_deg(am.close[offset:], False)

        macd = am.macd(20, 40, 16)

        calc_data = (dict(
            kdj=[round(kdj_val["k"][-1], 2), round(kdj_val["d"][-1], 2), round(kdj_val["j"][-1], 2)],
            cci_20=am.cci(20), rsi=am.rsi(20), adx=am.adx(20), boll=am.boll(20, 3.4),
            macd=[round(macd[0], 2), round(macd[1], 2), round(macd[2], 2)],
            deg40_20=round(deg1, 2), deg20_0=round(deg2, 2),
            deg20_10=round(calc_regress_deg(am.close[-20:-10], False), 2),
            deg30_15=round(calc_regress_deg(am.close[-30:-15], False), 2),
            deg15_0=round(calc_regress_deg(am.close[-15:], False), 2), deg_f=round(deg_full, 2),
            deg30_10=round(calc_regress_deg(am.close[-30:-10], False), 2), deg10_0=round(deg3, 2),
            atr=round(am.atr(10, length=15), 3), tr=round(am.atr(1, length=2), 3),
            atr_40=round(am.atr(40, length=42), 3),
            time=bar.datetime, price=bar.close_price,
            mean_std=np.mean(self.std_range.data[-5:]),
            vol=am.volume[-1], std_range=self.std_range.data[-1:-5:-1], range=am.range[-1:-5:-1].tolist(),
            range_sum=np.sum(am.range[-5:]),
            pattern=list(map(lambda x: KLINE_PATTERN_CHINESE[x], self.pattern_record.keys())),
            atr_mean=np.mean(am.atr(20, array=True, length=240)[-200:]),
        ))
        if self.ma_info.info.index.size >= 31:
            ma5 = self.ma_info.info[5][-31:]
            x = AnalyseWave(ma5)
            calc_data["ma5_info"] = x.optimize
            ma10 = self.ma_info.info[10][-31:]
            x = AnalyseWave(ma10)
            calc_data["ma10_info"] = x.optimize
        return calc_data

    def on_strategy(self, am: ArrayManager, bar: BarData, strategy_list, close_strategy_list, calc_data=None):

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
                self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, calc_data["deg40_20"],
                calc_data["deg20_0"]))
            self.request_order.extend(order_id)

        if self.tracker is not None:
            self.tracker["ma_tag_ls"].append(calc_data)

    def on_1min_bar(self, bar: BarData):
        self.trend_context = None
        self.am.update_bar(bar)
        am = self.am

        max_len = self.ma_level[-1] + 20
        data = self.am.close[-max_len:-1]

        if self.tracker is not None:
            self.tracker["bar_data"].append(bar)
        self.std_range.update(self.am.range[-1])

        self.data_center.push("bar_data", bar)
        self.data_center.push("array_manager", self.am)

        if not am.inited or not self.trading:
            return

        calc_data = self.generate_data(am, bar)
        open_strategy = [self.ma_trend_strategy, self.add_position]
        close_strategy = [self.ma_trend_strategy2, self.closeout_strategy, self.trend_reverse_close]
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

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        print("{}产生了{},价格为{},笔数为{},交易{},pos={}".format(order.datetime.strftime("%m/%d %H:%M:%S"),
                                                       order.offset.value + order.direction.value, order.price,
                                                       order.volume, order.status.value, self.pos))
        self.trade_mgr.on_order(order)
        if order.vt_orderid in self.request_order:
            if order.status == Status.ALLTRADED or order.status == Status.CANCELLED or order.status == Status.REJECTED:
                self.close_order.append(order.vt_orderid)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.trade_mgr.on_trade(trade)
        if trade.vt_orderid in self.request_order:
            # self.positions.on_trade(trade)
            if self.volumn == 0:
                self.add_pos = False
                self.trade_price = trade.price
                if trade.direction == Direction.LONG:
                    self.safe_price = trade.price * 1.003
                    scale = 1 - self.closeout_offset
                    self.closeout_price = round(trade.price * scale, 2)
                elif trade.direction == Direction.SHORT:
                    self.safe_price = trade.price * 0.997
                    scale = 1 + self.closeout_offset
                    self.closeout_price = round(trade.price * scale, 2)

            if trade.direction == Direction.LONG:
                self.volumn += trade.volume
            elif trade.direction == Direction.SHORT:
                self.volumn -= trade.volume

            if trade.vt_orderid in self.close_order:
                self.request_order.remove(trade.vt_orderid)
                self.close_order.remove(trade.vt_orderid)
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def ma_trend_strategy2(self, am: ArrayManager, bar: BarData, calc_data):
        context = self.trend_context
        if context == None:
            return

        deg = context["deg"]
        data = context["data"]
        sign = context["sign"]
        if self.pos > 0 and deg < 0:
            ma120 = self.ma_info.info[120]

            calc_data["trade_open"] = "平仓并开空,deg={}".format(deg)
            sign()
            self.trade_mgr.sell(bar.close_price)
            return self.trade_mgr.short(bar.close_price, 0.1, {})
        elif self.pos < 0 and deg > 0:
            calc_data["trade_open"] = "开多,deg={}".format(deg)
            sign()
            self.trade_mgr.cover(bar.close_price)
            return self.trade_mgr.buy(bar.close_price, 0.1, {})

        '''
        def ma_trend_strategy(self, am: ArrayManager, bar: BarData, calc_data,
                              setting={"len": 40, "atr": 40, "atr_valve": 0.09, "mid_sign": (10, 30)}):

            # if bar.close_price == 185.42:
            #     print("ok")
            # 如果有新的bar,则覆盖
            if self.trend_monitor.length() == 0:
                return

            ma_info = self.trend_monitor.info()
            ma3_std = ma_info["ma3"]
            # 60个bar后取消
            len = self.trend_monitor.length()

            if self.pos == 0:
                if ma3_std < 0.1:
                    return
                close = None
                count = 0
                # for lvl in self.ma_level[:-2]:
                #     count += 1
                #     if close is None:
                #         close = self.trend_record.data[lvl]
                #     else:
                #         close += self.trend_record.data[lvl]
                # close = close / count
                close = (self.trend_monitor.data[10] + self.trend_monitor.data[20] + self.trend_monitor.data[30]) / 3
                if len > 10:
                    y_fit = reg_util.regress_y_polynomial(close, zoom=True)
                    deg = calc_regress_deg(y_fit[:10], False)
                    ma120 = self.trend_monitor.data[120]
                    # y_fit = reg_util.regress_y_polynomial(ma120, zoom=True)
                    deg120 = calc_regress_deg(ma120[-5:], False)
                else:
                    deg = calc_regress_deg(close, False)
                    ma120 = self.trend_monitor.data[120]
                    deg120 = calc_regress_deg(ma120, False)

                if abs(deg) < 0.03:
                    return

                if deg < 0:
                    # if k < 20 and d < 10 and j < 10:
                    # if kdj[2] < 10:
                    num = 0
                    if self.trend_monitor.trend_point["ma3_5_ref"] > self.trend_monitor.data["ma3_5_ref"][-1]:
                        num = 50
                    elif deg120 < 0:
                        num = 1
                    if num > 0:
                        calc_data["trade_open"] = "开空,deg={},deg120={}".format(deg, deg120)
                        return self.trade_mgr.short(bar.close_price, PositionRadio.Eighth, {})
                        # calc_data["trade_open"] = "开空,deg={},deg120={}".format(deg, deg120)
                        # return self.short(bar.close_price, num, type=OrderType.MARKET)
                elif deg > 0:
                    # if k > 80 and d > 90 and j > 90:
                    # if kdj[2] > 90:
                    num = 0
                    if self.trend_monitor.trend_point["ma3_5_ref"] > self.trend_monitor.data["ma3_5_ref"][-1]:

                        num = 50
                    elif deg120 > 0:
                        num = 1
                    if num > 0:
                        calc_data["trade_open"] = "开多,deg={},deg120={}".format(deg, deg120)
                        return self.trade_mgr.buy(bar.close_price, PositionRadio.Eighth, {})
                        # calc_data["trade_open"] = "开多,deg={},deg120={}".format(deg, deg120)
                        # return self.buy(bar.close_price, num, type=OrderType.MARKET)
            else:
                if self.pos < 0:
                    close = self.am.close[-len:]
                    start_val = np.min(close)
                    r = np.where(start_val)
                    pos = r[0][0]
                    # ma_list = {}
                    # for i in self.ma_level[:-2]:
                    #     if i not in ma_list:
                    #         ma_list[i] = []

                    #     ma = self.ma_info[-1][i]

    '''

    # def ma_trend_strategy_xx(self, am:ArrayManager, bar:BarData, calc_data, setting={"len":40, "atr":40, "atr_valve":0.09, "mid_sign":(10,30)}):

    #     if bar.close_price == 185.42:
    #         print("ok")
    #     # 如果有新的bar,则覆盖
    #     ma_info = self.ma_info.iloc[-1]
    #     ma3_std = ma_info["ma3"]
    #     ma5_std = ma_info["ma5"]
    #     mid_ma = ma_info[20]
    #     if ma3_std <= self.threshold["ma3"]:
    #         self.reset_trend_record(ma_info)
    #         self.trend_record.data = self.ma_info[-10:-1]

    #     if  self.trend_record.ma_info is None:
    #         return

    #     # 60个bar后取消
    #     l = self.trend_record.data.index.size
    #     if l >= 60:
    #         self.reset_trend_record()
    #         return
    #     else:
    #         self.trend_record.data = self.trend_record.data.append(ma_info)
    #         l += 1

    #     if l < 3:
    #         return
    #     if self.pos == 0:
    #         if ma3_std < 0.1:
    #             return
    #         close = None
    #         count = 0
    #         # for lvl in self.ma_level[:-2]:
    #         #     count += 1
    #         #     if close is None:
    #         #         close = self.trend_record.data[lvl]
    #         #     else:
    #         #         close += self.trend_record.data[lvl]
    #         # close = close / count
    #         close = (self.trend_record.data[10] + self.trend_record.data[20] + self.trend_record.data[30]) / 3
    #         if l > 10:
    #             y_fit = reg_util.regress_y_polynomial(close, zoom=True)
    #             deg = calc_regress_deg(y_fit[:10], False)
    #         else:
    #             deg = calc_regress_deg(close, False)

    #         if abs(deg) < 0.03:
    #             return

    #         if deg < 0:
    #             # if k < 20 and d < 10 and j < 10:
    #             # if kdj[2] < 10:
    #             if self.trend_record.ma_info["ma3_5_ref"] > self.trend_record.data["ma3_5_ref"][-1]:
    #                 calc_data["trade_open"] = "开空,deg={},ma3_5_ref={}".format(deg, self.trend_record.data["ma3_5_ref"][-1])
    #                 return self.short(bar.close_price, 1, type=OrderType.MARKET)

    #         elif deg > 0:
    #             # if k > 80 and d > 90 and j > 90:
    #             # if kdj[2] > 90:
    #             if self.trend_record.ma_info["ma3_5_ref"] < self.trend_record.data["ma3_5_ref"][-1]:
    #                 calc_data["trade_open"] = "开多,deg={},ma3_5_ref={}".format(deg, self.trend_record.data["ma3_5_ref"][-1])
    #                 return self.buy(bar.close_price, 1, type=OrderType.MARKET)
    #     else:
    #         if self.pos < 0:
    #             close = self.am.close[-l:]
    #             start_val = np.min(close)
    #             r = np.where(start_val)
    #             pos = r[0][0]
    #             # ma_list = {}
    #             # for i in self.ma_level[:-2]:
    #             #     if i not in ma_list:
    #             #         ma_list[i] = []

    #             #     ma = self.ma_info[-1][i]

    # def ma_trend_strategy2(self, am: ArrayManager, bar: BarData, calc_data,
    #                       setting={"len": 40, "atr": 40, "atr_valve": 0.09, "mid_sign": (10, 30)}):

    #     if bar.close_price == 185.42:
    #         print("ok")
    #     # 如果有新的bar,则覆盖
    #     ma_info = self.ma_info.iloc[-1]
    #     ma3_std = ma_info["ma3"]
    #     ma5_std = ma_info["ma5"]
    #     mid_ma = ma_info[20]
    #     if ma3_std <= 0.01:
    #         self.reset_trend_record(ma_info)
    #         return

    #     if self.trend_record.ma_info is None:
    #         return

    #     # 60个bar后取消
    #     l = self.trend_record.data.index.size
    #     if l >= 60:
    #         self.reset_trend_record()
    #         return
    #     else:
    #         self.trend_record.data = self.trend_record.data.append(ma_info)
    #         l += 1

    #     if l < 3:
    #         return
    #     if self.pos == 0:
    #         if ma3_std < 0.1:
    #             return

    #         close = self.trend_record.data["close"]
    #         if l > 10:
    #             y_fit = reg_util.regress_y_polynomial(close, zoom=True)
    #             deg = calc_regress_deg(y_fit[:10], False)
    #         else:
    #             deg = calc_regress_deg(close, False)

    #         if abs(deg) < 0.03:
    #             return

    #         if deg < 0:
    #             # if k < 20 and d < 10 and j < 10:
    #             # if kdj[2] < 10:
    #             self.reset_trend_record()
    #             calc_data["trade_open"] = "开空,deg={}".format(deg)
    #             return self.short(bar.close_price, 1, type=OrderType.MARKET)

    #         else:
    #             # if k > 80 and d > 90 and j > 90:
    #             # if kdj[2] > 90:
    #             self.reset_trend_record()
    #             calc_data["trade_open"] = "开多,deg={}".format(deg)
    #             return self.buy(bar.close_price, 1, type=OrderType.MARKET)
    #     else:
    #         if self.pos < 0:
    #             close = self.am.close[-l:]
    #             start_val = np.min(close)
    #             r = np.where(start_val)
    #             pos = r[0][0]
    #             # ma_list = {}
    #             # for i in self.ma_level[:-2]:
    #             #     if i not in ma_list:
    #             #         ma_list[i] = []

    #             #     ma = self.ma_info[-1][i]
