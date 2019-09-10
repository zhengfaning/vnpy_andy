import pandas as pd
import numpy as np
import datetime
from itertools import accumulate
import operator
import sys

d1 = datetime.datetime(2013, 8, 5,15,50)
d2 = datetime.datetime(2013, 8, 4,21,9)
r = d1 - d2
r.total_seconds()
print(type(r))
print(r)