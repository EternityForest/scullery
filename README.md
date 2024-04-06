# scullery

Python library that provides some core parts of KaithemAutomation, especially things related to media handling.

* Data persistance
* Message bus
* Thread pool worker(At one point, Python did not natively have this, may be deprecated now that it does)

* Media Handling and JACK now moved to IceFlow

## Intro
See example.py for more details. Also see the equally simple audio and video player.


## Examples
```python
import scullery.workers
"This file demonstrates a lot of scullery's functionality in a small package"

#Most things require this thread pool to be running
scullery.workers.start()

#Including just importing this, #Todo?
import scullery.messagebus

import scullery.persist

#Start the gst pipeline
def subscriber(topic,val):

    print("Got a message")

#Unsubscribe happens automatically if we don't keep a ref to the function
scullery.messagebus.subscribe("/test/topic",subscriber)

#Post a message, the actual subscribers all run in the background worker pool
scullery.messagebus.post_message("/test/topic","TestPayload")

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

### scullery.messagebus

#### scullery.messagebus.subscribe(callback,topic)
Subscribe to a topic. Topics are a slash delimited heirarchy,a # at the end is a wildcard,
just like MQTT.


#### scullery.messagebus.subscriberErrorHandlers  = []

List of functions to be called whenever an error happens in a subscribed function.

Signature must be function,topic,value.

If the function has an attribute messagebusWrapperFor, the value of that property is passed instead of the function itself. Any higher level stuff that uses the message bus must set this property when wrapping functions.



### scullery.units
This module deals with unit conversions.

#### scullery.units.convert(value,fromUnit, toUnit)
Try to convert the value, falling back to the (very slow) pint library for less common conversions not natively
supported.
