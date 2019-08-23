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

class MaLevelTrackStrategy(CtaTemplate):
    author = "用Python的交易员"

    ma_level = [5, 10, 20, 30, 60]
    ma_tag = []
    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters = ["ma_level"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MaLevelTrackStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(200)

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
        
        now = self.am.sma(2, True)[-1]
        l = len(ma_lvl)
        ma_lvl_tag = []
        direction = 1 if now > ma_lvl[0] else 0
        ma_lvl_tag.append(direction)
        for i in range(l-1):
            val = 1 if ma_lvl[i] > ma_lvl[i+1] else 0
            ma_lvl_tag.append(val)
        bincount_val = np.bincount(np.array(ma_lvl_tag))
        tag_val = 0
        if len(bincount_val) == 2:
            tag_val = bincount_val[1]

        if len(self.ma_tag) < 100:
            self.ma_tag.append(tag_val)
        else:
            self.ma_tag[:-1] = self.ma_tag[1:]
            self.ma_tag[-1] = tag_val

        if not am.inited:
            return
        
        # var_val = np.var(np.array(self.ma_tag[-10:]))
        # self.array_sub(self.ma_tag[-3:])
        # if var_val > 1:
        #     direction = int(reduce(lambda x,y:y-x, self.ma_tag[-10:]))
        #     print(var_val)
        #     print(direction)
        #     print(self.ma_tag[-10:])
        #     self.buy(bar.close_price, 1)
        if self.ma_tag[-1] == 3 and self.ma_tag[-2] == 2 and 0 in self.ma_tag[-6:]:
            self.buy(bar.close_price, 1)
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
    def array_sub(data):
        l = len(data)
        result = None

        for v in data[::-1]:
            if result is None:
                result = v
            else:
                result -= v
        return result

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

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
