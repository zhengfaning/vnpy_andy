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


if __name__ == "__main__":
    symbols = ["goog", "baba"]
    info = openapi_client.get_briefs(symbols)
    print(openapi_client.get_trade_metas(symbols))
    print(openapi_client.get_short_interest(symbols))
