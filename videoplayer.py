import sys
import scullery.iceflow
import scullery.workers
scullery.workers.start()


class Player(scullery.iceflow.GstreamerPipeline):
    def __init__(self, file):
        scullery.iceflow.GstreamerPipeline.__init__(self)

        self.src = self.add_element('filesrc', location=file)

        # This bin autodetects and decodes basically any type of media
        # It is special cased, anything onnected to it is actually connected on-demand as needed
        decodebin = self.add_element('decodebin')

        # We have tell it explicitly what type of connection it should be trying to make dynamically,
        # So it doesn't link the audio to the video pads and make annoying messages
        self.add_element('audioconvert', connectToOutput=decodebin,
                         connectWhenAvailable="audio")
        self.add_element('audioresample')

        self.fader = self.add_element('volume', volume=1)
        self.sink = self.add_element('autoaudiosink')

        # Here we see the pipeline is no longer just linear, we branch into audio and video
        conv = self.add_element(
            'videoconvert', connectToOutput=decodebin, connectWhenAvailable="video")
        self.add_element('autovideosink', connectToOutput=conv)


p = Player(sys.argv[1])
p.start()

p.set_property(p.fader, "volume", 1)
