import numpy as np
import pandas as pd

from vnpy.app.cta_strategy.strategies.ma_trend.constant import DataSignalName, DataMethod
from vnpy.app.cta_strategy.strategies.ma_trend.data_center import DataCreator
from vnpy.trader.utility import ArrayManager


class MaInfoCreator(DataCreator):
    parameters = ["ma_level", "max_length"]
    ma_level = [10,20,30,60,120]
    max_length = 400

    trend_info = pd.DataFrame()

    def init(self):
        self.data_center.connect(DataSignalName.ArrayManager, self.on_am_data)
        self.data_center.add_method(DataMethod.MaInfoData, self.data)

    def data(self, parameters=None):
        return self.trend_info

    def tag(self):
        return "ma_info"

    def on_am_data(self, data):
        last_ma_lvl = self.ma_level[-1]
        am: ArrayManager = data[DataSignalName.ArrayManager]
        if am.count < last_ma_lvl:
            return

        close = am.close[-1]
        dt = am.time_array[-1]


        trend_info = {}
        ma_data = []
        for i in self.ma_level:
            ma = am.sma(i)
            trend_info[i] = [round(ma, 2)]
            ma_data.append(ma)

        ma = am.sma(5)
        trend_info[5] = [round(ma, 2)]
        # 统计穿越  start
        ma_lvl_tag = []
        last_lvl = self.ma_level[-1]
        for i in self.ma_level[:-1]:
            val = 1 if trend_info[i] > trend_info[last_lvl] else 0
            ma_lvl_tag.append(val)
        bincount_val = np.bincount(np.array(ma_lvl_tag[:-1]))
        trend_info["ma3_5_ref"] = int(bincount_val[1]) if bincount_val.size > 1 else 0

        start = 1
        for lvl_index in range(start, len(self.ma_level)):
            ma_lvl_tag = []
            lvl = self.ma_level[-lvl_index]
            for i in self.ma_level[:-lvl_index]:
                val = 1 if trend_info[i] > trend_info[lvl] else 0
                ma_lvl_tag.append(val)
            bincount_val = np.bincount(np.array(ma_lvl_tag))
            count = len(ma_lvl_tag)
            tag = "ma{}_{}_ref".format(count, count + 1)
            trend_info[tag] = int(bincount_val[1]) if bincount_val.size > 1 else 0

        trend_info["close"] = close
        data = []
        diff = ma_data[-1]
        for v in ma_data:
            data.append(round(v / diff, 6))

        trend_info["ma5"] = [round(np.var(data) * 1000000, 8)]

        data = []
        diff = ma_data[-3]
        for v in ma_data[:-2]:
            data.append(round(v / diff, 6))

        trend_info["ma3"] = [round(np.var(data) * 1000000, 8)]

        if len(self.trend_info) < self.max_length:
            self.trend_info = self.trend_info.append(pd.DataFrame(trend_info, index=[pd.to_datetime(dt)]))
        else:
            index = self.trend_info.index[0]
            self.trend_info = self.trend_info.drop([index])
            self.trend_info = self.trend_info.append(pd.DataFrame(trend_info, index=[pd.to_datetime(dt)]))

        self.push(DataSignalName.MaInfo, self.trend_info)

    @property
    def info(self):
        return self.trend_info
