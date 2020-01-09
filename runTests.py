import scullery.workers
scullery.workers.start()

import unittest


from tests import testAudioPlayback

unittest.main(testAudioPlayback)
