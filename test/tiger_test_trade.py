from tigeropen.common.consts import Language
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key
from tigeropen.trade.trade_client import TradeClient
from client_config import get_client_config
from tigeropen.common.consts import SecurityType
import time
from tigeropen.common.util.contract_utils import stock_contract, option_contract, future_contract
from tigeropen.common.util.order_utils import (market_order,        # 市价单
                                               limit_order,         # 限价单
                                               stop_order,          # 止损单
                                               stop_limit_order,    # 限价止损单
                                               trail_order)
from tigeropen.quote.quote_client import QuoteClient
import logging
from tigeropen.push.push_client import PushClient, QuoteKeyType
import time

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='a', )
logger = logging.getLogger('TigerOpenApi')





class Test:
    def __init__(self):
        self.client_config = get_client_config()
        self.trade_client = TradeClient(self.client_config)
        self.openapi_client = QuoteClient(self.client_config, logger=logger)
        # 初始化 pushclient

        protocol, host, port = self.client_config.socket_host_port
        self.push_client = PushClient(host, port, use_ssl=(protocol == 'ssl'))
        self.push_client.connect(self.client_config.tiger_id, self.client_config.private_key)



    def trade(self):
        stock = stock_contract(symbol='AAPL', currency='USD')
        option = option_contract(identifier='AAPL  190927P00200000')

        emu_account = []
        # stock_contract = trade_client.get_contracts(symbol='FB')[0]

        account = self.trade_client.get_managed_accounts()
        print(account)
        emu_account = account[1]
        account = self.client_config.paper_account
        assets = self.trade_client.get_assets(account=account)
        print(assets)
        posinfo = self.trade_client.get_positions(account=account)
        print(posinfo)
        stock_order = market_order(account=account,   # 下单账户，可以使用标准、环球、或模拟账户
                                  contract = option,       # 第1步中获取的合约对象
                                  action = 'BUY',
                                  quantity = 1)
        print(stock_order)
        self.trade_client.place_order(stock_order)
        print(stock_order)

# 直接本地构造contract对象。 期货 contract 的构造方法请参考后面的文档
    def get_option_quote(self):
        symbol = 'AAPL'
        expirations = self.openapi_client.get_option_expirations(symbols=[symbol])
        if len(expirations) > 1:
            print(expirations)
            expiry = int(expirations[expirations['symbol'] == symbol].at[0, 'timestamp'])
            chains = self.openapi_client.get_option_chain(symbol, expiry)
            print(chains)
        for index,row in chains.iterrows():
            print(row["identifier"], row["strike"], row["put_call"])
        briefs = self.openapi_client.get_option_briefs(['AAPL  190927P00200000'])
        print(briefs)
        bars = self.openapi_client.get_option_bars(['AAPL  190927P00200000'])
        print(bars)
        ticks = self.openapi_client.get_option_trade_ticks(['AAPL  190927P00200000'])
        print(ticks)
        for index,row in ticks.iterrows():
            print(row["identifier"], row["time"], row["price"])

    def on_quote_changed(self, symbol, items, hour_trading):
        print(symbol, items, hour_trading)


    def test1(self):
        info = app.openapi_client.get_briefs(symbols)
        print(info)

    def run(self):
        option_trade_ticks = self.openapi_client.get_option_trade_ticks(['AAPL  190927P00200000'])
        print(option_trade_ticks)

    def subscribe(self):
        # self.push_client.connect(self.client_config.tiger_id, self.client_config.private_key)
        self.push_client.quote_changed = self.on_quote_changed
        self.push_client.subscribe_quote(symbols=['AAPL  190927P00200000', 'GOOG', 'FB'], quote_key_type=QuoteKeyType.ALL)
        self.push_client.subscribe_asset()
        time.sleep(30)
        # self.push_client.unsubscribe_quote(['AAPL', 'GOOG'])

    def subscribe2(self):

        self.push_client.quote_changed = self.on_quote_changed
        self.push_client.subscribe_quote(symbols=['aapl'], quote_key_type=QuoteKeyType.ALL)
        self.push_client.subscribe_asset()

    def on_changed(self, symbol, items, hour_trading):
        print(symbol, items, hour_trading)
        data = dict(items)
        latest_price = data.get('latest_price')
        volume = data.get('volume')


    def query_subscribed(self):
        def on_subscribed_symbols(symbols, focus_keys, limit, used):
            print(symbols, focus_keys, limit, used)

        self.push_client.subscribed_symbols = on_subscribed_symbols
        self.push_client.query_subscribed_quote()

def on_changed(self, symbol, items, hour_trading):
    print(symbol, items, hour_trading)
    data = dict(items)
    latest_price = data.get('latest_price')
    volume = data.get('volume')

if __name__ == "__main__":
    symbols = ["goog", "baba"]
    app = Test()
    # app.get_option_quote()
    # app.trade()
    app.query_subscribed()
    app.subscribe()
    time.sleep(120)
    print("over")