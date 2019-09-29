class TrendData(dict):

    _data = {}
    _long = False
    _short = False

    def __init__(self, *args, **kwargs):
        super(TrendData, self).__init__(*args, **kwargs)


    def long_sign(self):
        self._long = True

    def short_sign(self):
        self._short = True

    @property
    def long(self):
        return self._long

    @property
    def short(self):
        return self._short

    @property
    def data(self):
        return self._data


d = TrendData(xx=1, yy=2)
print(d)
print('xx' in d)