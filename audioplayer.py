import scullery.workers
scullery.workers.start()

import scullery.iceflow
import sys

class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self,file):
        #Systemtime only applies to seekable pipes. Tries to keep it running at the system time rate. If it drifts, you may getCaps
        #Ugly pauses, but that may be better than getting out of sync.
        scullery.iceflow.GstreamerPipeline.__init__(self,realtime=None,systemTime=True)

        self.src = self.addElement('filesrc',location=file)

        #This bin autodetects and decodes basically any type of media
        #It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.addElement('decodebin')


        self.addElement('audioconvert',connectToOutput=decodebin)
        self.addElement('audioresample')

        self.fader = self.addElement('volume', volume=1)
        self.sink = self.addElement('autoaudiosink') 

    def onMessage(self,src,name,structure):
        print("Got Message: "+name+" from "+str(src))


p=Player(sys.argv[1])
p.start()

p.setProperty(p.fader, "volume",1)
