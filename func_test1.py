import app as vnpy_app
from time import sleep
import json
import handler
import script_handler
import time, datetime
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Exchange, Interval
from kdj import calc_kdj
import pandas as pd
import matplotlib.pyplot as plt
# from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.app.cta_strategy import (
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)

class TestBar(object):
    def __init__(self):
        self.am = ArrayManager(200)
        self.bg = BarGenerator(self.on_bar, interval=Interval.DAILY)

    def on_bar(self, bar: BarData):
        # self.am.update_bar(bar)
        self.am.update_bar(bar)


if __name__ == "__main__":
    req = HistoryRequest(
        symbol="goog",
        exchange=Exchange.SMART,
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,8,9,9),
        end=datetime.datetime(2019,8,10,4)
    )
    df_data = rq.rqdata_client.get_data("goog", begin="2019-08-09 09:00:00", end="2019-08-10 04:00:00")
    df = df_data[-200:]
    bar_data = rq.rqdata_client.query_history(req)

    tb = TestBar()
    for v in bar_data:
        tb.am.update_bar(v)

    data = df
    print(data["close"])
    print(tb.am.close_array)
    # data = df.to_dict('records')
    xxx = tb.am.kdj()


    bbb=calc_kdj(data)
    df['rsv']=bbb['rsv']
    df['max']=bbb['max']
    df['min']=bbb['min']
    df['k']=bbb['k']
    df['d']=bbb['d']
    df['j']=bbb['j']


    print(df)

    dm=df[['k','d','j']]
    dm2=pd.DataFrame(xxx)
    print(dm)
    print(dm2)
    dm2.plot(figsize=(20,10))
    plt.show()
    print("bye bye")

