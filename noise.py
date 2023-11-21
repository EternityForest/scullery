import scullery.iceflow
import time


class NoiseWindow(scullery.iceflow.GStreamerPipeline):
    def __init__(self):
        scullery.iceflow.GStreamerPipeline.__init__(self)
        self.add_element("videotestsrc", pattern="snow")
        # self.add_element("autovideosink")
        self.capture = self.add_pil_capture((64, 64))
        self.pd = scullery.iceflow.PresenceDetector(self.capture)


n = NoiseWindow()
n.start()
while 1:
    n.pd.poll()
    time.sleep(1)
p.save("noise.png")
n.stop()
