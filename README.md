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




### scullery.iceflow.GstreamerPipeline
This is the base class for making GStreamer apps

#### addElement(elementType, name=None, connectToOutput=None,**kwargs)

Adds an element to the pipe and returns a weakref proxy. Normally, this will connect to the last added
element, but you can explicitly pass a an object to connect to. If the last object is a decodebin, it will be connected when a pad
on that is available.

The `**kwargs` are used to set properties of the element.


#### setProperty(element, property, value)
Set a prop of an element, with some added nice features like converting strings to GstCaps where needed, and checking that filesrc locations are actually
valid files that exist.

#### onMessage(source, name, structure)
Used for subclassing. Called when a message that has a structure is seen on the bus. Source is the GST elemeny, struct is dict-like, and name is a string.

#### play()
If paused, start. If never started, raise an error.

#### start()
Start running

#### stop()

Permanently stop and clean up.

#### pause()

What it sounds like

#### seek(t=None, rate=None)
Seek to a time, set playback rate, or both.




### scullery.jack

This submodule requires pyjack, and of course Jack. You should normally import this somewhere if using IceFlow with JACK.


#### Message Bus activity

##### /system/jack/newport
 A PortInfo object with a .name, isInput, and isOutput property gets posted here whenever a new port is added to JACK.

##### /system/jack/delport
 A PortInfo object gets posted here whenever a port is unregistered.

##### system/jack/started
When jack is started or restarted

 

#### Config:
```
jackPeriods = 3
periodSize = 128

#These apply to soundcards other than the main system card
usbPeriodSize = 384
usbLatency = 384

realtimePriority = 70

#Do we want to run PulseAudio and the pulse jack backend?
usePulse= True

sharePulse = None

#Should we create alsa_in and alsa_out ports for every soundcard, with persistant names?
manageSoundcards = True

#Should we auto restart the jack process?
#No by default, gets auto set to True by startJackServer()
manageJackProcess = False
```


#### sullery.jack.startManaging()
Start the worker thread and enable management functions

#### scullery.jack.startJackServer()
Actually start the jack server. They are separate because you may want to do this yourself.

#### scullery.jack.Airwire(from,to)
Return an Airwire object. This is a declaration that you want to connect two clients or ports and keep them connected.
If you try to connect a client to a single port, all outputs get mixed down. Likewise a port to a client duplicates to all inputs.

They start in the disconnected state.


#### scullery.jack.Airwire.connect()
Connect and stay connected. Even if a client dissapears and comes back. Deleting the Airwire will disconnect.
Note that manually disconnecting may not be undone, to prevent annoyance.

#### scullery.jack.Airwire.disconnect()
Disconnect.




