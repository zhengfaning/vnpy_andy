"""
General utility functions.
"""

import json
from pathlib import Path
from typing import Callable

import numpy as np
import talib

from .object import BarData, TickData
from .constant import Exchange, Interval


def extract_vt_symbol(vt_symbol: str):
    """
    :return: (symbol, exchange)
    """
    symbol, exchange_str = vt_symbol.split(".")
    return symbol, Exchange(exchange_str)


def generate_vt_symbol(symbol: str, exchange: Exchange):
    """
    return vt_symbol
    """
    return f"{symbol}.{exchange.value}"


def _get_trader_dir(temp_name: str):
    """
    Get path where trader is running in.
    """
    cwd = Path.cwd()
    temp_path = cwd.joinpath(temp_name)

    # If .vntrader folder exists in current working directory,
    # then use it as trader running path.
    if temp_path.exists():
        return cwd, temp_path

    # Otherwise use home path of system.
    home_path = Path.home()
    temp_path = home_path.joinpath(temp_name)

    # Create .vntrader folder under home path if not exist.
    if not temp_path.exists():
        temp_path.mkdir()

    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".vntrader")


def get_file_path(filename: str):
    """
    Get path for temp file with filename.
    """
    return TEMP_DIR.joinpath(filename)


def get_folder_path(folder_name: str):
    """
    Get path for temp folder with folder name.
    """
    folder_path = TEMP_DIR.joinpath(folder_name)
    if not folder_path.exists():
        folder_path.mkdir()
    return folder_path


def get_icon_path(filepath: str, ico_name: str):
    """
    Get path for icon file with ico name.
    """
    ui_path = Path(filepath).parent
    icon_path = ui_path.joinpath("ico", ico_name)
    return str(icon_path)


def load_json(filename: str):
    """
    Load data from json file in temp path.
    """
    filepath = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            data = json.load(f)
        return data
    else:
        save_json(filename, {})
        return {}


def save_json(filename: str, data: dict):
    """
    Save data into json file in temp path.
    """
    filepath = get_file_path(filename)
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def round_to(value: float, target: float):
    """
    Round price to price tick value.
    """
    rounded = int(round(value / target)) * target
    return rounded


class BarGenerator:
    """
    For: 
    1. generating 1 minute bar data from tick data
    2. generateing x minute bar/x hour bar data from 1 minute data

    Notice:
    1. for x minute bar, x must be able to divide 60: 2, 3, 5, 6, 10, 15, 20, 30
    2. for x hour bar, x can be any number
    """

    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        """Constructor"""
        self.bar = None
        self.on_bar = on_bar

        self.interval = interval
        self.interval_count = 0

        self.window = window
        self.window_bar = None
        self.on_window_bar = on_window_bar

        self.last_tick = None
        self.last_bar = None

    def update_tick(self, tick: TickData):
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return

        if not self.bar:
            new_minute = True
        elif self.bar.datetime.minute != tick.datetime.minute:
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            self.bar.close_price = tick.last_price
            self.bar.open_interest = tick.open_interest
            self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick

    def update_bar(self, bar: BarData):
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            if not (bar.datetime.minute + 1) % self.window:
                finished = True
        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
                # 1-hour bar
                if self.window == 1:
                    finished = True
                # x-hour bar
                else:
                    self.interval_count += 1

                    if not self.interval_count % self.window:
                        finished = True
                        self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar

    def generate(self):
        """
        Generate the bar data and call callback immediately.
        """
        self.bar.datetime = self.bar.datetime.replace(
            second=0, microsecond=0
        )
        self.on_bar(self.bar)
        self.bar = None


class ArrayManager(object):
    """
    For:
    1. time series container of bar data
    2. calculating technical indicator value
    """

    def __init__(self, size=100):
        """Constructor"""
        self.count = 0
        self.size = size
        self.inited = False

        self.open_array = np.zeros(size)
        self.high_array = np.zeros(size)
        self.low_array = np.zeros(size)
        self.close_array = np.zeros(size)
        self.volume_array = np.zeros(size)
        self.time_array = [1] * size
        
    # def maxmin(data,fastk_period):
    #     close_prices = np.nan_to_num(np.array([v['close'] for v in data]))
    #     max_prices = np.nan_to_num(np.array([v['high'] for v in data]))
    #     min_prices = np.nan_to_num(np.array([v['low'] for v in data]))
        
    #     max_close = talib.MAX(self.high_array, timeperiod=fastk_period)
    #     min_close = talib.MIN(self.low_array, timeperiod=fastk_period)
        
    #     for k in range(len(min_prices)):
    #         if k<fastk_period and k>1:
    #             aaa = talib.MIN(min_prices,timeperiod=k)
    #             bbb = talib.MAX(max_prices,timeperiod=k)
    #             min_close[k]= aaa[k]
    #             max_close[k]= bbb[k]
    #         elif k==1 or k==0:
    #             min_close[k]=min_prices[k]
    #             max_close[k]=max_prices[k]
            
    #     indicators= {
    #         'close': close_prices,
    #         'max': max_close,
    #         'min': min_close
    #     }
    #     return indicators


    def wave(self, window = 0.0003):

        data = self.close_array
        if len(data) <= 0:
            return 
        # r = array[::-1]
        v_list = []
        p_list = []
        r = data
        l = len(data) - 1
        now = r[0]
        v_list.append(now)
        p_list.append(0)
        pos = 1
        start_pos = 0
        vol = 0
        u_tag = None
        d_tag = None
        end_tag = None
        while pos < l:

            if now < r[pos]:
                u_tag = pos
                if d_tag:
                    diff = r[start_pos] - r[d_tag]
                    if abs(diff / r[start_pos]) > window:
                        end_tag = d_tag
                        
            elif now > r[pos]:
                d_tag = pos
                if u_tag:
                    diff = r[start_pos] - r[u_tag]
                    if abs(diff / r[start_pos]) > window:
                        end_tag = u_tag

            if not end_tag is None:
                # print("point = {},start = {}, end = {}, vol = {:.2%}".format(
                # r[end_tag],start_pos, end_tag, vol/r[start_pos]))
                start_pos = end_tag
                v_list.append(r[end_tag])
                p_list.append(end_tag)
                end_tag = None

            vol += r[pos] - now
            now = r[pos]
            pos += 1
        # print(v_list)
        # print(p_list)
        return v_list, p_list

    def kdj(self, fastk_period=9, slowk_period=3, slowd_period=3):
        #计算kd指标
        # high_prices = np.array([v['high'] for v in data])
        # low_prices = np.array([v['low'] for v in data])
        # close_prices = np.array([v['close'] for v in data])

        max_close = talib.MAX(self.high_array, timeperiod=fastk_period)
        min_close = talib.MIN(self.low_array, timeperiod=fastk_period)
        
        for k in range(len(self.low_array)):
            if k<fastk_period and k>1:
                aaa = talib.MIN(self.low_array,timeperiod=k)
                bbb = talib.MAX(self.high_array,timeperiod=k)
                min_close[k]= aaa[k]
                max_close[k]= bbb[k]
            elif k==1 or k==0:
                min_close[k]=self.low_array[k]
                max_close[k]=self.high_array[k]
        # rsv = maxmin(data, fastk_period)
        diff = max_close - min_close

        fast_k = (self.close_array - min_close)/diff *100
        ppp = max_close - min_close
        for t in range(len(self.close_array)):
            if max_close[t] == min_close[t]:
                fast_k[t] = 0
        slow_k1 = np.full_like(self.close_array,50)
        slow_d1 = np.full_like(self.close_array,50)
        for k in range(1,len(fast_k)):
            slow_k1[k] = slow_k1[k-1]*2/3+fast_k[k]/3
            slow_d1[k] = slow_d1[k-1]*2/3+slow_k1[k]/3
        
        indicators= {
            'rsv':fast_k,
            'max':max_close,
            'min':min_close,
            'k': slow_k1,
            'd': slow_d1,
            'j': 3 * slow_k1 - 2 * slow_d1
        }
        return indicators

    def update_bar(self, bar):
        """
        Update new bar data into array manager.
        """
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]
        self.time_array[:-1] = self.time_array[1:]

        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume
        self.time_array[-1] = bar.datetime
    @property
    def open(self):
        """
        Get open price time series.
        """
        return self.open_array

    @property
    def high(self):
        """
        Get high price time series.
        """
        return self.high_array

    @property
    def low(self):
        """
        Get low price time series.
        """
        return self.low_array

    @property
    def close(self):
        """
        Get close price time series.
        """
        return self.close_array

    @property
    def volume(self):
        """
        Get trading volume time series.
        """
        return self.volume_array

    def sma(self, n, array=False):
        """
        Simple moving average.
        """
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]

    def std(self, n, array=False):
        """
        Standard deviation
        """
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]

    def cci(self, n, array=False):
        """
        Commodity Channel Index (CCI).
        """
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def atr(self, n, array=False):
        """
        Average True Range (ATR).
        """
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def rsi(self, n, array=False):
        """
        Relative Strenght Index (RSI).
        """
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fast_period, slow_period, signal_period, array=False):
        """
        MACD.
        """
        macd, signal, hist = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def adx(self, n, array=False):
        """
        ADX.
        """
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def boll(self, n, dev, array=False):
        """
        Bollinger Channel.
        """
        mid = self.sma(n, array)
        std = self.std(n, array)

        up = mid + std * dev
        down = mid - std * dev

        return up, down

    def keltner(self, n, dev, array=False):
        """
        Keltner Channel.
        """
        mid = self.sma(n, array)
        atr = self.atr(n, array)

        up = mid + atr * dev
        down = mid - atr * dev

        return up, down

    def donchian(self, n, array=False):
        """
        Donchian Channel.
        """
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]


def virtual(func: "callable"):
    """
    mark a function as "virtual", which means that this function can be override.
    any base class should use this or @abstractmethod to decorate all functions
    that can be (re)implemented by subclasses.
    """
    return func
