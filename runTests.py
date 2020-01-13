import scullery.workers
scullery.workers.start()

import unittest


#WARNING: Plays audio, stops pulse, and generally takes over hte sound
from tests import testJack
unittest.main(testJack)


from tests import testAudioPlayback
unittest.main(testAudioPlayback)


from tests import testMisc
unittest.main(testMisc)
