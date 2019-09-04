import numpy as np
import talib
import math

class Algorithm:
    # @staticmethod
    # def lm_kdj(df, n,ksgn='close'):
    #     lowList= pd.rolling_min(df['low'], n)
    #     lowList.fillna(value=pd.expanding_min(df['low']), inplace=True)
    #     highList = pd.rolling_max(df['high'], n)
    #     highList.fillna(value=pd.expanding_max(df['high']), inplace=True)
    #     rsv = (df[ksgn] - lowList) / (highList - lowList) * 100
    #     df['kdj_k'] = pd.ewma(rsv,com=2)
    #     df['kdj_d'] = pd.ewma(df['kdj_k'],com=2)
    #     df['kdj_j'] = 3.0 * df['kdj_k'] - 2.0 * df['kdj_d']
    #     #print('n df',len(df))
    #     return df

    @staticmethod
    def kdj(high_array, low_array, close_array, fastk_period=9, slowk_period=3, slowd_period=3):
        #计算kd指标
        # high_prices = np.array([v['high'] for v in data])
        # low_prices = np.array([v['low'] for v in data])
        # close_prices = np.array([v['close'] for v in data])

        max_close = talib.MAX(high_array, timeperiod=fastk_period)
        min_close = talib.MIN(low_array, timeperiod=fastk_period)
        
        for k in range(len(low_array)):
            if k<fastk_period and k>1:
                aaa = talib.MIN(low_array,timeperiod=k)
                bbb = talib.MAX(high_array,timeperiod=k)
                min_close[k]= aaa[k]
                max_close[k]= bbb[k]
            elif k==1 or k==0:
                min_close[k]=low_array[k]
                max_close[k]=high_array[k]
        # rsv = maxmin(data, fastk_period)
        diff = max_close - min_close
        diff[diff == 0] = 1 
        # diff = 1 if diff == 0 else diff
        fast_k = (close_array - min_close)/diff *100
        ppp = max_close - min_close
        for t in range(len(close_array)):
            if max_close[t] == min_close[t]:
                fast_k[t] = 0
        slow_k1 = np.full_like(close_array,50)
        slow_d1 = np.full_like(close_array,50)
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

    @staticmethod  
    def wave(data, window = 0.0003):

            if len(data) <= 0:
                return 
            # r = array[::-1]
            v_list = []
            p_list = []
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