import scullery.workers
scullery.workers.start()

import scullery.iceflow
import scullery.jack

import os,time

import unittest,random,gc

class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self):
        scullery.iceflow.GstreamerPipeline.__init__(self,realtime=False)

        self.sink = self.addElement('audiotestsrc') 

        self.sink = self.addElement('jackaudiosink',client_name="JackTest") 



scullery.jack.startManaging()
scullery.jack.startJackServer()

class TestJackAudio(unittest.TestCase):
    def test_airwire(self):
        p=Player()
        p.start()
        
        print("You should hear noise")
        aw =scullery.jack.Airwire("JackTest","system")
        aw.connect()
        time.sleep(1)
        print("No more noise")
        
        del aw
        gc.collect()
        
        self.assertEqual(len(scullery.jack.allConnections), 0)
            
    def test_z_stop(self):
        "Must obviously run last"
        scullery.jack.stopManaging()
        scullery.jack.stopJackServer()

            





