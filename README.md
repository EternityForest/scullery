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



### scullery.messagebus

#### scullery.messagebus.subscribe(callback,topic)
Subscribe to a topic. Topics are a slash delimited heirarchy,a # at the end is a wildcard,
just like MQTT.


#### scullery.messagebus.subscriberErrorHandlers  = []

List of functions to be called whenever an error happens in a subscribed function.

Signature must be function,topic,value.

If the function has an attribute messagebusWrapperFor, the value of that property is passed instead of the function itself. Any higher level stuff that uses the message bus must set this property when wrapping functions.

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
```python

#Only relevant if manageJackProcess is True
jackPeriods = 3
periodSize = 128

#These apply to soundcards other than the main system card
usbPeriodSize = 384
usbLatency = 384

realtimePriority = 70

#Do we want to run PulseAudio and the pulse jack backend?
#Note that we automatically kill any pulseaudio process we find before
usePulse= True

sharePulse = None

#Should we create alsa_in and alsa_out ports for every soundcard, with persistant names?
manageSoundcards = True

#Should we start the jack process itself, and auto restart it?
#If False, we just try to use an existing one.
#Must set this to True before calling startManaging!
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

### scullery.mqtt

#### scullery.mqtt.getConnection(server, port=1883, password=None, messageBusName=None)

Creates an MQTT connection. To speify username, use user@server.net syntax.

To use an internal fake server for testing, use the server "__virtual__".

This connection handles automatically reconnecting and resubscribing for you.  If a connection to a user@server already exists,
it will return that connection.  

All traffic goes through the internal message bus first, on topics that will begin with /mqtt/. Normally, the internal name is server+":"+port
But you can specify it explicitly.  The topic name also acts as a sort of internal ID, and the system understands new connections with the same ID
to be replacements for the old one. All subscriptions will carry over.

Resubscriptions are stored in a master list.  If you subscribe, then delete the connection and recreate a new connection with the same message bus
name, everything will carry on like nothing happened, so long as you kept a reference to the subscribed function.

You can even create one connection, delete it, make a new one with the same internal messageBusName, to a different server, and all the old subscriptions
will be "remade" at the new server, as the system knows that the new connection is a "replacement" for the old name.

You cannot have two connections to the same user@server combo with different internal names or passwords, however, if you do not supply a password,
and the existing connection has one, it will still work as it is simply returning the existing one.

This feature is meant to make GUI config easier, so that changing a connection doesn't break all existing users of that connection.

##### Passive connections

If server is '', it will not create any real connections, but will still publish and subscribe to the internal
bus, meaning that you can use it as a "passive" connection which uses a real connection configured elsewhere.

Note that you will(currently) only recieve through passives if the backend also subscribed to that topic, subscribing through a passive
connecting is truly passive, but this may change. At the moment, think of them like "spy" connections.

To use a passive connection, you obviously need to specify the same messageBusName on the passive and backend.

##### MQTTConnection.publish(self, topic, message, qos=2, encoding="json"):

Encoding may be: json,msgpack, raw, utf8

##### MQTTConnection.subscribe(self, topic, function, qos=2, encoding="json")
Function is passed f(topic,message). 

Scullery only weakly references, so if you delete or otherwise let the function be GCed, it is auto unsubscribed.

##### MQTTConnection.unsubscribe(self, topic, function)
Automatically unsubscribes from the actual MQTT topic when there are no more local subscribers. Note that subscriptions through a "