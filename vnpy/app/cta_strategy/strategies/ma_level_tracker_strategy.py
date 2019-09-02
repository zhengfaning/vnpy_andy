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
from vnpy.trader.constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType
from dataclasses import dataclass, field
from  enum import Enum


class ClosePosType(Enum):
    SAFE_PRICE = 1
    TREND_CHANGE = 2


@dataclass
class Poisition:
    volumn: int = 0
    level: int = 0
    close_price: float = 0.0
    price: float = 0
    safe_price: float = 0
    order_data = np.array([])
    # 形态预测出错修正
    last_close_info = None
    def __init__(self, strategy):
        self.strategy:MaLevelTrackStrategy  = strategy
        # self.am = self.strategy.am
        self.ma_tag = self.strategy.ma_tag

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

    def on_bar(self, bar:BarData):
        if self.volumn == 0:
            return
        
        self.order_data = np.append(self.order_data, bar.close_price)

        if self.volumn < 0:
            if bar.close_price > self.close_price:
                order_id = self.strategy.cover(self.close_price, 1, type=OrderType.MARKET)
                return order_id
        elif self.volumn > 0:
            if bar.close_price < self.close_price:
                order_id = self.strategy.sell(self.close_price, 1, type=OrderType.MARKET)
                return order_id
        
        order_id = None
        offset = -40
        offset_m = int(offset / 2)
        
        # self.price
        if self.level == 0:
            if self.volumn > 0 and bar.close_price > self.safe_price:
                self.level += 1
            elif self.volumn < 0 and bar.close_price < self.safe_price:
                self.level += 1

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

        if self.level >= 2:
            if len(self.order_data) > abs(offset * 1.5):
                deg_full = calc_regress_deg(self.strategy.am.close[offset :], False)
                y_fit = reg_util.regress_y_polynomial(self.order_data, zoom=True)
                deg_order_short = calc_regress_deg(y_fit[:abs(offset)], False)

                if self.volumn > 0:
                    if deg_full < -0.05 and std_val < 1:
                        if abs(deg_order_short) < abs(deg_full):
                            order_id = self.strategy.sell(bar.close_price, 1, type=OrderType.MARKET)
                elif self.volumn < 0:
                    if deg_full > 0.05 and std_val < 1:
                        if abs(deg_order_short) < abs(deg_full):
                            order_id = self.strategy.cover(bar.close_price, 1, type=OrderType.MARKET)

            print("pos<0", deg_order_short, deg_full)
        
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
                    self.close_price = round(order.price * 0.995, 2)
                    self.safe_price = order.price * 1.005
                    self.price = order.price
                    self.order_data = np.array([])
                    self.level = 0
                self.volumn += order.volume
                
            elif order.direction == Direction.SHORT:
                if self.volumn == 0:
                    self.close_price = round(order.price * 1.005, 2)
                    self.order_data = np.array([])
                    self.price = order.price
                    self.safe_price = order.price * 0.995
                    self.level = 0
                self.volumn -= order.volume

            elif order.direction == Direction.NET:
                self.volumn = order.volume
            
            
                

class MaLevelTrackStrategy(CtaTemplate):
    author = "用Python的交易员"

    ma_level = [10, 20, 30, 60, 120]
    ma_tag = []
    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0
    request_order = []
    
    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MaLevelTrackStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(200)
        self.order_data = None
        self.positions = Poisition(self)


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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        am = self.am
        am.update_bar(bar)
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

        if not am.inited or not self.trading:
            return
        
        

        # var_val = np.var(np.array(self.ma_tag[-10:]))
        # self.array_sub(self.ma_tag[-3:])
        # if var_val > 1:
        #     direction = int(reduce(lambda x,y:y-x, self.ma_tag[-10:]))
        #     print(var_val)
        #     print(direction)
        #     print(self.ma_tag[-10:])
        #     self.buy(bar.close_price, 1)
        # calc_nums = np.array(self.ma_tag[-45:-15])
        # if self.pos > 0 and  self.positions.volumn < 0:
        #     if bar.close_price < self.positions.close_price:
        #         order_id = self.cover(self.positions.close_price, 1)
        #         return
        # elif self.pos < 0 and  self.positions.volumn < 0:
        #     if bar.close_price < self.positions.close_price:
        #         order_id = self.short(self.positions.close_price, 1)
        #         return

        offset = -40
        offset_m = int(offset / 2)
        calc_nums = np.array(self.ma_tag[-offset:-1])
        # var_val = np.var(calc_nums)
        std_val = np.std(calc_nums)
        mean_val = np.mean(calc_nums)
        # median_val = np.median(calc_nums)
        order_id = None
        if self.tracker is not None:
            deg1 = calc_regress_deg(self.am.close[offset : offset_m], False)
            deg2 = calc_regress_deg(self.am.close[offset_m :], False)
            deg_full = calc_regress_deg(self.am.close[offset :], False)
            self.tracker["ma_tag_ls"].append((bar.datetime, bar.close_price, tag_val, std_val, mean_val, deg1, deg2, deg_full))
        if self.pos == 0:
            if std_val < 1 and mean_val < 2 and self.ma_tag[-1] >= (mean_val + 2):
                is_order = True
                self.tracker["trade_info"].append((
                    self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, deg1, deg2))
                order_id = self.buy(bar.close_price, 1, type=OrderType.MARKET)
            elif std_val < 1 and mean_val > 3 and self.ma_tag[-1] <= (mean_val - 2):
                is_order = True
                self.tracker["trade_info"].append((
                    self.am.time_array[offset], self.am.time_array[offset_m], bar.datetime, deg1, deg2))
                order_id = self.short(bar.close_price, 1, type=OrderType.MARKET)
        else:
            order_id = self.positions.on_bar(bar)
            # if order_id is not None:
            #     self.init_order_data()
                # self.order_data = np.append(self.order_data, bar.close_price)
        # elif self.pos > 0 and self.positions.volumn > 0:
        #     self.order_data = np.append(self.order_data, bar.close_price)
        #     if deg_full < -0.05 and std_val < 1:
        #         y_fit = reg_util.regress_y_polynomial(self.order_data, zoom=True)
        #         deg_order_short = calc_regress_deg(y_fit[:abs(offset)], False)
        #         deg_order = calc_regress_deg(self.order_data, False)
        #         deg_order2 = calc_regress_deg(self.order_data[int(len(self.order_data) / 2):], False)
        #         print("pos>0",deg_order, deg_order2,deg_order_short, deg_full, std_val)
        #         if abs(deg_order_short) < abs(deg_full):
        #             order_id = self.sell(bar.close_price, 1)
        #             self.order_data = None
        # elif self.pos < 0 and  self.positions.volumn < 0:

        #     self.order_data = np.append(self.order_data, bar.close_price)
        #     if self.positions.level == 0:
        #         self.positions.level += 1

        #     if deg_full > 0.05 and std_val < 1:
        #         y_fit = reg_util.regress_y_polynomial(self.order_data, zoom=True)
        #         deg_order_short = calc_regress_deg(y_fit[:abs(offset)], False)
        #         deg_order = calc_regress_deg(self.order_data, False)
        #         deg_order2 = calc_regress_deg(self.order_data[int(len(self.order_data) / 2):], False)
        #         print("pos<0",deg_order, deg_order2,deg_order_short, deg_full, std_val)
        #         # print(deg)
        #         if abs(deg_order_short) < abs(deg_full):
        #             order_id = self.cover(bar.close_price, 1) 
        #             self.order_data = None
            
        if order_id is not None:
            self.request_order.extend(order_id)
        #     if self.ma_tag[-1] == 3 and self.ma_tag[-1] == 4 and 5 in self.ma_tag[-5:]:
        #         self.sell(bar.close_price, 1)
        #     direction = int(reduce(lambda x,y:y-x, self.ma_tag[-10:]))
        #     print(var_val)
        #     print(direction)
        #     print(self.ma_tag[-10:])
        #     self.buy(bar.close_price, 1)

        

        self.tracker["ma_tag"].append(self.ma_tag[-10:])
        self.tracker["var"].append(np.var(np.array(self.ma_tag[-10:])))
        self.tracker["var1"].append(np.var(np.array(self.ma_tag[-5:])))
        self.tracker["var2"].append(np.var(np.array(self.ma_tag[-3:])))
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
