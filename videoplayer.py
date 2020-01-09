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

        #We have tell it explicitly what type of connection it should be trying to make dynamically,
        #So it doesn't link the audio to the video pads and make annoying messages
        self.addElement('audioconvert',connectToOutput=decodebin, connectWhenAvailable="audio")
        self.addElement('audioresample')

        self.fader = self.addElement('volume', volume=1)
        self.sink = self.addElement('autoaudiosink')

        #Here we see the pipeline is no longer just linear, we branch into audio and video
        conv = self.addElement('videoconvert',connectToOutput=decodebin,connectWhenAvailable="video")
        self.addElement('autovideosink',connectToOutput=conv)


p=Player(sys.argv[1])
p.start()

p.setProperty(p.fader, "volume",1)
