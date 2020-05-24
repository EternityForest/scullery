import scullery.workers
scullery.workers.start()

import unittest

from tests import testMQTT
unittest.main(testMQTT,exit=False)


#WARNING: Plays audio, stops pulse, and generally takes over hte sound
from tests import testJack
unittest.main(testJack,exit=False)


from tests import testAudioPlayback
unittest.main(testAudioPlayback,exit=False)


from tests import testMisc
unittest.main(testMisc,exit=False)


