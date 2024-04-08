import unittest
import time
import random

from scullery import workers


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
        time.sleep(random.random() * 0.05)
        l.append(1)

    for i in range(count):
        workers.do(f)


assert workerTest()


class TestWorkers(unittest.TestCase):
    def test_Workers(self):
        workers.start(8)

        workerSpam(100)
        self.assertLessEqual(len(workers.workers), workers.maxWorkers)
        self.assertGreaterEqual(len(workers.workers), workers.minWorkers + 2)

        for i in range(10):
            self.assertEqual(workerTest(), 1)

        for i in range(10):
            self.assertEqual(workerTest(), 1)
            time.sleep(0.001)

        for i in range(1):
            self.assertEqual(workerTest(0.1), 1)

        for i in range(100):
            self.assertEqual(workerTest(), 1)
            time.sleep(random.random() * 0.001)

        self.assertLessEqual(len(workers.workers), workers.maxWorkers)

        time.sleep(3)
        self.assertGreaterEqual(len(workers.workers), workers.minWorkers)

        for i in range(25):
            if workers.workers:
                time.sleep(1)
        # Workers should stop within 3s of inactivity, but we can only stop one at a time
        # every seconds
        self.assertEqual(len(workers.workers), 0)
