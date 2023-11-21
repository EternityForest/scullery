
import os
import time
import scullery.persist
import scullery.messagebus
import scullery.iceflow
import scullery.workers


"This file demonstrates a lot of scullery's functionality in a small package"

# Most things require this thread pool to be running
scullery.workers.start()

# Including just importing this, #Todo?

myData = [1, 2, 3]


class NoiseWindow(scullery.iceflow.GstreamerPipeline):
    def __init__(self):
        scullery.iceflow.GstreamerPipeline.__init__(self)
        self.add_element("videotestsrc", pattern="snow")
        self.add_element("autovideosink")

    def onMessage(self, src, name, structure):
        print("Got Message: "+name+" from "+str(src))


n = None
# Start the gst pipeline


def subscriber(topic, val):
    # Prevent GC
    global n
    n = NoiseWindow()
    n.start()
    print("started")


# Unsubscribe happens automatically if we don't keep a ref to the function
scullery.messagebus.subscribe("/test/topic", subscriber)

# Post a message, the actual subscribers all run in the background worker pool
scullery.messagebus.post_message("/test/topic", "TestPayload")


# Also supports YAML, txt, bin for the appropriate datatypes, if the YAML lib is there.
# Can use .gz or .b2z to compress. Saved atomically with tilde files and UNIX rename semantics.
# Checks if it actually needs to save before actually writing the file.
# Get an abs path
fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testFile.json")
print("Going to save data to: "+fn)
scullery.persist.save(myData, fn)
assert scullery.persist.load(fn) == myData

while (1):
    time.sleep(1)
