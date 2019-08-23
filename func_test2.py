import pandas as pd
import numpy as np
import datetime
from itertools import accumulate
import operator

def array_sub(data):
    l = len(data)
    result = None

    for v in data[::-1]:
        if result is None:
            result = v
        else:
            result -= v
    
    return result




a = np.array([3,2,1])
r = np.where(a==0)
b = np.array([3, 3, 2, 2, 2, 4, 4, 5, 4, 4])
y = array_sub( [1,2,3,4])
z = y / len(a)
v1 = np.mean(b)
v2 = np.var(b)
v3 = np.std(b)
t1 = np.bincount(a)

print(len(t1))