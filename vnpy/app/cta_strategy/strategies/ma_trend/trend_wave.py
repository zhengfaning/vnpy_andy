import pandas as pd
import math

class TrendWave:
    def __init__(self):
        self.data = []
        self.threshold = {"min_range": 0.0005, "large": 0.001, "recent_time": 10}
        self.wave = self.parse_wave(self.data)
        pd_wave = pd.DataFrame(self.wave)
        self.optimize, self.statistics = self.optimize_wave(pd_wave)
    def init(self):
        # length = len(self.data)
        # if len(self.data) <= 0:
        #     return
        # self.max_pos = length - 1
        self.result_data = {"value": [], "range": [], "pos": [], "length": [], "time":[]}
        self.start_pos = 0
        self.cur_vol = 0
        self.cur_pos = 0
        self.u_tag = None
        self.d_tag = None
        self.end_tag = None

    def update(self, new_data):
        self.data.append(new_data)
        length = len(self.data)
        if length == 1:
            self.diff_val = new_data
            self.cur_pos += 1
            return
        # max_pos = length - 1

        if self.diff_val < self.data[self.cur_pos]:
            self.u_tag = self.cur_pos
            if self.d_tag:
                if self.d_tag - self.start_pos > 0:
                    self.end_tag = self.d_tag
        elif self.diff_val > self.data[self.cur_pos]:
            self.d_tag = self.cur_pos
            if self.u_tag:
                if self.u_tag - self.start_pos > 0:
                    self.end_tag = self.u_tag

        if self.end_tag is not None:
            line_len = self.end_tag - self.start_pos
            range_val = round(self.data[self.end_tag] / self.data[self.start_pos] - 1, 4)
            self.result_data["range"].append(range_val)
            self.result_data["length"].append(line_len)
            self.result_data["value"].append(self.data[self.end_tag])
            self.result_data["pos"].append(self.end_tag)
            self.result_data["time"].append(self.data.index[self.end_tag])
            self.start_pos = self.end_tag
            self.end_tag = None

        self.cur_vol += self.data[self.cur_pos] - self.diff_val
        self.diff_val = self.data[self.cur_pos]
        self.cur_pos += 1

    def parse_wave(self, data):


            # r = array[::-1]
        # result = {"value": [], "range": [], "pos": [], "length": [], "plus": [], "minus":[], "plus_len": [], "minus_len":[]}
        result = {"value": [], "range": [], "pos": [], "length": [], "time":[]}
        r = data
        l = len(data) - 1
        now = r[0]
        # v_list.append(now)
        # p_list.append(0)
        pos = 1

        vol = 0
        u_tag = None
        d_tag = None
        end_tag = None
        start_pos = 0
        while pos < l:
            if math.isnan(now):
                now = r[pos]
                pos += 1
                continue
            else:
                start_pos = pos - 1
                break

        while pos < l:

            if now < r[pos]:
                u_tag = pos
                if d_tag:
                    if d_tag - start_pos > 0:
                        end_tag = d_tag
            elif now > r[pos]:
                d_tag = pos
                if u_tag:
                    if u_tag - start_pos > 0:
                        end_tag = u_tag

            if end_tag is not None:
                line_len = end_tag - start_pos
                range_val = round(r[end_tag] / r[start_pos] - 1, 4)
                result["range"].append(range_val)
                result["length"].append(line_len)
                result["value"].append(r[end_tag])
                result["pos"].append(end_tag)
                result["time"].append(r.index[end_tag])
                start_pos = end_tag
                end_tag = None

            vol += r[pos] - now
            now = r[pos]
            pos += 1

        if end_tag is None:
            end_tag = l - 1
            line_len = end_tag - start_pos
            range_val = round(r[end_tag] / r[start_pos] - 1, 4)
            result["range"].append(range_val)
            result["length"].append(line_len)
            result["value"].append(r[end_tag])
            result["pos"].append(end_tag)
            result["time"].append(r.index[end_tag])
            start_pos = end_tag

        return result

    def optimize_wave(self, data):
        # 大幅度 小幅度 平盘 最近表现
        # 相差10%内为相等幅度
        statistics = {"large":[], "recent":{"range":[], "length":[],"minus":[], "plus":[], "sum_range": 0}, "minus":[], "plus":[]}
        ten_min = statistics["recent"]
        large = self.threshold["large"]
        candidate = []
        min_range = self.threshold["min_range"]
        result = {"value": [], "range": [], "pos": [], "length": []}
        i = 0



        while i < data.index.size:
            val = data["range"][i]

            candidate.append(i)
            sum_candidate = sum(map(lambda _i: data["range"][_i], candidate))

            i += 1
            if abs(sum_candidate) > min_range:
                j = i + 2
                while j < data.index.size:
                    j_1 = j - 2
                    j_2 = j - 1
                    j_3 = j

                    t1 = data["range"][j_1]
                    t2 = data["range"][j_2]
                    t3 = data["range"][j_3]

                    if abs(t1) > min_range:
                        break

                    next_r = t1 + t2 + t3

                    if sum_candidate >= 0 and (next_r) < -0.0005 or \
                       sum_candidate < 0 and (next_r) > 0.0005:
                        break

                    candidate.append(j_1)
                    candidate.append(j_2)
                    sum_candidate += t1
                    sum_candidate += t2
                    i = j
                    j += 2

                sum_len = sum(map(lambda _i: data["length"][_i], candidate))
                result["range"].append(sum_candidate)
                result["length"].append(sum_len)
                result["value"].append(data["value"][candidate[-1]])
                result["pos"].append(data["pos"][candidate[-1]])
                candidate = []

        if len(candidate) > 0:
            sum_len = sum(map(lambda _i: data["length"][_i], candidate))
            result["range"].append(sum_candidate)
            result["length"].append(sum_len)
            result["value"].append(data["value"][candidate[-1]])
            result["pos"].append(data["pos"][candidate[-1]])

        count = self.threshold["recent_time"]
        for i in range(len(result["length"]))[::-1]:

            if count < 0:
                break
            l = result["length"][i]
            r = result["range"][i]

            statistics["recent"]["length"].append(l)
            statistics["recent"]["range"].append(r)
            if r > 0:
                statistics["recent"]["plus"].append(r)
            else:
                statistics["recent"]["minus"].append(r)
            count -= l
        statistics["recent"]["sum_range"] = sum(statistics["recent"]["range"])
        for val in result["range"]:
            if val > 0:
                statistics["plus"].append(val)
            else:
                statistics["minus"].append(val)
            if abs(val) > large:
                statistics["large"].append(val)
        sort_length = list(data["length"])
        sort_length.sort(reverse=True)
        result["sort_length"] = sort_length

        return result, statistics
        # for i in range(data.index.size):
        #     item = data["range"][i]
        #
        #     candidate.append(i)
        #     sum_candidate = sum(map(lambda _i: data["range"][_i], candidate))
        #
        #     if abs(sum_candidate) > 0.0005:
        #         # if len(candidate) > 0:
        #         result.append(candidate)
        #         candidate = []
        #     else:
        #         candidate.append(i)
        #         result.append(i)
        #     continue





