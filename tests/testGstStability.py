import scullery.workers
scullery.workers.start()

import scullery.iceflow
import scullery.fluidsynth

import os,time

import unittest,random,gc

class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self,file):
        scullery.iceflow.GstreamerPipeline.__init__(self,realtime=False)

        self.src = self.addElement('filesrc',location=file)

        #This bin autodetects and decodes basically any type of media
        #It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.addElement('decodebin')


        self.addElement('audioconvert',connectToOutput=decodebin)
        self.addElement('audioresample')

        self.fader = self.addElement('volume', volume=1)
        self.sink = self.addElement('autoaudiosink') 


class TestAudio(unittest.TestCase):

    def test_z_no_segfaults(self):
        #Test for segfault-ery
        for i in range(0,100):
            p=Player(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media","Brothers Unite.ogg"))
            p.start()
            time.sleep(0.1*random.random())
            p.seek(0.3)
            time.sleep(0.1*random.random())
            p.setProperty(p.fader, "volume",1)
            p.stop()
        del p
        gc.collect()
        time.sleep(15)
        gc.collect()

        self.assertEqual(len(scullery.iceflow.pipes), 0)
     