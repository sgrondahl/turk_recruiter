import threading
import Queue
import tornado.ioloop

class Asynchronizer(object) :
    def __init__(self, callback_transformer = (lambda x : x)) :  
        self.callback_transformer = callback_transformer
        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self.worker)
        self.alive = True
    def register_callback(self, thunk, callback) :
        self.queue.put((thunk, self.callback_transformer(callback)))
    def worker(self) :
        while self.alive :
            thunk, callback = self.queue.get(block=True)
            callback(thunk())
        import Settings
        Settings.logging.info("Async worker... it is dead")
    def run(self) :
        self.thread.start()
    def kill(self) :
        self.alive = False
        self.register_callback((lambda : None), (lambda _ : None))

def in_ioloop(callback) :
    def _callback(r) :
        tornado.ioloop.IOLoop.instance().add_callback(lambda : callback(r))
    return _callback
