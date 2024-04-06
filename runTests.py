import scullery.workers

scullery.workers.start()

import unittest

from tests import testMisc

unittest.main(testMisc, exit=False)
