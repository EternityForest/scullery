# scullery
Python library for things like media playback, thread pools, and a message bus. It is essentially the parts of KaithemAutomation
that make sense independantly.

There is a lot of functionality planned, but it's not at all neccesary to use or understand all of it to use one piece.


## Intro
See example.py for more details. 

## Examples
```python
import scullery.iceflow
import scullery.workers


"This file demonstrates a lot of scullery's functionality in a small package"

#Most things require this thread pool to be running
scullery.workers.start()

#Including just importing this, #Todo?
import scullery.messagebus

class NoiseWindow(scullery.iceflow.GstreamerPipeline):
	def __init__(self):
		scullery.iceflow.GstreamerPipeline.__init__(self)
		self.addElement("videotestsrc",pattern="snow")
		self.addElement("autovideosink")
		
n = None
#Start the gst pipeline
def subscriber(topic,val):
    #Prevent GC
    global n
    n=NoiseWindow()
    n.start()
    print("started")
    
#Unsubscribe happens automatically if we don't keep a ref to the function
scullery.messagebus.subscribe("/test/topic",subscriber)

#Post a message, the actual subscribers all run in the background worker pool
scullery.messagebus.postMessage("/test/topic","TestPayload")

import time
while(1):
    time.sleep(1)
```
