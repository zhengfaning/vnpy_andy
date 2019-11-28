import numpy as np
import pandas as pd

from abu.UtilBu import ABuRegUtil as reg_util
from abu.UtilBu.ABuRegUtil import calc_regress_deg
from vnpy.app.cta_strategy.strategies.ma_trend.analyse_wave import AnalyseWave
from vnpy.app.cta_strategy.strategies.ma_trend.constant import DataSignalName
from vnpy.app.cta_strategy.strategies.ma_trend.data_center import DataCreator
from vnpy.trader.constant import Direction
from vnpy.trader.object import BarData
from vnpy.trader.utility import ArrayManager


class TrendData(dict):
    _long = False
    _short = False

    def __init__(self, *args, **kwargs):
        super(TrendData, self).__init__(*args, **kwargs)

    def long_sign(self):
        self._long = True

    def short_sign(self):
        self._short = True

    @property
    def long(self):
        return self._long

    @property
    def short(self):
        return self._short


'''
    趋势监视器
    1.发现趋势
    2.基准线比较
'''


class TrendInfoCreator(DataCreator):
    _data = pd.DataFrame()
    parameters = ["ma_level", "threshold"]
    # trend_info = pd.DataFrame()
    reference = None
    max_length = 400
    ma_level = [10, 20, 30, 60, 120]
    threshold = {"ma3": 0.03, "deg": 0.03}
    trend_ls = {}

    # def __init__(self, am: ArrayManager, ma_level, event_groups=None):
    #     self.am = am
    #     self.ma_level = ma_level
    #     self.event_groups = event_groups

    def data(self):
        return self.trend_ls

    def tag(self):
        return "trend_info"

    def init(self):
        self.data_center.connect(DataSignalName.MaInfo, self.on_ma_info)

    def on_ma_info(self, data):
        trend_info = data["ma_info"]

        self.ma3_catch(trend_info)

        ma_info = trend_info.iloc[-1]

        drop = []

        for k in self.trend_ls.keys():
            item = self.trend_ls[k]
            data = item["data"]
            if len(data) >= 60:
                drop.append(k)
            else:
                item["data"] = item["data"].append(ma_info)

        if len(drop) > 0:
            for i in drop:
                self.trend_ls.pop(i)

    # def set_reference(self, ma_index):
    #     if ma_index not in range(len(self.ma_level)):
    #         return
    #
    #     self.reference = self.ma_level[ma_index]

    def statistics(self, trend_info, calc_data):
        ma_data = [self.trend_info[10][-1], self.trend_info[20][-1], self.trend_info[30][-1]]
        min_val = min(ma_data)
        max_val = max(ma_data)
        diff_val = self.trend_info[60][-1]

        calc_data['diff_60_min'] = abs(diff_val / min_val - 1)
        calc_data['diff_60_max'] = abs(diff_val / max_val - 1)

        if self.trend_info.iloc[-1]["ma3"] <= self.threshold["ma3"]:
            calc_data["kdj_key"] = True

        calc_data['trend_info'] = self.trend_info.iloc[-1].to_dict()

    def adjoin(self, min_val, max_val, diff_val):
        if diff_val >= min_val and diff_val <= max_val:
            return True

        scale = 0.0001
        if abs(diff_val / min_val - 1) > scale or abs(diff_val / max_val - 1) > scale:
            return True
        else:
            return False

    '''
        检查最新数据,根据条件筛选出起点,根据方向阈值发出回调,方向为long和short
    '''

    def ma3_catch(self, trend_info):
        ma_info = trend_info.iloc[-1]
        ma3_std = ma_info["ma3"]

        if ma3_std <= self.threshold["ma3"]:
            self.trend_ls["ma3"] = TrendData(data=trend_info[-15:-1], start=trend_info.iloc[-1])
            return

        if "ma3" in self.trend_ls:
            ma3_trend = self.trend_ls["ma3"]
            if not ma3_trend.long or not ma3_trend.short:
                data = ma3_trend["data"]
                close = (data[10] + data[20] + data[30]) / 3
                if len(data) > 10:
                    y_fit = reg_util.regress_y_polynomial(close, zoom=True)
                    deg = calc_regress_deg(y_fit[:10], False)
                else:
                    deg = calc_regress_deg(close, False)
                if not ma3_trend.long and deg > self.threshold["deg"]:
                    self.push(DataSignalName.TrendInfo,
                              {"data": ma3_trend, "deg": deg, "type": "ma3", "sign": ma3_trend.long_sign,
                               "direction": Direction.LONG}
                              )
                if not ma3_trend.short and deg < -self.threshold["deg"]:
                    self.push(DataSignalName.TrendInfo,
                              {"data": ma3_trend, "deg": deg, "type": "ma3", "sign": ma3_trend.short_sign,
                               "direction": Direction.SHORT}
                              )
