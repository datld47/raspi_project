import threading
import time
from even_loop import Event_Loop,Event_Item

class Soft_Timer:
    def __init__(self,tick=1000) -> None:
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon=True  
        self._stop_event = threading.Event()
        self.fn={}
        self.eventloop=Event_Loop()
        self.tick=tick/1000 
    
    def register(self,name,fun_,arg_,delay_):
        item=Event_Item(fun_,arg_,{"name":name,"delay":delay_,"count":0})
        self.fn[name]=item
    
    def start(self):
        self._stop_event.clear()
        self.thread.start()
        self.eventloop.start()
                    
    def stop(self):
        self._stop_event.set()
        self.thread.join()
        self.eventloop.stop()
    
    def run(self):
        while not self._stop_event.is_set():          
            for f in self.fn.values():
                f.kwargs['count']+=1
                if f.kwargs['count']==f.kwargs['delay']:
                    self.eventloop.put_event_item(f)
                    f.kwargs['count']=0  
            time.sleep(self.tick)
        
    
    