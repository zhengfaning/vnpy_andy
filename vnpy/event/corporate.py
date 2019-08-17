from queue import Queue
from engine import EventEngine,CorporateEvent,Event

class Corporate:
    def __init__(self, event_engine):
        self.event_engine = event_engine
        self.async_event_list = {}
        self.event_engine.register(CorporateEvent, self.process_event)

    def process_event(self, event: Event):
        if not event.data["end"]:
            name = event.data["name"]
            self.async_event_list[name] = Queue()
        else:
            q:Queue = self.async_event_list[name]
            q.put('end')
            


    def wait_async(self, name, timeout=30):
        if name in self.async_event_list:
            q:Queue = self.async_event_list[name]
            q.get(timeout=timeout)
            return True
        else:
            return False

