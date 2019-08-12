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

"""
算法描述:  
    定义15min回调,使用sma算法计算120ma均线,求出后成
立第1步,并存储start_kdj和start_ma,接着是等待kdj突破,
根据120ma均线作出决定,根据设定的间隔计算谷底或者谷顶
以及更新,当方向改变或者kdj相反时平仓
"""

class Kdj120MaStrategy(CtaTemplate):
    author = "用Python的交易员"

    # fast_window = 10
    ma_window = 120
    interval = 15
    start_kdj = None
    start_ma = None
    last_ma = None
    state = None


    parameters = ["ma_window"]
    variables = ["start_kdj", "start_ma", "last_ma", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(Kdj120MaStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar, 15, self.on_5min_bar)
        self.am = ArrayManager(200)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(2)

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

        self.bg.update_bar(bar)


    def on_5min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        ma_window = am.sma(self.ma_window, array=True)
        now = bar.close_price
        ma_price = ma_window[-1]

        if state is None:
            state = 1 if now > ma_price else 0
        else:
            if state == 0:
                if self.pos == 0:
                    self.buy(bar.close_price, 1)
                elif self.pos < 0:
                    self.cover(bar.close_price, 1)
                    self.buy(bar.close_price, 1)
            else:                    
                if self.pos == 0:
                    self.short(bar.close_price, 1)
                elif self.pos > 0:
                    self.sell(bar.close_price, 1)
                    self.short(bar.close_price, 1)
        

        self.put_event()

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
