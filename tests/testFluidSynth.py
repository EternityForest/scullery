import unittest

from scullery import workers
workers.start()

from scullery import fluidsynth
import time

class TestAudio(unittest.TestCase):
            

    def test_fluidsynth_nojack(self):
        fs = fluidsynth.FluidSynth(jackClientName="Foo")
        time.sleep(3)
        print("Testing fluidsynth with JACK")
        print("You should hear a MIDI note. This test require's fluidsynth, pyFluidsynth, and it's default sf2 file")
        fs.noteOn(0,70,50)
        time.sleep(0.5)
        fs.noteOff(0,70)
        fs.setInstrument(0,"flute")
        print("You should hear a flute note")
        fs.noteOn(0,70,70)
        time.sleep(2)
        fs.noteOff(0,70)


