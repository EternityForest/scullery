import scullery.workers
scullery.workers.start()

import scullery.iceflow
import sys

class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self,file):
        scullery.iceflow.GstreamerPipeline.__init__(self)

        self.src = self.addElement('filesrc',location=file)

        #This bin autodetects and decodes basically any type of media
        #It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.addElement('decodebin')


        self.addElement('audioconvert',connectToOutput=decodebin)
        self.addElement('audioresample')

        self.fader = self.addElement('volume', volume=1)
        self.sink = self.addElement('autoaudiosink') 




p=Player(sys.argv[1])
p.start()

p.setProperty(p.fader, "volume",1)