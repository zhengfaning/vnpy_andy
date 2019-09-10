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


@dataclass
class Position:
    volumn: int = 0
    level: int = 0
    close_price: float = 0.0
    price: float = 0
    safe_price: float = 0
    order_data = np.array([])
    # 形态预测出错修正,日后增设级别在3以上才执行
    last_close_info = None
    def __init__(self, strategy):
        self.strategy = strategy
        # self.am = self.strategy.am
        self.ma_tag = self.strategy.ma_tag
        self.close_process = [self.close1, self.close2]

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
                return self.strategy.cover(self.close_price, 1, type=OrderType.MARKET,
                       extra= { "reason":"平仓:到达最低价{}".format(self.close_price)})
                 
        elif self.volumn > 0:
            if bar.close_price < self.close_price:
                return self.strategy.sell(self.close_price, 1, type=OrderType.MARKET,
                       extra={"reason": "平仓:到达最低价{}".format(self.close_price)})

    
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
                        return self.strategy.sell(bar.close_price, 1, type=OrderType.MARKET, 
                                extra={"reason":"平仓:趋势趋弱,deg={}".format(deg_full)})


            elif self.volumn < 0:
                if deg_full > 0.01:
                    # if abs(deg_order_short) < abs(deg_full):
                        return self.strategy.cover(bar.close_price, 1, type=OrderType.MARKET, 
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
        if order.status == Status.ALLTRADED or order.status == Status.PARTTRADED:
            # pre_volumn = 0
            if order.direction == Direction.LONG:
                if self.volumn == 0:
                    self.close_price = round(order.price * 0.998, 2)
                    self.safe_price = order.price * 1.005
                    self.price = order.price
                    self.order_data = np.array([])
                    self.level = 0
                self.volumn += order.volume
                
            elif order.direction == Direction.SHORT:
                if self.volumn == 0:
                    self.close_price = round(order.price * 1.002, 2)
                    self.order_data = np.array([])
                    self.price = order.price
                    self.safe_price = order.price * 0.995
                    self.level = 0
                self.volumn -= order.volume

            elif order.direction == Direction.NET:
                self.volumn = order.volume
@dataclass            
class Score:
    base = 0.0
    time = None
    track = {}
    pattern = {}

''' 
    TODO: 加入每日时间识别
    TODO: 加入红绿十字星识别
    TODO: 加入十字星后,快速趋势判断购买
    TODO: 加入高吊线和低线识别
    TODO: 策略架构改进,多个策略并存
'''
class PatternScoreStrategy(CtaTemplate):
    author = "用Python的交易员"

    ma_level = [10, 20, 30, 60, 120]
    ma_tag = []
    bd = []
    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0
    request_order = []
    bar_identify = []

    score = Score()
    count = 0
    interval = 6
    
    
    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(PatternScoreStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar)
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
        
        self.open_strategy = [self.open_kline1]
        self.offset = 40
        self.min = 0
        self.max = 0
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
            # deg = calc_regress_deg(self.am3.close[-20:])
    
    def calc_score(self):
        score = 0
        score += self.score.base

        for item in self.pattern_record.values():
            score += item["value"]

        return score

    def on_5min_bar(self, bar: BarData):
        
        self.std_range5.update(self.am5.range[-1])
        self.am5.update_bar(bar)
        if not self.am.inited or not self.trading:
            return
        diff_time = bar.datetime - self.am.time_array[-1]
        if diff_time.total_seconds() > 3600 or self.count > self.interval:
            self.count = 0
            self.score.base = calc_regress_deg(self.am.close[-self.interval:], False) * 1000
            print("score:", self.score.base, self.min, self.max)
        else:
            self.count += 1

        # pattern_list = [KlinePattern.CDLEVENINGSTAR, KlinePattern.CDL2CROWS, KlinePattern.CDLCONCEALBABYSWALL, KlinePattern.CDLEVENINGDOJISTAR]
        pattern = self.am5.pattern(list(KlinePattern))
        if len(pattern) > 0:
            print(list(map(lambda x: (KLINE_PATTERN_CHINESE[x[0]],x[1]), pattern)))
            self.pattern_record.add_pattern(pattern)
            deg_full = calc_regress_deg(self.am.close[-40 :], False)
            print("deg:",deg_full)
        
        self.pattern_record.update()


    

    def open_kline1(self, bar:BarData, calc_data):

        score = self.calc_score()
        if score < self.min:
            self.min = score
        if score > self.max:
            self.max = score
        
        if abs(calc_data["range_sum"]) < 0.001 or abs(score) < 300:
            return

        # if std_val2 < 0.2: 
        if score > 0 and calc_data["range_sum"] > 0:
            return self.buy(bar.close_price, 1, type=OrderType.MARKET,
                            extra={"reason": "开多,score={}, rang_sum={}".format(score, calc_data["range_sum"])})
        if score < 0 and calc_data["range_sum"] < 0:
            return self.short(bar.close_price, 1, type=OrderType.MARKET,
                              extra={"reason":"开多,score={}, rang_sum={}".format(score, calc_data["range_sum"])})


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
        
        calc_data = (dict(
                kdj=[round(kdj_val["k"][-1],2),round(kdj_val["d"][-1],2),round(kdj_val["j"][-1],2)],
                deg40_20=round(deg1,2), deg20=round(deg2,2), deg10=round(deg3,2),deg_f=round(deg_full,2),
                time=bar.datetime, price=bar.close_price, ma=round(ma, 2), 
                std_40=round(std_val, 2),mean40=round(mean_val,2), 
                std_10=round(std_val2,2), mean30_10=round(mean_val4,2), mean10=round(mean_val2,2),
                vol=self.am.volume[-1], std_range=self.std_range.data[-1:-5:-1], range=self.am.range[-1:-5:-1].tolist(),
                range_sum=np.sum(self.am.range[-5:]), atr=self.am.atr(10), tr=self.am.atr(1, length=2),
                pattern=list(map(lambda x: KLINE_PATTERN_CHINESE[x], self.pattern_record.keys()))))

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
                        self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, calc_data["deg40_20"], calc_data["deg20"]))
            self.request_order.extend(order_id)
        
        if self.tracker is not None:
            self.tracker["ma_tag_ls"].append(calc_data)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg3.update_bar(bar)
        self.bg5.update_bar(bar)
        am = self.am
        self.am.update_bar(bar)
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

                

        if not self.am.inited or not self.trading:
            return
        
        
        
        self.on_strategy(bar)
            # median_val = np.median(calc_nums)
        
        self.put_event()

    # def init_order_data(self):
    #     self.order_data = np.array([])
        

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        print("{}产生了{},价格为{},交易{},".format(order.datetime.strftime("%m/%d %H:%M:%S"), order.offset.value + order.direction.value,order.price,order.status.value))
        
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
