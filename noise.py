import scullery.iceflow
import time

class NoiseWindow(scullery.iceflow.GStreamerPipeline):
	def __init__(self):
		scullery.iceflow.GStreamerPipeline.__init__(self)
		self.addElement("videotestsrc",pattern="snow")
		#self.addElement("autovideosink")
		self.capture = self.addPILCapture((64,64))
		self.pd = scullery.iceflow.PresenceDetector(self.capture)

n=NoiseWindow()
n.start()
while 1:
	n.pd.poll()
	time.sleep(1)
p.save("noise.png")
n.stop()