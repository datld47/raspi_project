import time
import queue
import threading
import signal
import atexit
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging

class EventDispatcher:

    def __init__(self, max_workers=4,task_timeout=10):

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.event_queue = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.handlers = {}
        self._running = False
        self._stopped=False
        self.task_timeout = task_timeout

        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info('Init EventDispatcher ok')

    def register_handler(self, topic, callback, use_pool=False):
    
        self.handlers[topic] = {
            'callback': callback,
            'use_pool': use_pool
        }

        self.logger.info(f'register {topic} ok')

    def dispatch(self, topic, payload):
     
        handler_info = self.handlers.get(topic, {
            'callback': self.default_handler,
            'use_pool': False
        })
        task = {
            'topic': topic,
            'payload': payload,
            'callback': handler_info['callback'],
            'use_pool': handler_info['use_pool'],
            'timestamp': time.time()
        }
        self.event_queue.put(task)
        
        self.logger.info(f'put {topic} ok')


    def start_loop(self):

        if self._running:
            self.logger.warning("[Dispatcher] Loop already running.")
            return
        
        self.logger.info("[Dispatcher] Event loop started.")

        self._running = True

        while self._running:
            task = self.event_queue.get()
            if task is None:
                break  

           

            callback = task['callback']
            payload = task['payload']
            use_pool = task['use_pool']
            topic = task['topic']
            start = time.time()

            self.logger.info(f"get {topic} ok")

            if use_pool:
                self.logger.info(f"processing {topic} in pool ...")
                future = self.pool.submit(self._run_callback, callback, payload, topic, start)
                try:
                    future.result(timeout=self.task_timeout)
                except TimeoutError:
                    self.logger.error(f"[Dispatcher][TIMEOUT] Task on '{topic}' exceeded {self.task_timeout}s")
                except Exception as e:
                    self.logger.error(f"[Dispatcher][ERROR] Task on '{topic}' raised: {e}")
            else:
                self.logger.info(f"processing {topic} in event loop...")
                self._run_callback(callback, payload, topic, start)

    def _run_callback(self, callback, payload, topic, start_time):
        try:
            callback(payload)
        except Exception as e:
            self.logger.error(f"[ERROR] Callback for {topic} raised error: {e}")
        finally:
            duration = time.time() - start_time
            self.logger.info(f"[Dispatcher] {topic} processed in {duration:.3f}s (pool: {threading.current_thread().name})")

    def default_handler(self, payload):
        self.logger.info(f"[Dispatcher] No handler for topic. Payload: {payload}")

    def _signal_handler(self, sig, frame):
        self.logger.info(f"[Dispatcher] Signal {sig} received.")
        self.stop()
        sys.exit(0)

    def stop(self):

        if self._stopped:
            return

        if not self._running:
            return
            
        self.logger.info("[Dispatcher] Stopping...")
        self._running = False
        self.event_queue.put(None)

        try:
            self.pool.shutdown(wait=True)
            self.logger.info("[Dispatcher] Thread pool shutdown complete.")
        except Exception as e:
            self.logger.error(f"[Dispatcher][ERROR] During shutdown: {e}")
        finally:
            self._stopped = True