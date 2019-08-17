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
    ma_window = 60
    wave_window = 0.0005
    bar_min = 5
    interval = 0
    # start_kdj = None
    # start_ma = None
    # last_ma = None
    bull = None
    base_wave = None

    report = {"gain":0, "bull_count":0, "bear_count": 0, "king_count":0, "die_count":0, "kdj_list":[]}
    price = 0


    parameters = ["ma_window", "wave_window", "bar_min"]
    variables = ["bull", "base_wave"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(Kdj120MaStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar, self.bar_min, self.on_x_min_bar)
        self.am = ArrayManager(400)

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


    def on_x_min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        
        # 现在的价格
        now = bar.close_price

        w,_ = self.am.wave()
        
        w = w[::-1]
        # 持仓的情况下,检查是否低于或者高于第1波浪,根据情况进行平仓
        # if self.pos != 0:
        #     print("收盘价", bar.close_price)

        if self.pos > 0:
            new_wave = bar.close_price - self.interval
            if now < self.base_wave:
                self.cover(bar.close_price, 1)
                # self.pos = 0
                gain = bar.close_price - self.price
                self.report["gain"] += gain
                print("平多仓,价格为{},盈利{}".format(bar.close_price, gain))
            elif self.base_wave < new_wave:
                if abs(self.base_wave - new_wave) > self.interval:
                    self.base_wave = new_wave
                    print("平仓价更新=", new_wave)
            # self.cover(bar.close_price, 1)
            # print("平仓", bar.close_price)
        elif self.pos < 0:
            new_wave = bar.close_price + self.interval
            if now > self.base_wave:
                self.sell(bar.close_price, 1)
                # self.cover(bar.close_price, 1)
                # self.pos = 0
                gain = -(bar.close_price - self.price)
                self.report["gain"] += gain
                print("平卖空仓,价格为{},盈利{}".format(bar.close_price, gain))
            elif self.base_wave > new_wave:
                if (self.base_wave - new_wave) > self.interval:
                    self.base_wave = new_wave
                    print("平仓价更新=", new_wave)
                    # print("更新wave, 新wave=", new_wave)
            

        ma_window = am.sma(self.ma_window, array=True)
        
        # 现在的均线
        ma_price = ma_window[-1]

        # 计算均线,并保存
        self.bull = 1 if now > ma_price else 0
        
        kdj = self.am.kdj(5,3,3)

        k = kdj["k"][-1]
        d = kdj["d"][-1]
        j = kdj["j"][-1]
        # self.report["kdj_list"].append([k,d,j])
        # 均线之上,配合金叉进行
        if self.bull == 1:
            self.report["bull_count"] += 1
            # 金叉出现,且j值大于100时
            
            if k < 45 and k > d:
                self.report["king_count"] += 1
                if now  > w[0] and \
                   w[0] < w[1] and \
                   w[0] > w[2] and \
                   w[1] > w[2]:
                   
                    if self.pos == 0:
                        self.interval = abs((w[0] - w[2]) * 10)
                        self.buy(bar.close_price, 1)
                        # self.pos += 1
                        self.base_wave = w[0]
                        self.price = bar.close_price
                        print("进行买多,price={},平仓价={}".format(bar.close_price, self.base_wave))
                    elif self.pos < 0:
                        self.interval = abs((w[0] - w[2]) * 10)
                        # self.pos += 1
                        gain = bar.close_price - self.price
                        self.report["gain"] += gain
                        self.cover(bar.close_price, 1)
                        self.buy(bar.close_price, 1)
                        self.base_wave = w[0]
                        self.price = bar.close_price
                        print("平仓后买多,price={},平仓价={},盈利为{}".format(bar.close_price, self.base_wave, gain))
                        
                    
        # 均线之下
        else:
            # 死叉出现,且j值小于10时
            self.report["bear_count"] += 1
            if k >= 55 and k < d:
                self.report["die_count"] += 1
                if now  < w[0] and \
                   w[0] > w[1] and \
                   w[0] < w[2] and \
                   w[1] < w[2]:
                    if self.pos == 0:
                        self.interval = abs((w[0] - w[2]) * 10)
                        self.short(bar.close_price, 1)
                        # self.pos -= 1
                        self.base_wave = w[0]
                        self.price = bar.close_price
                        print("进行卖空,price={},平仓价={}".format(bar.close_price, self.base_wave))
                    elif self.pos > 0:
                        self.interval = abs((w[0] - w[2]) * 10)
                        self.sell(bar.close_price, 1)
                        self.short(bar.close_price, 1)
                        # self.pos -= 1
                        self.base_wave = w[0]
                        gain = -(bar.close_price - self.price)
                        self.report["gain"] += gain
                        self.price = bar.close_price
                        print("平仓后卖空,price={},平仓价={},盈利为{}".format(bar.close_price, self.base_wave, gain))
                    
                        
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
