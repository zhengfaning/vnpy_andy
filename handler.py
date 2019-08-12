
import json
from vnpy.trader.engine import MainEngine
from vnpy.app.cta_backtester.engine import BacktesterEngine
from vnpy.trader.constant import Exchange, Interval
import time, datetime

op_list = {}

def addop(name):
    def add(func):
        op_list[name] = func
        return func
    return add

@addop("init")
def init(args):
    # vnapp.start()
    return "初始化vnpy系统完成"

@addop("contracts")
def contracts(args):
    engine = args["engine"]
    contracts = engine.get_all_contracts()
    result = []
    result.append("<table> ")
    for obj in contracts:
        result.append("<tr> ")
        result.append("<td> ")
        result.append(obj.name)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.symbol)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.vt_symbol)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.gateway_name)
        result.append("</td> ")
        result.append("</tr> ")
    result.append("</table> ")
    return "".join(result)

@addop("download")
def download(args):
    engine : MainEngine = args["engine"]
    # contracts = engine.get_all_contracts()
    cta_backtest : BacktesterEngine = engine.get_engine("CtaBacktester")
    cta_backtest.run_downloading("goog.SMART", Interval.MINUTE, datetime.datetime(2019,7,15,20), datetime.datetime(2019,8,10,5))
    print("ok")
    return "down 成功"

@addop("backtest")
def backtest(args):
    engine : MainEngine = args["engine"]
    # contracts = engine.get_all_contracts()
    cta_backtest : BacktesterEngine = engine.get_engine("CtaBacktester")
    cta_backtest.run_backtesting("DoubleMaStrategy",
                                 "goog.SMART",
                                 Interval.MINUTE,
                                 datetime.datetime(2019,7,15,20),
                                 datetime.datetime(2019,8,10,5),
                                 rate=0.29/10000, # 手续费
                                 slippage=0.2,   # 滑点
                                 size=1,         # 合约乘数
                                 pricetick=0.01, # 价格跳动
                                 capital=100000, # 资金
                                 setting={"fast_window": 10, "slow_window": 30}      # 策略设置
                                 )
    result_df = cta_backtest.get_result_df()
    calculate_statistics = cta_backtest.get_result_statistics()
    print(result_df)
    print(calculate_statistics)
    cta_backtest.backtesting_engine.show_chart(result_df)
    return "ok"


# op_list = { "init": init, "contracts": contracts, "download": download }