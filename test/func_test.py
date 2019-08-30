import app as vnpy_app
from time import sleep
import json
import handler
import script_handler
import time, datetime
import vnpy.trader.rqdata as rq
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Exchange, Interval

if __name__ == "__main__":
    req = HistoryRequest(
        symbol="goog",
        exchange=Exchange.SMART,
        interval=Interval.MINUTE,
        start=datetime.datetime(2019,7,1,21,30),
        end=datetime.datetime(2019,8,10,5)
    )
    xx = req.end - req.start

    d = rq.rqdata_client.query_history(req)
    
    
    

    print(xx)


