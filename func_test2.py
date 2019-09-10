import pandas as pd
import numpy as np
import datetime
from itertools import accumulate
import operator
import sys

a = [2, 34, 5,6]
b = 4

c = np.std(a + [b] )
print(c)