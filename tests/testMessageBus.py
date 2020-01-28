

import unittest,gc,time

from scullery import workers
workers.start()

from scullery import messagebus


class TestJackAudio(unittest.TestCase):
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

        self.assertEqual(p,['foo'])
            
