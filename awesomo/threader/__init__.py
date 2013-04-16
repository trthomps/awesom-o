import threading
import Queue

Class Threader(object):
    def __init__(self, numthreads):
        self._numthreads=numthreads

    def get_data(self,):
        raise NotImplementedError, "You must implement get_data as a function that returns an iterable"
        return range(10000)
    def handle_data(self,data):
        raise NotImplementedError, "You must implement handle_data as a function that returns anything"
        time.sleep(random.randrange(1,5))
        return data*data
    def handle_result(self, data, result):
        raise NotImplementedError, "You must implement handle_result as a function that does anything"
        print data, result

    def _handle_data(self):
        while 1:
            x=self.Q.get()
            if x is None:
                break
            self.DQ.put((x,self.handle_data(x)))

    def _handle_result(self):
        while 1:
            x,xa=self.DQ.get()
            if x is None:
                break
            self.handle_result(x, xa)

    def run(self):
        if hasattr(self, "prerun"):
            self.prerun()
        self.Q=Queue.Queue()
        self.DQ=Queue.Queue()
        ts=[]
        for x in range(self._numthreads):
            t=threading.Thread(target=self._handle_data)
            t.start()
            ts.append(t)

        at=threading.Thread(target=self._handle_result)
        at.start()

        try :
            for x in self.get_data():
                self.Q.put(x)
        except NotImplementedError, e:
            print e
        for x in range(self._numthreads):
            self.Q.put(None)
        for t in ts:
            t.join()
        self.DQ.put((None,None))
        at.join()
        if hasattr(self, "postrun"):
            return self.postrun()
        return None
