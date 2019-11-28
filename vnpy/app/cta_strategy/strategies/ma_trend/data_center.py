from abc import ABC, abstractmethod
from vnpy.trader.object import BarData


class DataCenter(object):
    # creator = []
    observer = {}

    def __init__(self, component:dict=None):
        self._record = {}
        self._call = {}
        self._component = component

    def reset_record(self):
        self._record = {}

    def add_method(self, call_name, callback):
        self._call[call_name] = callback

    @property
    def component(self):
        return  self._component


    @property
    def record(self):
        return  self._record

    def connect(self, signal, callback):
        if signal not in self.observer:
            self.observer[signal] = []

        if callback not in self.observer[signal]:
            self.observer[signal].append(callback)

    def get_creator(self, tag, callback):
        if tag not in self.observer:
            self.observer[tag] = []

        if callback not in self.observer[tag]:
            self.observer[tag].append(callback)

    def invoke(self, name, parameters):
        if name in self._call:
            callback = self._call[name]
            return callback(parameters)

    def push(self, tag, data):
        if tag not in self.observer:
            return

        for callback in self.observer[tag]:
            callback({tag:data})

    # def on_update(self, bar:BarData):
    #     for creator in self.creator:
    #         creator.update(bar)

class DataCreator(ABC):
    def __init__(self, data_center: DataCenter, setting = None):
        self.data_center: DataCenter = data_center
        if setting is not None:
            self.update_setting(setting)
        self.init()

    def update_setting(self, setting: dict):
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])


    def push(self, signal, data):
        self.data_center.push(signal, data)

    @abstractmethod
    def init(self):
        pass




