import unittest
import time
import scullery.mqtt 
import gc

class VirtualServer(unittest.TestCase):
    def test_loop(self):
        d = [0]
        def p(*x):
            print("Got MQTT response:"+str([x]))
            d[0]+=1
        
        scullery.mqtt.testCrashOnce = True
        c = scullery.mqtt.getConnection("localhost",1883,messageBusName="testBusName")
        
        time.sleep(0.2)
        c.subscribe("test", p)
        
        c.publish("test","someData")
        
        time.sleep(1)
        
        self.assertEqual(d[0], 1)


        #Passive connection, all it does is act as a wrapper around the internal message bus, all real MQTT traffic is through
        #the real connection we made above.
        c2 = scullery.mqtt.getConnection("",messageBusName='testBusName')

        d2=[0]
        def p2(*x):
            print("Got MQTT response2:"+str([x]))
            d2[0]+=1
                
        time.sleep(0.2)
        c2.subscribe("test", p2)
        
        c2.publish("test","someData2")
        
        time.sleep(0.2)
        
        self.assertEqual(d2[0], 1)

        c2.close()
        c.close()

        del c2
        del c
        gc.collect()
        gc.collect()

        #Recreate the connection, all subscribers carry over
        c = scullery.mqtt.getConnection("localhost",1883,messageBusName="testBusName")
        time.sleep(1)
        c.publish("test","someData2")
        time.sleep(0.2)
        self.assertEqual(d2[0], 2)

        #Delete the functions. Scullery only weakly references them, so they should just be gone.
        del p
        del p2
        gc.collect()
        gc.collect()

        c.publish("test","someData2")
        time.sleep(0.2)
        self.assertEqual(d2[0], 2)
