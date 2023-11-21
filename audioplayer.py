import sys
import scullery.iceflow
import scullery.workers
scullery.workers.start()


class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self, file):
        # Systemtime only applies to seekable pipes. Tries to keep it running at the system time rate. If it drifts, you may getCaps
        # Ugly pauses, but that may be better than getting out of sync.
        scullery.iceflow.GstreamerPipeline.__init__(
            self, realtime=None, systemTime=True)

        self.src = self.add_element('filesrc', location=file)

        # This bin autodetects and decodes basically any type of media
        # It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.add_element('decodebin')

        self.add_element('audioconvert', connectToOutput=decodebin)
        self.add_element('audioresample')

        self.fader = self.add_element('volume', volume=1)
        self.sink = self.add_element('autoaudiosink')

    def onMessage(self, src, name, structure):
        print("Got Message: "+name+" from "+str(src))


p = Player(sys.argv[1])
p.start()

p.set_property(p.fader, "volume", 1)
