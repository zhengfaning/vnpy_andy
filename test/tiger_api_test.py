from tigeropen.common.consts import Market, QuoteRight, TimelinePeriod, BarPeriod
from tigeropen.quote.quote_client import QuoteClient
import numpy as np
import pandas as pd
import os
from client_config import get_client_config
import talib
import struct
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='a', )
logger = logging.getLogger('TigerOpenApi')

client_config = get_client_config()
openapi_client = QuoteClient(client_config, logger=logger)


def get_option_quote():
    symbol = 'AAPL'
    expirations = openapi_client.get_option_expirations(symbols=[symbol])
    if len(expirations) > 1:
        print(expirations)
        expiry = int(expirations[expirations['symbol'] == symbol].at[0, 'timestamp'])
        chains = openapi_client.get_option_chain(symbol, expiry)
        print(chains)
    for index,row in chains.iterrows():
        print(row["identifier"], row["strike"], row["put_call"])
    briefs = openapi_client.get_option_briefs(['AAPL  190906C00215000'])
    print(briefs)
    bars = openapi_client.get_option_bars(['AAPL  190906C00215000'])
    print(bars)
    ticks = openapi_client.get_option_trade_ticks(['AAPL  190906C00215000'])
    print(ticks)
    for index,row in ticks.iterrows():
        print(row["identifier"], row["time"], row["price"])


if __name__ == "__main__":
    symbols = ["goog", "baba"]
    info = openapi_client.get_briefs(symbols)
    get_option_quote()
    # print(openapi_client.get_trade_metas(symbols))
    # print(openapi_client.get_short_interest(symbols))
