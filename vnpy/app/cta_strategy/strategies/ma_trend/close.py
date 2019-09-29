from enum import Enum

import numpy as np

from vnpy.app.cta_strategy.strategies.ma_trend_strategy import MaTrendStrategy
from vnpy.trader.constant import OrderType, Direction, Offset
from vnpy.trader.object import TradeData, OrderData, BarData
from vnpy.trader.utility import ArrayManager


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

    def buy(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET, extra: dict = None):
        """
        Send buy order to open a long position.
        """
        return self.strategy.send_order(Direction.LONG, Offset.OPEN, price, volume, lock, type, extra)

    def sell(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET, extra: dict = None):
        """
        Send sell order to close a long position.
        """
        return self.strategy.send_order(Direction.SHORT, Offset.CLOSE, price, volume, lock, type, extra)

    def short(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET, extra: dict = None):
        """
        Send short order to open as short position.
        """
        return self.strategy.send_order(Direction.SHORT, Offset.OPEN, price, volume, lock, type, extra)

    def cover(self, price: float, volume: float, lock: bool = False, type: OrderType = OrderType.MARKET, extra: dict = None):
        """
        Send cover order to close a short position.
        """
        return self.strategy.send_order(Direction.LONG, Offset.CLOSE, price, volume, lock, type, extra)

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
        self.strategy: MaTrendStrategy = strategy
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
        self.strategy: MaTrendStrategy = strategy
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
            self.closeout_price = round(trade.price * scale, 2)
            self.trade_price = trade.price
            self.order_data = np.array([])
        elif trade.direction == Direction.SHORT:
            scale = 1 + self.closeout_offset
            self.closeout_price = round(trade.price * scale, 2)
            self.order_data = np.array([])
            self.trade_price = trade.price