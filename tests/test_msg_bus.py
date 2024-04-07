from scullery import messagebus
import unittest
import gc
import time


class TestMsgbus(unittest.TestCase):
    def test_sync(self):
        p = []

        def f(t, v):
            p.append((t, v))

        messagebus.subscribe("/test", f)
        messagebus.post_message("/test", "foo", synchronous=True)

        self.assertEqual(p, [("/test", "foo")])

    def test_del(self):
        "Test unsubscribing by deleting a function"
        p = []

        def f(v):
            p.append(v)

        messagebus.subscribe("test", f)
        del f
        gc.collect()

        messagebus.post_message("test", "foo", synchronous=True)

        self.assertEqual(p, [])

    def test_async(self):
        p = []

        def f(v):
            p.append(v)

        messagebus.subscribe("test", f)
        messagebus.post_message("test", "foo")

        s = 100
        while (not p) and s:
            time.sleep(0.01)
            s -= 1
        self.assertEqual(p, ["foo"])
