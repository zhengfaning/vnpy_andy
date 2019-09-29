import pandas as pd
import math

class AnalyseWave:
    def __init__(self, data):
        self.data = data

    def parse_wave(self, data):

        if len(data) <= 0:
            return
            # r = array[::-1]
        result = {"value": [], "range": [], "pos": [], "length": [], "plus": [], "minus":[], "plus_len": [], "minus_len":[]}
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
                # if range_val > 0:
                #     result["plus"].append(range_val)
                #     result["plus_len"].append(line_len)
                # else:
                #     result["minus"].append(range_val)
                #     result["minus_len"].append(line_len)
                result["range"].append(range_val)
                result["length"].append(line_len)
                start_pos = end_tag
                result["value"].append(r[end_tag])
                result["pos"].append(end_tag)
                end_tag = None

            vol += r[pos] - now
            now = r[pos]
            pos += 1
        return pd.DataFrame(result)

    def merge(self, data):
        candidate = []
        new_range = []
        new_length = []
        i = 0
        while i < data.index.size:
            t1 = data["range"][i]
            candidate.append(i)
            sum_candidate = sum(map(lambda _i: data["range"][_i], candidate))

            i += 1
            if abs(sum_candidate) > 0.0005:
                j = i + 2
                while j < data.index.size:
                    j_1 = j - 2
                    j_2 = j - 1
                    j_3 = j

                    t1 = data["range"][j_1]
                    t2 = data["range"][j_2]
                    t3 = data["range"][j_3]

                    if abs(t1) > 0.0005:
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
                new_range.append(sum_candidate)






        for i in range(data.index.size):
            item = data["range"][i]

            candidate.append(i)
            sum_candidate = sum(map(lambda _i: data["range"][_i], candidate))

            if abs(sum_candidate) > 0.0005:
                # if len(candidate) > 0:
                result.append(candidate)
                candidate = []
            else:
                candidate.append(i)
                result.append(i)
            continue





