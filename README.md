# scullery

![LGPL](badges/lgpl.png)
![Python](badges/python.png)
![Pytest](badges/pytest.png)
![Pre-commit Badge](badges/pre-commit.png)

Python library that provides some core parts of KaithemAutomation.  It's a general purpose
utility library

* Data persistance
* Internal MQTT-like message bus
* Thread pool workers
* State Machines(With conditions and timers)
* Scheduling, including repeating events
* Media Handling and JACK now moved to [IceMedia](https://github.com/EternityForest/icemedia)

## Intro
See example.py for more details. Also see the equally simple audio and video player.


## Examples
```python
import scullery.workers
"This file demonstrates a lot of scullery's functionality in a small package"

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

#### kaithem.message.post(topic,message, timestamp=None, annotation=None)

Post a message to the internal system-wide message bus.
Message topics are hierarchial, delimited by forward
slashes, and the root directory is /. However /foo is equivalent to
foo.

messages may be any python object at all.

The timestamp will be set to time.monotonic() if it is None.

Annotation is used for sending "extra" or "hidden" metadata, usually for preventing loops. It defaults to None.

#### kaithem.message.subscribe(topic,callback)

Request that function *callback* which must take four arguments(topic,message, timestamp,annotation), two
arguments(topic,message), or just one argument(message) be called whenever a message matching the topic
is posted.

Wildcards follow MQTT subscription rules.

Should the topic end with a slash and a hash, it will also match all
subtopics(e.g. "/foo/#" will match "/foo", "/foo/bar" and
"/foo/anything").

Uncaught errors in the callback are ignored but logged.

You must always maintain a reference to the callback, otherwise, the
callback will be garbage collected and auto-unsubscribed. This is also
how you unsubscribe.


### scullery.units
This module deals with unit conversions.

#### scullery.units.convert(value,from_unit, to_unit)
Try to convert the value, falling back to the (very slow) pint library for less common conversions not natively
supported.

#### scullery.units.si_format_number(value, digits=2)

Format a number like 2000 -> "2k", digits controls max decimal places after.


## Scheduling
Wraps the very simple scheduling module in a way that supports
repeating events, error reporting, and weakref-based cleanup.

## Example
```python
import logging
import sys
import time
import gc
import scullery.scheduling

# Set up logging, for demo purposes
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

@scullery.scheduling.every(1)
def f():
    print("test")

time.sleep(4)

# You could delete f and it would go away, but
# lets close it properly.
# del f
f.unregister()


# Since you can't decorate the class methods
# the same way, we do this

class Foo():
    def __init__(self):
        # Must keep a reference to scheduled
        # Or it will stop
        self.scheduled = scullery.scheduling.every(self.bar,1)

    def bar(self):
        print("test 2")


f = Foo()
time.sleep(3)
# We don't call unregister, so we get a warning.
# f.scheduled.unregister()
del f
# Garbage collect so the deleter runs right away
gc.collect()

# Should stop running because we deleted the class
time.sleep(3)
```

## State Machines


```python
import time
import scullery.statemachines

sm = scullery.statemachines.StateMachine("start")

sm.add_state('start', exit=lambda: print('Exiting start state'))
sm.add_state('state2', enter=lambda: print('Entering state 2'))
sm.add_state('state3', enter=lambda: print('Entering state 3'))

sm.add_rule('start', 'my_event', 'state2')
sm.set_timer('state2', 2, 'state3')

# Event triggered, now we are in state2
# A timer is running in the background.
sm.event('my_event')

time.sleep(3)

# The timer went off, now we are in state 3
# Stateage returns a tuple of state, age
# Where age is how long we've been in that state.
print(sm.stateage)

```

## Rate Limiting(0.17.0 and up)

```python
import scullery.ratelimits

# 1hz average, up to max burst of 50
rl = scullery.ratelimits.RateLimiter(hz=1, burst=50)

for i in range(100):
    # Returns number of credits remaining.
    # They refill at the given hz rate up to the burst limit

    if not rl.limit():
        raise RuntimeError("No rate limiter credits remaining")
```

## snake_compat(0.17.0 and up)

This module converts between snake_case, camelCase, and kebeb-case.

It can do so for one string, or it can make a shallow copy of a dict
with all the keys converted and values untouched.

```python

# Example only, * imports are bad!
from scullery.snake_compat import *

# def camel_to_kebab(s: str) -> str:

# def kebab_to_snake(s: str):

# def snake_to_kebab(s: str):

# def snake_to_camel(s: str):

# def camel_to_snake(s: str):

# def snakify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:


# def kebabify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:

# def camelify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
```