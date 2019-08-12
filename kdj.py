import numpy
import talib
import numpy as np
from math import isnan


def maxmin(data,fastk_period):
    close_prices = data["close"].values #np.nan_to_num(np.array([v['close'] for v in data]))
    max_prices = data["high"].values #np.nan_to_num(np.array([v['high'] for v in data]))
    min_prices = data["low"].values #np.nan_to_num(np.array([v['low'] for v in data]))
    
    max_close = talib.MAX(max_prices, timeperiod=fastk_period)
    min_close = talib.MIN(min_prices, timeperiod=fastk_period)
    
    try:
        for k in range(len(min_prices)):
            if k<fastk_period and k>1:
                aaa = talib.MIN(min_prices,timeperiod=k)
                bbb = talib.MAX(max_prices,timeperiod=k)
                min_close[k]= aaa[k]
                max_close[k]= bbb[k]
            elif k==1 or k==0:
                min_close[k]=min_prices[k]
                max_close[k]=max_prices[k]
    except Exception as e:
        print(e)
            
    indicators= {
        'close': close_prices,
        'max': max_close,
        'min': min_close
    }
    return indicators

def calc_kdj(data, fastk_period=9, slowk_period=3, slowd_period=3):
    #计算kd指标
    high_prices = data["high"].values #np.array([v['high'] for v in data])
    low_prices = data["low"].values #np.array([v['low'] for v in data])
    close_prices = data["close"].values #np.array([v['close'] for v in data])

    rsv = maxmin(data, fastk_period)
    fast_k = (rsv['close']-rsv['min'])/(rsv['max']-rsv['min'])*100
    ppp = rsv['max']-rsv['min']
    for t in range(len(close_prices)):
        if rsv['max'][t]==rsv['min'][t]:
            fast_k[t] = 0
    slow_k1 = np.full_like(close_prices,50)
    slow_d1 = np.full_like(close_prices,50)
    for k in range(1,len(fast_k)):
        slow_k1[k] = slow_k1[k-1]*2/3+fast_k[k]/3
        slow_d1[k] = slow_d1[k-1]*2/3+slow_k1[k]/3
    
    indicators= {
        'rsv':fast_k,
        'max':rsv['max'],
        'min':rsv['min'],
        'k': slow_k1,
        'd': slow_d1,
        'j': 3 * slow_k1 - 2 * slow_d1
    }
    return indicators

# df=get_price(frequency='daily',fields=['close','high','low'], security='600036.XSHG', skip_paused=False, fq='pre',start_date='2018-1-16',end_date='2018-12-12')
# data = df.to_dict('records')

# bbb=self_KDJ(data)
# df['rsv']=bbb['rsv']
# df['max']=bbb['max']
# df['min']=bbb['min']
# df['k']=bbb['k']
# df['d']=bbb['d']
# df['j']=bbb['j']
# dm=df[['k','d','j']]
# dm.plot(figsize=(20,10))