import unittest
import time

from scullery import scheduling


class TestScheduler(unittest.TestCase):
    def test_scheduler(self):
        c = [0]

        @scheduling.every(1)
        def f():
            c[0] += 1

        time.sleep(1.5)
        assert c[0] > 0
        assert c[0] < 3

        time.sleep(1.5)
        assert c[0] > 1
        assert c[0] < 4

        f.unregister()
        x = c[0]

        time.sleep(2)

        assert x == c[0]
