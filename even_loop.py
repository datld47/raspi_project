import threading
import  queue

class Event_Item:
    def __init__(self,fun,arg,kwargs:dict) -> None:
        self.fun_callback=fun
        self.arg=arg
        self.kwargs=kwargs or {}

    def excute(self):
        self.fun_callback(self.arg,**self.kwargs)


class Event_Loop:
    def __init__(self) -> None:
        self.thread = threading.Thread(target=self.run,daemon=True)
        self._stop_event = threading.Event()
        self.queue=queue.Queue()
        self.queue.put(None)
    
    def put_event_item(self,item:Event_Item):
        self.queue.put(item)
    
    def start(self):
        self._stop_event.clear()
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run,daemon=True)
            self.thread.start()
        
    def stop(self):
        self._stop_event.set()
        self.queue.put(None)
        self.thread.join()
        
    def run(self):
        while not self._stop_event.is_set():  
            try:
                item = self.queue.get(30)
                if item is None:
                    continue
                item.excute()
            except queue.Empty:
                continue
            except Exception as e:
                print(f'[EventLoop] Error; {e}')
        