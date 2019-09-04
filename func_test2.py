import pandas as pd
import numpy as np
import datetime
from itertools import accumulate
import operator
import sys

a = [2, 2, 1, 1, 1,2,2,2,2] 
print(np.cov(a), np.std(a), np.var(a))