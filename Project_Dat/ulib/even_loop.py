import threading
import  queue

class Event_Item:
    def __init__(self,fun,arg,kwargs:dict) -> None:
        self.fun_callback=fun
        self.arg=arg
        self.kwargs=kwargs

class Event_Loop:
    def __init__(self) -> None:
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon=True  
        self._stop_event = threading.Event()
        self.queue=queue.Queue()
        self.queue.put(None)
    
    def put_event_item(self,item:Event_Item):
        self.queue.put(item)
    
    def start(self):
        self._stop_event.clear()
        self.thread.start()
        
    def stop(self):
        self._stop_event.set()
        self.thread.join()
        
    def run(self):
        while not self._stop_event.is_set():  
            try:
                f = self.queue.get(30)
                f.fun_callback(f.arg)
            except:
                pass
        