from datetime import datetime, timedelta
from typing import List

from tigeropen.common.consts import Market, QuoteRight, TimelinePeriod, BarPeriod
from tigeropen.quote.quote_client import QuoteClient
import logging
# from rqdatac import init as rqdata_init
# from rqdatac.services.basic import all_instruments as rqdata_all_instruments
# from rqdatac.services.get_price import get_price as rqdata_get_price
# from rqdatac.share.errors import AuthenticationFailed

from .setting import SETTINGS
from .constant import Exchange, Interval
from .object import BarData, HistoryRequest
import pandas as pd


INTERVAL_VT2RQ = {
    Interval.MINUTE: BarPeriod.ONE_MINUTE,
    Interval.HOUR: BarPeriod.ONE_HOUR,
    Interval.DAILY: BarPeriod.DAY,
}

INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()         # no need to adjust for daily bar
}

from tigeropen.common.consts import Language
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key

rsa_private_key = read_private_key('./money/rsa_private_key.pem')

def get_client_config():
    """
    https://www.itiger.com/openapi/info 开发者信息获取
    :return:
    """
    is_sandbox = False
    client_config = TigerOpenClientConfig(sandbox_debug=is_sandbox)
    client_config.private_key = rsa_private_key
    client_config.tiger_id = '20150137'
    client_config.account = None # 'U9923867'  # 环球账户
    client_config.standard_account = None  # 标准账户
    client_config.paper_account = '20190130122050760'  # 模拟账户
    client_config.language = Language.zh_CN
    return client_config

# class RqdataClient:
#     """
#     Client for querying history data from RQData.
#     """

#     def __init__(self):
#         """"""
#         self.username = SETTINGS["rqdata.username"]
#         self.password = SETTINGS["rqdata.password"]

#         self.inited = False
#         self.symbols = set()

#     def init(self, username="", password=""):
#         """"""
#         if self.inited:
#             return True

#         if username and password:
#             self.username = username
#             self.password = password

#         if not self.username or not self.password:
#             return False

#         rqdata_init(self.username, self.password,
#                     ('rqdatad-pro.ricequant.com', 16011))

#         try:
#             df = rqdata_all_instruments(date=datetime.now())
#             for ix, row in df.iterrows():
#                 self.symbols.add(row['order_book_id'])
#         except (RuntimeError, AuthenticationFailed):
#             return False

#         self.inited = True
#         return True

#     def to_rq_symbol(self, symbol: str, exchange: Exchange):
#         """
#         CZCE product of RQData has symbol like "TA1905" while
#         vt symbol is "TA905.CZCE" so need to add "1" in symbol.
#         """
#         if exchange in [Exchange.SSE, Exchange.SZSE]:
#             if exchange == Exchange.SSE:
#                 rq_symbol = f"{symbol}.XSHG"
#             else:
#                 rq_symbol = f"{symbol}.XSHE"
#         else:
#             if exchange is not Exchange.CZCE:
#                 return symbol.upper()

#             for count, word in enumerate(symbol):
#                 if word.isdigit():
#                     break

#             # Check for index symbol
#             time_str = symbol[count:]
#             if time_str in ["88", "888", "99"]:
#                 return symbol

#             # noinspection PyUnboundLocalVariable
#             product = symbol[:count]
#             year = symbol[count]
#             month = symbol[count + 1:]

#             if year == "9":
#                 year = "1" + year
#             else:
#                 year = "2" + year

#             rq_symbol = f"{product}{year}{month}".upper()

#         return rq_symbol

#     def query_history(self, req: HistoryRequest):
#         """
#         Query history bar data from RQData.
#         """
#         symbol = req.symbol
#         exchange = req.exchange
#         interval = req.interval
#         start = req.start
#         end = req.end

#         rq_symbol = self.to_rq_symbol(symbol, exchange)
#         if rq_symbol not in self.symbols:
#             return None

#         rq_interval = INTERVAL_VT2RQ.get(interval)
#         if not rq_interval:
#             return None

#         # For adjust timestamp from bar close point (RQData) to open point (VN Trader)
#         adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

#         # For querying night trading period data
#         end += timedelta(1)

#         df = rqdata_get_price(
#             rq_symbol,
#             frequency=rq_interval,
#             fields=["open", "high", "low", "close", "volume"],
#             start_date=start,
#             end_date=end,
#             adjust_type="none"
#         )

#         data: List[BarData] = []

#         if df is not None:
#             for ix, row in df.iterrows():
#                 bar = BarData(
#                     symbol=symbol,
#                     exchange=exchange,
#                     interval=interval,
#                     datetime=row.name.to_pydatetime() - adjustment,
#                     open_price=row["open"],
#                     high_price=row["high"],
#                     low_price=row["low"],
#                     close_price=row["close"],
#                     volume=row["volume"],
#                     gateway_name="RQ"
#                 )
#                 data.append(bar)

#         return data



class RqdataClient:
    """
    Client for querying history data from RQData.
    """

    def __init__(self):
        """"""
        logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='a', )
        logger = logging.getLogger('TigerOpenApi')
        client_config = get_client_config()
        self.openapi_client = QuoteClient(client_config, logger=logger)

        self.inited = False
        self.symbols = set()

    def init(self, username="", password=""):
        """"""
        if self.inited:
            return True

        self.__init__()

        self.inited = True
        return True

    def to_rq_symbol(self, symbol: str, exchange: Exchange):
        
        return symbol
    
    def get_data(self, symbol, period=BarPeriod.ONE_MINUTE, limit=1300, begin=-1, end=-1):
        return self.openapi_client.get_bars(symbols=[symbol], period=period, limit=limit, begin_time=begin, end_time=end)

    def query_history(self, req: HistoryRequest):
        """
        Query history bar data from RQData.
        """
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        # rq_symbol = self.to_rq_symbol(symbol, exchange)
        # if rq_symbol not in self.symbols:
        #     return None

        rq_interval = INTERVAL_VT2RQ.get(interval)
        if not rq_interval:
            return None

        # For adjust timestamp from bar close point (RQData) to open point (VN Trader)
        adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

        # For querying night trading period data

        end += adjustment
        final = end.timestamp()
        
        # 获取总时间间隔
        # interval_total = end - start
        # unix_start = start.timestamp() * 1000
        # unix_end = end.timestamp() * 1000
        bars_start = start.timestamp()
        bars_end = bars_start + timedelta(3).total_seconds()
        bars_end = bars_end if bars_end < final else final
        df = None
        while bars_start < final:
            df_data = self.openapi_client.get_bars([symbol], 
                                              period=rq_interval, 
                                              limit=5000, 
                                              begin_time=bars_start * 1000, 
                                              end_time=bars_end * 1000)
            print("query_history:symbol={0},从{1}到{2},一共获取到{3}条数据".format(
                symbol,
                datetime.fromtimestamp(bars_start),
                datetime.fromtimestamp(bars_end),
                df_data.__len__()))
            bars_start = bars_end + adjustment.total_seconds()
            bars_end = bars_end + timedelta(3).total_seconds()
            bars_end = bars_end if bars_end < final else final
            if df_data.empty:
                continue
    
            if df is None:
                df = df_data
            else:
                df = pd.concat([df, df_data])
            print(df)
        
        if df is None:
            return []

        print("query_history:symbol={0},从{1}到{2},一共获取到{3}条数据".format(
            symbol,
            datetime.fromtimestamp(int(df.time.values[0])/1000),
            datetime.fromtimestamp(int(df.time.values[-1])/1000),
            df.__len__()))

        # df = rqdata_get_price(
        #     rq_symbol,
        #     frequency=rq_interval,
        #     fields=["open", "high", "low", "close", "volume"],
        #     start_date=start,
        #     end_date=end,
        #     adjust_type="none"
        # )

        data: List[BarData] = []

        if df is not None:
            for ix, row in df.iterrows():
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    datetime=datetime.fromtimestamp(row.time / 1000),
                    open_price=row["open"],
                    high_price=row["high"],
                    low_price=row["low"],
                    close_price=row["close"],
                    volume=row["volume"],
                    gateway_name="RQ"
                )
                data.append(bar)

        return data

rqdata_client = RqdataClient()
