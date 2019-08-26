import pandas as pd
import numpy as np
import datetime
from itertools import accumulate
import operator
import sys
print(sys.getdefaultencoding())
#coding=utf-8

s='中文'

x = None
if(isinstance(s, str)):
#s为u'中文'
    x = s.encode('gb2312')
else:
#s为'中文'
    x = s.decode('utf8').encode('gb2312')

print(x)