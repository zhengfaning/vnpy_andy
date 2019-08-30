
import json
from vnpy.trader.constant import Exchange, Interval


script_list = {}

def add_script(name):
    def add(func):
        script_list[name] = func
        return func
    return add

@add_script("get_contract")
def get_contract(args):
    # vnapp.start()
    engine = args["engine"]
    symbol = args["symbol"]
    data = engine.get_contract(symbol)
    d = {}
    d.update(data.__dict__)
    # d["exchange"] = d["exchange"].value
    # d["product"] = d["product"].value
    print(d)

    return str(d).encode("UTF-8")

@add_script("get_bars")
def get_bars(args):
    # vnapp.start()
    engine = args["engine"]
    symbol = args["symbol"]
    data = engine.get_bars(vt_symbol=symbol, start_date="20190718", interval=Interval.DAILY)
    return str(data)

    