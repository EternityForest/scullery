

import unittest,gc,time,os,random

from scullery import workers
workers.start()

from scullery import messagebus

def workerTest(extra=0):
    l = []
    def f():
        l.append(1)
    workers.do(f)
    for i in range(200000):
        if l:
            break
        time.sleep(0.00001)
    time.sleep(extra)
    return len(l)



def workerSpam(count=10):
    l = []
    def f():
        l.append(1)
    for i in range(count):
        workers.do(f)

assert(workerTest())

class TestMsgbus(unittest.TestCase):
    def test_sync(self):
        p = []
        def f(t,v):
            p.append((t,v))
        messagebus.subscribe("/test",f)
        messagebus.postMessage("/test","foo",synchronous=True)

        self.assertEqual(p,[('/test','foo')])

    def test_del(self):
        "Test unsubscribing by deleting a function"
        p = []
        def f(v):
            p.append(v)
        messagebus.subscribe("test",f)
        del f
        gc.collect()

        messagebus.postMessage("test","foo",synchronous=True)

        self.assertEqual(p,[])   

    def test_async(self):
        p = []
        def f(v):
            p.append(v)
        messagebus.subscribe("test",f)
        messagebus.postMessage("test","foo")

        s = 100
        while (not p) and s:
            time.sleep(0.01)
            s-=1
        self.assertEqual(p,['foo'])

    def test_Workers(self):
        workerSpam(100)
        self.assertLessEqual(len(workers.workers),workers.maxWorkers)

        for i in range(1000):
            self.assertEqual(workerTest(),1)

        for i in range(100):
            self.assertEqual(workerTest(),1)
            time.sleep(0.001)

        for i in range(1):
            self.assertEqual(workerTest(0.1),2)

        for i in range(100):
            self.assertEqual(workerTest(),1)
            time.sleep(random.random()*0.001)
        
        self.assertLessEqual(len(workers.workers),workers.maxWorkers)

        time.sleep(3)
        #Workers should stop within 1s of inactivity.
        self.assertEqual(len(workers.workers),workers.minWorkers)
