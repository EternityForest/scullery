# scullery
Python library for things like media playback, thread pools, and a message bus. It is essentially the parts of KaithemAutomation
that make sense independantly.

There is a lot of functionality planned, but it's not at all neccesary to use or understand all of it to use one piece.

You will obviously need the Python Gstreamer bindings for those features(but not unrelated features), and several other
dependancies.

## Intro
See example.py for more details. Also see the equally simple audio and video player.

## Testing
Warning, takes over audio, starts JACK, makes noise:python3 -m unittest discover tests

Running just one test suite: python3 -m unittest tests/testFluidSynth.py
8
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



class NoiseWindow(scullery.iceflow.GStreamerPipeline):
	def __init__(self):
		scullery.iceflow.GStreamerPipeline.__init__(self)
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




### scullery.iceflow.GStreamerPipeline
This is the base class for making GStreamer apps

#### addElement(elementType, name=None, connectToOutput=None,**kwargs)

Adds an element to the pipe and returns a weakref proxy. Normally, this will connect to the last added
element, but you can explicitly pass a an object to connect to. If the last object is a decodebin, it will be connected when a suitable pad
on that is available.

The `**kwargs` are used to set properties of the element.

#### addPILCapture(resolution, connectToOutput=None,buffer=1)
Adds a PILCapture object which acts like a video sink. It will buffer the most recent N frames, discarding as needed.

##### PILCapture.pull()
Return a video frame as a PIL/Pillow Image. May return None on empty buffers.

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

#### isActive()

Return True if playing or paused

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



### scullery.fluidsynth

This module deals with MIDI synthesis

### scullery.fluidsynth.FluidSynth(self, soundfont=None,jackClientName=None)

Creates an instance of the FluidSynth soundfont synthesizer. Soundfont is an file path, or it defaults
to one that sometimes ships with fluidsynth. if jackClientName is provided, outputs audio via JACK.

You don't have to worry about cleanup, that happens automatically on GC.

Using this without JACK may not work.

#### fs.noteOn(channel,note,velocity)
#### fs.noteOff(channel,note)
#### fs.setInstrument(channel,instrument)
Set the instrumemt. If instrument is str, we will use the closest match we can find, or raise an error.


### scullery.units
This module deals with unit conversions.

#### scullery.units.convert(value,fromUnit, toUnit)
Try to convert the value, falling back to the (very slow) pint library for less common conversions not natively
supported.

### scullery.netmedia

#### scullery.netmedia.downloadVideo(vid, directory="~/Videos/IceFlow Cache", format="bestvideo", timeout=10)

Download a video based on a youtube-dl specifier, in the given format("bestaudio") for audio only, and try to return the filename the moment the download begins.


Nothing else should ever be writing to this cache dir, aside from maybe manually putting in videos.