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
    ECBOT = "ECBOT"
    CFE = "CFE"
    CMECRYPTO = "CMECRYPTO"
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

EXCHANGE_CALENDAR = {
    Exchange.SMART: "NYSE",
}


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

KLINE_PATTERN_CHINESE = {
    KlinePattern.CDL2CROWS : "两只乌鸦",
    KlinePattern.CDL3BLACKCROWS : "三只乌鸦",
    KlinePattern.CDL3INSIDE : "三内部上涨和下跌",
    KlinePattern.CDL3LINESTRIKE : "三线震荡",
    KlinePattern.CDL3OUTSIDE : "三外部上涨和下跌",
    KlinePattern.CDL3STARSINSOUTH : "南方三星",
    KlinePattern.CDL3WHITESOLDIERS : "三白兵",
    KlinePattern.CDLABANDONEDBABY : "弃婴",
    KlinePattern.CDLADVANCEBLOCK : "大敌当前/推进",
    KlinePattern.CDLBELTHOLD : "捉腰带线",
    KlinePattern.CDLBREAKAWAY: "脱离",
    KlinePattern.CDLCLOSINGMARUBOZU : "收盘光头光脚",
    KlinePattern.CDLCONCEALBABYSWALL : "藏婴吞没",
    KlinePattern.CDLCOUNTERATTACK : "反击线",
    KlinePattern.CDLDARKCLOUDCOVER : "乌云盖顶",
    KlinePattern.CDLDOJI : "十字",
    KlinePattern.CDLDOJISTAR : "十字星",
    KlinePattern.CDLDRAGONFLYDOJI : "蜻蜓十字/T形十字",
    KlinePattern.CDLENGULFING : "吞没模式",
    KlinePattern.CDLEVENINGDOJISTAR : "黄昏十字星",
    KlinePattern.CDLEVENINGSTAR : "黄昏之星",
    KlinePattern.CDLGAPSIDESIDEWHITE : "向上/下跳空并列阳线",
    KlinePattern.CDLGRAVESTONEDOJI : "墓碑十字/倒T十字",
    KlinePattern.CDLHAMMER : "锤头",
    KlinePattern.CDLHANGINGMAN : "上吊线",
    KlinePattern.CDLHARAMI : "母子线/阴阳线",
    KlinePattern.CDLHARAMICROSS : "十字孕线",
    KlinePattern.CDLHIGHWAVE : "风高浪大线/长脚十字线",
    KlinePattern.CDLHIKKAKE : "陷阱",
    KlinePattern.CDLHIKKAKEMOD : "改良的陷阱",
    KlinePattern.CDLHOMINGPIGEON : "家鸽",
    KlinePattern.CDLIDENTICAL3CROWS : "三胞胎乌鸦",
    KlinePattern.CDLINNECK : "颈内线",
    KlinePattern.CDLINVERTEDHAMMER : "倒锤头",
    KlinePattern.CDLKICKING : "反冲形态",
    KlinePattern.CDLKICKINGBYLENGTH : "由较长光头光脚决定的反冲形态",
    KlinePattern.CDLLADDERBOTTOM : "梯底",
    KlinePattern.CDLLONGLEGGEDDOJI : "长脚十字",
    KlinePattern.CDLLONGLINE : "长蜡烛线",
    KlinePattern.CDLMARUBOZU : "光头光脚/缺影线",
    KlinePattern.CDLMATCHINGLOW : "相同低价/匹配低价",
    KlinePattern.CDLMATHOLD : "铺垫",
    KlinePattern.CDLMORNINGDOJISTAR : "十字晨星/早晨十字星",
    KlinePattern.CDLMORNINGSTAR : "晨星",
    KlinePattern.CDLONNECK : "颈上线",
    KlinePattern.CDLPIERCING : "刺透形态",
    KlinePattern.CDLRICKSHAWMAN : "黄包车夫",
    KlinePattern.CDLRISEFALL3METHODS : "Rising/Falling Three Methods 上升/下降三法",
    KlinePattern.CDLSEPARATINGLINES : "Separating Lines 分离线/分割线",
    KlinePattern.CDLSHOOTINGSTAR : "Shooting Star 射击之星/流星",
    KlinePattern.CDLSHORTLINE : "Short Line Candle 短蜡烛线",
    KlinePattern.CDLSPINNINGTOP : "Spinning Top 纺锤",
    KlinePattern.CDLSTALLEDPATTERN : "Stalled Pattern 停顿形态",
    KlinePattern.CDLSTICKSANDWICH : "Stick Sandwich 条形三明治",
    KlinePattern.CDLTAKURI : "Takuri (Dragonfly Doji with very long lower shadow) 探水竿",
    KlinePattern.CDLTASUKIGAP : "Tasuki Gap 跳空并列阴阳线",
    KlinePattern.CDLTHRUSTING : "Thrusting Pattern 插入形态",
    KlinePattern.CDLTRISTAR : "Tristar Pattern 三星形态",
    KlinePattern.CDLUNIQUE3RIVER : "Unique 3 River 独特三河",
    KlinePattern.CDLUPSIDEGAP2CROWS : "Upside Gap Two Crows 向上跳空的两只乌鸦/双飞乌鸦",
    KlinePattern.CDLXSIDEGAP3METHODS : "Upside/Downside Gap Three Methods 上升/下降跳空三法",
}