# SPDX-FileCopyrightText: Copyright Daniel Dunn
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
This file manages global message bus.  Think of it as an internal version of MQTT.
In fact, the same wildcard syntax as MQTT is supported.

The global subscribe, unsubscribe, and post_message functions run subscribers in
a background thread by default.

"""

import weakref
import threading
import time
import traceback
import logging
import inspect
import types
import copy
from typing import Any
from collections.abc import Callable

import beartype

from . import workers
from collections import defaultdict, OrderedDict

_subscribers_list_modify_lock = threading.RLock()
cachelock = threading.RLock()
# OrderedDict doesn't seem as fast as dict. So I have a cache of the cache
parsecache = OrderedDict()
parsecachecache = {}

log = logging.getLogger("system.messagebus")


def normalize_topic(topic: str) -> str:
    """ "Because some topics are equivalent("/foo" and "foo"), this lets us convert them to the canonical "/foo" representation.
    Note that "/foo/" is not the same as "/foo", because a trailing slash indicates a "directory"."""
    topic = topic.strip()
    if not topic.startswith("/"):
        return "/" + topic
    else:
        return topic


def _shouldReRaiseAttrErr():
    return True


subscriber_error_handlers = []


def _handle_error(f: Callable[..., Any], topic: str, value: Any):
    log.exception("Message bus subscriber error")
    if hasattr(f, "messagebusWrapperFor"):
        f = f.messagebusWrapperFor
    for i in subscriber_error_handlers:
        try:
            i(f, topic, value)
        except Exception:
            print(traceback.format_exc())


def _run_function(f, a):
    return f(*a)


class MessageBus:
    def __init__(self, executor: Callable[..., Any] | None = None):
        """You pass this a function of one argument that just calls its argument.
        Defaults to calling in same thread and ignoring errors.

        If you pass it an executor, the executor must take a
        callable and call it in a background thread.

        """
        if executor == None:

            def do(self, f: Callable[[], Any]):
                try:
                    f()
                except Exception:
                    pass

            self._executor = do
        else:
            self._executor = executor

        self._subscribers = defaultdict(list)
        self._subscribers_immutable = {}

    @beartype.beartype
    def subscribe(self, topic: str, callback: Callable[..., Any]):
        topic = normalize_topic(topic)

        with _subscribers_list_modify_lock:
            wrappedCallback = self._wrap_callback(callback, topic)

            self._subscribers[topic].append(wrappedCallback)
            self._subscribers_immutable = copy.deepcopy(self._subscribers)

    def unsubscribe(self, topic: str, function: Callable[..., Any]):
        "Unsubscribe topic from function"
        try:
            with _subscribers_list_modify_lock:
                target = None
                for j in self._subscribers[topic]:
                    if j.originalFunction() == function:
                        target = j
                if target:
                    self._subscribers[topic].remove(target)
                else:
                    pass
        except Exception:
            print(traceback.format_exc())
        # There is a very slight chance someone will
        # Add something to topic before we delete it but after the test.
        # That would result in a canceled subscription
        # So we use this lock.
        try:
            with _subscribers_list_modify_lock:
                if not self._subscribers[topic]:
                    self._subscribers.pop(topic)
        except AttributeError as e:
            # This try and if statement are supposed to catch nuisiance errors when shutting down.
            if _shouldReRaiseAttrErr():
                raise e

        finally:
            with _subscribers_list_modify_lock:
                self._subscribers_immutable = copy.deepcopy(self._subscribers)

    @staticmethod
    def parse_topic(topic: str) -> set[str]:
        """Parse the topic string into a list of all the different subscriptions
        that could possibly match, including wildcards"""
        global parsecache
        # Since this is a pure function(except the caching itself) we can cache it
        if topic in parsecache:
            return parsecache[topic]

        # Let's cache by the original version of the topic, so we don't have to convert it to the canonical
        oldtopic = topic
        topic = normalize_topic(topic)

        # A topic foo/bar/baz would go to
        # foo, foo/bar, and /foo/bar/baz
        # So we need to make a list like that
        matchingtopics = {"/#"}
        parts = topic.split("/")
        last = ""

        # Add the exact one
        matchingtopics.add(topic)

        for i in parts:
            last += i + "/"
            matchingtopics.add(last + "#")
        parsecache[oldtopic] = matchingtopics
        # Don't let the cache get too big.
        # Getting rid of the oldest should hopefully converge to the most used topics being cached
        if len(parsecache) > 600:
            parsecache.popitem(last=False)
        return matchingtopics

    @beartype.beartype
    def _wrap_callback(self, f: Callable[..., Any], topic: str):
        """return function g that calls f with (topic,message) or just f(topic), depending
        on how many args there are.
         and if errors is true logs the error"""

        args = len(inspect.signature(f).parameters)

        timestamp = time.monotonic()

        try:
            desc = str(f.__name__ + " of " + f.__module__)
        except Exception:
            desc = str(f)

        # Allright, here is how this works.
        # We have to deal with the possibility that, at any time,
        # The callback will cease to exist. That, in fact, is how one unsubscribes.
        # So, we make this here closure that knows the topic, and
        # When the GC goes Om Nom Nom on the function, we get passed the weakref to it.
        # Then we get rid of the empty weakref and if that causes the entire topic
        # To have no subscribers, delete that too in case of memory leak.

        def delsubscription(weakrefobject):
            if time.monotonic() < timestamp - 0.5:
                logging.warning(
                    "Function: "
                    + desc
                    + " was deleted 0.5s after being subscribed.  This is probably not what you wanted."
                )

            try:
                with _subscribers_list_modify_lock:
                    self._subscribers[topic].remove(weakrefobject)
            except Exception:
                pass
            # There is a very slight chance someone will
            # Add something to topic before we delete it but after the test.
            # That would result in a canceled subscription
            # So we use this lock.
            try:
                with _subscribers_list_modify_lock:
                    if not self._subscribers[topic]:
                        self._subscribers.pop(topic)
            except AttributeError as e:
                # This try and if statement are supposed to catch nuisiance errors when shutting down.
                if _shouldReRaiseAttrErr():
                    raise e

            finally:
                with _subscribers_list_modify_lock:
                    self._subscribers_immutable = copy.deepcopy(self._subscribers)

        if isinstance(f, types.MethodType):
            f = weakref.WeakMethod(f, delsubscription)
        else:
            f = weakref.ref(f, delsubscription)

        # Mutable object that gets saved to the closure for keeping track of if we already loggged this
        alreadyLogged = [False]
        if args == 0:

            def g(topic, message, errors, timestamp, annotation):
                try:
                    f2 = f()
                    if f2:
                        f2()
                except Exception:
                    try:
                        if errors:
                            if not alreadyLogged[0]:
                                global _handle_error
                                _handle_error(f2, topic, message)
                            alreadyLogged[0] = True
                    except Exception as e:
                        print("err", e)
        elif args == 2:

            def g(topic, message, errors, timestamp, annotation):
                try:
                    f2 = f()
                    if f2:
                        f2(topic, message)
                except Exception:
                    try:
                        if errors:
                            if not alreadyLogged[0]:
                                global _handle_error
                                _handle_error(f2, topic, message)
                            alreadyLogged[0] = True

                    except Exception as e:
                        print("err", e)
        elif args == 4:

            def g(topic, message, errors, timestamp, annotation):
                try:
                    f2 = f()
                    if f2:
                        f2(topic, message, timestamp, annotation)
                except Exception:
                    try:
                        if errors:
                            if not alreadyLogged[0]:
                                global _handle_error
                                _handle_error(f2, topic, message)
                            alreadyLogged[0] = True

                    except Exception as e:
                        print("err", e)
        elif args == 1:

            def g(topic, message, errors, timestamp, annotation):
                try:
                    f2 = f()
                    if f2:
                        f2(message)
                except Exception:
                    try:
                        if errors:
                            if not alreadyLogged[0]:
                                global _handle_error
                                _handle_error(f2, topic, message)
                            alreadyLogged[0] = True
                    except Exception as e:
                        print("err", e)
        else:
            raise ValueError(
                "Invalid function signature(0,1,2, or 4 args supported, not "
                + str(args)
                + ")"
            )

        # Ref to the weakref so it's easy to check if the function we are wrapping
        # Still exists.
        g.originalFunction = f
        return g

    def _post(self, topic, message, errors, timestamp, annotation, executor=None):
        executor = executor or self._executor

        matchingtopics = self.parse_topic(topic)
        # We can't iterate on anything that could possibly change so we make copies
        d = self._subscribers_immutable
        for i in matchingtopics:
            if i in d:
                # When we find a match, we make a copy of that subscriber list
                x = d[i][:]
                # And iterate the copy
                for f in x:
                    # we call the ref to get its refferent
                    # An error could happen in the subscriber
                    # Or a typeerror could because the weakref has been collected
                    # We ignore both of these errors and move on
                    executor(f, (topic, message, errors, timestamp, annotation))

    def post_message(
        self,
        topic: str,
        message: Any,
        errors: bool = True,
        timestamp: float | None = None,
        annotation: Any = None,
        synchronous: bool = False,
    ):
        # Use the executor to run the post message job
        # To allow for the possibility of it running in the background as a thread
        global _run_function
        topic = normalize_topic(topic)
        try:
            topic = str(topic)
        except Exception:
            raise TypeError("Topic must be a string or castable to a string.")

        timestamp = timestamp or time.monotonic()
        self._post(
            topic,
            message,
            errors,
            timestamp,
            annotation,
            _run_function if synchronous else None,
        )


# Setup the default system messagebus
_bus = MessageBus(workers.do)
subscribe = _bus.subscribe
unsubscribe = _bus.unsubscribe
post_message = _bus.post_message
