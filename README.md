# scullery
Python library for things like media playback, thread pools, and a message bus. It is essentially the parts of KaithemAutomation
that make sense independantly.

There is a lot of functionality planned, but it's not at all neccesary to use or understand all of it to use one piece.

You will obviously need the Python Gstreamer bindings for those features(but not unrelated features), and several other
dependancies.

## Intro
See example.py for more details. Also see the equally simple audio and video player.

## Examples
```python
import scullery.iceflow
import scullery.workers


"This file demonstrates a lot of scullery's functionality in a small package"

#Most things require this thread pool to be running
scullery.workers.start()

#Including just importing this, #Todo?
import scullery.messagebus

import scullery.persist



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

#Also supports YAML, txt, bin for the appropriate datatypes, if the YAML lib is there.
#Can use .gz or .b2z to compress. Saved atomically with tilde files and UNIX rename semantics.
#Checks if it actually needs to save before actually writing the file.
import os
#Get an abs path
fn = os.path.join(os.path.dirname(os.path.abspath(__file__)),"testFile.json")
print("Going to save data to: "+fn)
scullery.persist.save(myData,fn)
assert scullery.persist.load(fn)==myData



while(1):
    time.sleep(1)
```
