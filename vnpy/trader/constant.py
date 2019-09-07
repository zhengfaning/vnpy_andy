"""
General constant string used in VN Trader.
"""

from enum import Enum


class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = "多"
    SHORT = "空"
    NET = "净"


class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"


class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"


class Product(Enum):
    """
    Product class.
    """
    EQUITY = "股票"
    FUTURES = "期货"
    OPTION = "期权"
    INDEX = "指数"
    FOREX = "外汇"
    SPOT = "现货"
    ETF = "ETF"
    BOND = "债券"
    WARRANT = "权证"
    SPREAD = "价差"
    FUND = "基金"


class OrderType(Enum):
    """
    Order type.
    """
    LIMIT = "限价"
    MARKET = "市价"
    STOP = "STOP"
    FAK = "FAK"
    FOK = "FOK"


class OptionType(Enum):
    """
    Option type.
    """
    CALL = "看涨期权"
    PUT = "看跌期权"


class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    CFFEX = "CFFEX"         # China Financial Futures Exchange
    SHFE = "SHFE"           # Shanghai Futures Exchange
    CZCE = "CZCE"           # Zhengzhou Commodity Exchange
    DCE = "DCE"             # Dalian Commodity Exchange
    INE = "INE"             # Shanghai International Energy Exchange
    SSE = "SSE"             # Shanghai Stock Exchange
    SZSE = "SZSE"           # Shenzhen Stock Exchange
    SGE = "SGE"             # Shanghai Gold Exchange
    WXE = "WXE"             # Wuxi Steel Exchange

    # Global
    SMART = "SMART"         # Smart Router for US stocks
    NYMEX = "NYMEX"         # New York Mercantile Exchange
    COMEX = "COMEX"         # a division of theNew York Mercantile Exchange
    GLOBEX = "GLOBEX"       # Globex of CME
    IDEALPRO = "IDEALPRO"   # Forex ECN of Interactive Brokers
    CME = "CME"             # Chicago Mercantile Exchange
    ICE = "ICE"             # Intercontinental Exchange
    SEHK = "SEHK"           # Stock Exchange of Hong Kong
    HKFE = "HKFE"           # Hong Kong Futures Exchange
    SGX = "SGX"             # Singapore Global Exchange
    CBOT = "CBT"            # Chicago Board of Trade
    DME = "DME"             # Dubai Mercantile Exchange
    EUREX = "EUX"           # Eurex Exchange
    APEX = "APEX"           # Asia Pacific Exchange
    LME = "LME"             # London Metal Exchange
    BMD = "BMD"             # Bursa Malaysia Derivatives
    TOCOM = "TOCOM"         # Tokyo Commodity Exchange
    EUNX = "EUNX"           # Euronext Exchange
    KRX = "KRX"             # Korean Exchange

    # CryptoCurrency
    BITMEX = "BITMEX"
    OKEX = "OKEX"
    HUOBI = "HUOBI"
    BITFINEX = "BITFINEX"
    BINANCE = "BINANCE"


class Currency(Enum):
    """
    Currency.
    """
    USD = "USD"
    HKD = "HKD"
    CNY = "CNY"


class Interval(Enum):
    """
    Interval of bar data.
    """
    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"


class KlinePattern(Enum):
    CDL2CROWS = 'CDL2CROWS'                         #两只乌鸦
    CDL3BLACKCROWS = 'CDL3BLACKCROWS'               #三只乌鸦
    CDL3INSIDE = 'CDL3INSIDE'
    CDL3LINESTRIKE = 'CDL3LINESTRIKE'
    CDL3OUTSIDE = 'CDL3OUTSIDE'
    CDL3STARSINSOUTH = 'CDL3STARSINSOUTH'
    CDL3WHITESOLDIERS = 'CDL3WHITESOLDIERS'         #红三兵
    CDLABANDONEDBABY = 'CDLABANDONEDBABY'
    CDLADVANCEBLOCK = 'CDLADVANCEBLOCK'
    CDLBELTHOLD = 'CDLBELTHOLD'
    CDLBREAKAWAY = 'CDLBREAKAWAY'
    CDLCLOSINGMARUBOZU = 'CDLCLOSINGMARUBOZU'
    CDLCONCEALBABYSWALL = 'CDLCONCEALBABYSWALL'
    CDLCOUNTERATTACK = 'CDLCOUNTERATTACK'
    CDLDARKCLOUDCOVER = 'CDLDARKCLOUDCOVER'         #乌云盖顶
    CDLDOJI = 'CDLDOJI'
    CDLDOJISTAR = 'CDLDOJISTAR'
    CDLDRAGONFLYDOJI = 'CDLDRAGONFLYDOJI'
    CDLENGULFING = 'CDLENGULFING'
    CDLEVENINGDOJISTAR = 'CDLEVENINGDOJISTAR'
    CDLEVENINGSTAR = 'CDLEVENINGSTAR'               #黄昏之星
    CDLGAPSIDESIDEWHITE = 'CDLGAPSIDESIDEWHITE'
    CDLGRAVESTONEDOJI = 'CDLGRAVESTONEDOJI'
    CDLHAMMER = 'CDLHAMMER'                         #锤子
    CDLHANGINGMAN = 'CDLHANGINGMAN'
    CDLHARAMI = 'CDLHARAMI'
    CDLHARAMICROSS = 'CDLHARAMICROSS'
    CDLHIGHWAVE = 'CDLHIGHWAVE'
    CDLHIKKAKE = 'CDLHIKKAKE'
    CDLHIKKAKEMOD = 'CDLHIKKAKEMOD'
    CDLHOMINGPIGEON = 'CDLHOMINGPIGEON'
    CDLIDENTICAL3CROWS = 'CDLIDENTICAL3CROWS'
    CDLINNECK = 'CDLINNECK'
    CDLINVERTEDHAMMER = 'CDLINVERTEDHAMMER'         #倒锤
    CDLKICKING = 'CDLKICKING'
    CDLKICKINGBYLENGTH = 'CDLKICKINGBYLENGTH'
    CDLLADDERBOTTOM = 'CDLLADDERBOTTOM'
    CDLLONGLEGGEDDOJI = 'CDLLONGLEGGEDDOJI'
    CDLLONGLINE = 'CDLLONGLINE'
    CDLMARUBOZU = 'CDLMARUBOZU'
    CDLMATCHINGLOW = 'CDLMATCHINGLOW'
    CDLMATHOLD = 'CDLMATHOLD'
    CDLMORNINGDOJISTAR = 'CDLMORNINGDOJISTAR'
    CDLMORNINGSTAR = 'CDLMORNINGSTAR'               #早晨之星
    CDLONNECK = 'CDLONNECK'
    CDLPIERCING = 'CDLPIERCING'
    CDLRICKSHAWMAN = 'CDLRICKSHAWMAN'
    CDLRISEFALL3METHODS = 'CDLRISEFALL3METHODS'
    CDLSEPARATINGLINES = 'CDLSEPARATINGLINES'
    CDLSHOOTINGSTAR = 'CDLSHOOTINGSTAR'             #流星线
    CDLSHORTLINE = 'CDLSHORTLINE'
    CDLSPINNINGTOP = 'CDLSPINNINGTOP'
    CDLSTALLEDPATTERN = 'CDLSTALLEDPATTERN'
    CDLSTICKSANDWICH = 'CDLSTICKSANDWICH'
    CDLTAKURI = 'CDLTAKURI'
    CDLTASUKIGAP = 'CDLTASUKIGAP'
    CDLTHRUSTING = 'CDLTHRUSTING'
    CDLTRISTAR = 'CDLTRISTAR'
    CDLUNIQUE3RIVER = 'CDLUNIQUE3RIVER'
    CDLUPSIDEGAP2CROWS = 'CDLUPSIDEGAP2CROWS'
    CDLXSIDEGAP3METHODS = 'CDLXSIDEGAP3METHODS'