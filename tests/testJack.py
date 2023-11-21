import gc
import random
import unittest
import time
import os
import scullery.jacktools
import scullery.iceflow
import scullery.workers
scullery.workers.start()


class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self):
        scullery.iceflow.GstreamerPipeline.__init__(self, realtime=False)
        self.sink = self.add_element('audiotestsrc')
        self.sink = self.add_element('jackaudiosink', client_name="JackTest")


# scullery.jacktools.start_managing()

# We call this manually, because we didn't set manageJackProcess
# So it won't actually auto manage the server itself
# scullery.jacktools._startJackProcess()

class TestJackAudio(unittest.TestCase):
    def test_airwire(self):
        p = Player()
        p.start()

        print("You should hear noise")
        aw = scullery.jacktools.Airwire("JackTest", "system")
        aw.connect()
        time.sleep(1)
        print("No more noise")

        del aw
        gc.collect()

        self.assertEqual(len(scullery.jacktools.allConnections), 0)

    def test_fluidsynth_jack(self):
        import scullery.fluidsynth
        fs = scullery.fluidsynth.FluidSynth(
            jack_client_name="fstest", connect_output="system")

        print("You should hear a MIDI note. This test require's fluidsynth, pyFluidsynth, and it's default sf2 file")
        fs.noteOn(0, 70, 50)
        time.sleep(0.5)
        fs.noteOff(0, 70)
        fs.setInstrument(0, "Pizzicato")
        print("You should hear a Pizzicato string note")
        fs.noteOn(0, 70, 70)
        time.sleep(1)
        fs.noteOff(0, 70)

    def test_z_stop(self):
        "Must obviously run last"
        print("Stopping JACK")
        scullery.jacktools.stop_managing()
        scullery.jacktools.stopJackServer()
        print("Stopped JACK")
