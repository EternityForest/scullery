import gc
import random
import unittest
import time
import os
import scullery.fluidsynth
import scullery.iceflow
import scullery.workers
scullery.workers.start()


class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self, file):
        scullery.iceflow.GstreamerPipeline.__init__(self, realtime=False)

        self.src = self.add_element('filesrc', location=file)

        # This bin autodetects and decodes basically any type of media
        # It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.add_element('decodebin')

        self.add_element('audioconvert', connectToOutput=decodebin)
        self.add_element('audioresample')

        self.fader = self.add_element('volume', volume=1)
        self.sink = self.add_element('autoaudiosink')


class TestAudio(unittest.TestCase):

    def test_z_no_segfaults(self):
        # Test for segfault-ery
        for i in range(0, 100):
            p = Player(os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "media", "Brothers Unite.ogg"))
            p.start()
            time.sleep(0.01*random.random())
            p.seek(0.3)
            time.sleep(0.01*random.random())
            p.set_property(p.fader, "volume", 0.1)
            p.stop()
            # Ensure nothing bad happens setting the volume after stopping
            p.set_property(p.fader, "volume", 1)
            del p
            gc.collect()
        for i in range(150):
            time.sleep(0.1)
            if len(scullery.iceflow.pipes) == 0:
                break
        gc.collect()

        self.assertEqual(len(scullery.iceflow.pipes), 0)

    def test_seekpastend(self):
        p = Player(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "media", "Brothers Unite.ogg"))
        p.start()
        time.sleep(0.01*random.random())
        p.seek(99999)
        time.sleep(0.01*random.random())
        p.set_property(p.fader, "volume", 1)
        p.stop()
        # Ensure nothing bad happens setting the volume after stopping
        p.set_property(p.fader, "volume", 1)
        del p
        gc.collect()
        for i in range(150):
            time.sleep(0.1)
            if len(scullery.iceflow.pipes) == 0:
                break
        gc.collect()

        self.assertEqual(len(scullery.iceflow.pipes), 0)
