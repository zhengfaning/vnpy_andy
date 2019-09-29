import math
from enum import Enum

from vnpy.trader.constant import OrderType, Offset, Direction, Status
from vnpy.trader.object import BarData, TradeData, OrderData



class PositionStatus(Enum):
    Empty = 0
    Long = 1
    Short = 2


class TradeMgr:
    ma_info = None
    trade_data = {}  #买入信息 记录买入点的信息和价格还有类型

    submit = []
    price = 0  #现有价格
    vol = 0
    current = None
    def __init__(self, strategy, capital, default_order_type, setting, on_trade_complete = None, on_empty = None):
        self.strategy = strategy
        self.capital = capital
        self.default_order_type = default_order_type
        self.on_trade_complete = on_trade_complete
        self.on_empty = on_empty
        self._init_distribute(20)

    def _init_distribute(self, length):
        self.distribute = []
        capital = self.capital / length
        self.pos_size = capital
        for i in range(length):
            self.distribute.append(capital)

    def alloc_capital(self, size):

        x = size
        alloc = 0
        for i in range(len(self.distribute)):
            item = self.distribute[i]
            if item == 0:
                continue
            r = item - x
            if r >= 0:
                self.distribute[i] = r
                alloc += x
                break
            else:
                self.distribute[i] = 0
                x = abs(r)
                alloc += item

        return alloc

    def remain_capital(self):
        return sum(self.distribute)

    def used_capital(self):
        return self.capital - sum(self.distribute)


    def add_capital(self, capital):


        x = capital
        for i in range(len(self.distribute), 0, -1):
            index = i -1
            item = self.distribute[index]
            if item == self.pos_size:
                continue
            r = item + x
            if r > self.pos_size:
                self.distribute[index] = self.pos_size
                x = r - self.pos_size
            else:
                self.distribute[index] = r
                break

        if x < capital:
            self.capital += x
            self.distribute.append(x)

    def set_default_order_type(self, order_type):
        self.default_order_type = order_type

    def get_request(self):
        return self.submit

    def on_bar(self, bar:BarData):
        self.bar = bar

    #获取持仓盈亏
    def get_profit(self):
        return self.bar.close_price / self.price - 1

    def get_status(self):
        if self.vol == 0:
            return PositionStatus.Empty
        if self.vol > 0:
            return PositionStatus.Long
        if self.vol < 0:
            return PositionStatus.Short

    def get_volumn(self):
        return abs(self.vol)

    def calc_cost(self, price, init_capital):


        capital = self.alloc_capital(init_capital)
        vol = int(capital / price)
        if vol == 0:
            # 归还资金
            self.add_capital(capital)
            return 0,0

        commission = self.calc_commission(price, vol)
        item_cost = vol * price
        cost = item_cost + commission
        if cost > capital:
            diff = cost - capital
            n = math.ceil(diff / price)
            vol -= n
            commission = self.calc_commission(price, vol)
            cost = cost + commission

        if vol == 0:
            self.add_capital(capital)
            return 0, 0

        return cost, vol


    def calc_commission(self, price, vol):
        commission_base = price * vol * 0.0000207
        min_commission = 2.99
        commission = (0.0039 + 0.00396 + 0.004)* vol
        if commission < min_commission:
            commission = min_commission

        return commission + commission_base


    def add_new_trade(self, order_id, trade_info):
        self.submit.append(order_id)
        self.trade_data[order_id] = trade_info

    def buy(self, price: float, ratio, order_info = {}, lock: bool = False, order_type: OrderType = None):
        if order_type is None:
            order_type = self.default_order_type
        init_capital = self.capital * ratio
        capital,vol = self.calc_cost(price, init_capital)
        order_info = {"req_vol": vol, "capital":capital, "vol":0}
        order_id = self.strategy.buy(price, vol, lock, order_type)
        self.add_new_trade(order_id[0], order_info)

        return order_id

    def short(self, price: float, ratio, order_info = {}, lock: bool = False, order_type: OrderType = None):
        if order_type is None:
            order_type = self.default_order_type

        init_capital = self.capital * ratio
        capital,vol = self.calc_cost(price, init_capital)
        order_info = {"req_vol": vol, "capital":capital, "vol":0}
        order_id = self.strategy.short(price, vol, lock, order_type)
        self.add_new_trade(order_id[0], order_info)


        return order_id

    def overweight(self, price, new_ratio, order_type: OrderType = None):


        if self.get_volumn() == 0:
            return

        old_ratio = self.used_capital() / self.capital
        if old_ratio >= new_ratio:
            return

        if order_type is None:
            order_type = self.default_order_type

        ratio = new_ratio - old_ratio

        init_capital = self.capital * ratio
        capital, vol = self.calc_cost(price, init_capital)

        if vol == 0:
            return

        order_info = {"req_vol": vol, "capital": capital, "vol": 0}
        if self.get_volumn() > 0:
            order_id = self.strategy.sell(price, vol, False, order_type)
        else:
            order_id = self.strategy.cover(price, vol, False, order_type)
        self.add_new_trade(order_id[0], order_info)

        return order_id



    def sell(self, price: float, ratio = 1, order_info = {}, order_type: OrderType = None):
        if order_type is None:
            order_type = self.default_order_type
        vol = int(ratio * self.get_volumn())
        order_info = {"req_vol": vol, "capital": vol * price, "vol": 0}
        order_id = self.strategy.sell(price, vol, False, order_type)
        self.add_new_trade(order_id[0], order_info)

        return order_id

    def cover(self, price: float, ratio = 1, order_info = {}, order_type: OrderType = None):
        if order_type is None:
            order_type = self.default_order_type
        vol = int(ratio * self.get_volumn())
        order_info = {"req_vol": vol, "capital": vol * price, "vol": 0}
        order_id = self.strategy.cover(price, vol, False, order_type)
        self.add_new_trade(order_id[0], order_info)

        return order_id



    def on_trade(self, trade: TradeData):
        if trade.vt_orderid in self.submit:
            # self.positions.on_trade(trade)
            trade_data = self.trade_data[trade.vt_orderid]
            trade_data["vol"] += trade.volume

            self.price = trade.price
            if trade.offset == Offset.OPEN:
                capital = trade.price * trade.volume + self.calc_commission(trade.price, trade.volume)
                trade_data["capital"] -= capital
            elif trade.offset == Offset.CLOSE:
                capital = trade.price * trade.volume - self.calc_commission(trade.price, trade.volume)
                self.add_capital(capital)
            if trade.direction == Direction.LONG:
                self.vol += trade.volume
            elif trade.direction == Direction.SHORT:
                self.vol -= trade.volume
            if trade_data["req_vol"] == trade_data["vol"]:
                self.submit.remove(trade.vt_tradeid)
                if self.on_trade_complete is not None:
                    self.on_trade_complete(trade.vt_orderid)
                if self.get_status() == PositionStatus.Empty and self.on_empty is not None:
                    self.on_empty()
                self.last = trade.vt_tradeid
            else:
                self.current = trade.vt_tradeid


    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        if order.vt_orderid in self.submit:
            if order.status == Status.CANCELLED or order.status == Status.REJECTED:
                #归还资金
                trade_data = self.trade_data[order.vt_orderid]
                self.add_capital(trade_data["capital"])