import datetime

import numpy as np
import pandas as pd

from abu.UtilBu import ABuRegUtil as reg_util
from abu.UtilBu.ABuRegUtil import calc_regress_deg
from vnpy.app.cta_strategy.strategies.ma_trend.analyse_wave import AnalyseWave
from vnpy.app.cta_strategy.strategies.ma_trend.constant import DataSignalName
from vnpy.app.cta_strategy.strategies.ma_trend.data_center import DataCreator
from vnpy.app.cta_strategy.strategies.ma_trend.time_manager import ClockManager
from vnpy.trader.constant import Direction
from vnpy.trader.object import BarData
from vnpy.trader.utility import ArrayManager




class MaDistCreator(DataCreator):
    _data = pd.DataFrame()
    parameters = ["ma_level", "threshold"]
    # trend_info = pd.DataFrame()
    ma_level = [10, 20, 30, 60, 120]
    base_ma = 5
    max_length = 3
    dist_data = []
    time_mgr = ClockManager(datetime.time(10, 30), datetime.time(16, 0))

    # def __init__(self, am: ArrayManager, ma_level, event_groups=None):
    #     self.am = am
    #     self.ma_level = ma_level
    #     self.event_groups = event_groups


    def tag(self):
        return "ma_dist"

    def init(self):
        self.data_center.connect("ma_info", self.on_ma_info)

    def on_ma_info(self, data):
        ma_info = data["ma_info"]
        last = ma_info.iloc[-1]
        dt = ma_info.index[-1].to_pydatetime()
        base_ma = last[self.base_ma]
        dist_ls = []
        diff = 0
        for l in self.ma_level:
            v = last[l]
            dist = (base_ma / v) - 1
            if dist >= 0:
                diff += 1
            dist_ls.append(dist)



        item = (diff, np.array(dist_ls))
        self.data_center.record["ma_dist"] = item
        if len(self.dist_data) < self.max_length:
            self.dist_data.append(item)
        else:
            self.dist_data[:-1] = self.dist_data[1:]
            self.dist_data[-1] = item

        # self.push(DataSignalName.MaDist, data)
    # def set_reference(self, ma_index):
    #     if ma_index not in range(len(self.ma_level)):
    #         return
    #
    #     self.reference = self.ma_level[ma_index]



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
