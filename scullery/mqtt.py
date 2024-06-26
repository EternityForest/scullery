# SPDX-FileCopyrightText: Copyright Daniel Dunn
# SPDX-License-Identifier: LGPL-2.1-or-later

from socket import timeout
import threading
import weakref
import logging
import time
import uuid
import traceback
import json
import asyncio

from scullery import messagebus, workers, util

try:
    import msgpack
except Exception:
    pass

logger = logging.getLogger("system.mqtt")


connections = {}

lock = threading.RLock()

# {server, topic, qos : weakref(f)}

allSubscriptions = {}


# list them by local name.  But only real, phsyical MQTT connections.
# This is how passive connections find their real one
connectionsByBusName = weakref.WeakValueDictionary()


def getWeakrefHandlers(self):
    self = weakref.ref(self)

    def on_connect(client, userdata=None, flags=None, rc=0, *a):
        if not rc == 0:
            self().on_disconnected()
            return

        logger.info(
            "Connected to MQTT server: " + self().server + "result code " + str(rc)
        )
        self().on_still_connected()
        # Don't block the network thread too long

        def subscriptionRefresh():
            try:
                with self().lock:
                    for i in allSubscriptions:
                        # Here the bus prefix is our connection ID
                        if i[0] == self().busPrefix:
                            if allSubscriptions[i]():
                                # Refresh all subscriptions
                                self().connection.subscribe(i[1], i[2])
            except Exception:
                logger.exception("Error subscription refresh")

        workers.do(subscriptionRefresh)

    def on_disconnect(client, *a):
        if not self():
            return
        logger.info("Dis_connected from MQTT server: " + self().server)
        self().on_disconnected()
        logger.info("Dis_connected from MQTT server: " + self().server)

    def on_message(client, userdata, msg):
        try:
            s = self()
            # Everything must be fine, because we are getting messages
            messagebus.post_message(
                s.busPrefix + "/in/" + msg.topic,
                msg.payload,
            )
            s.on_still_connected()
        except Exception:
            print(traceback.format_exc())

    return on_connect, on_disconnect, on_message


# Used to fake a crash fro unit testing purposes


class Connection:
    def __init__(
        self,
        server,
        port=1883,
        password=None,
        message_bus_name=None,
        *,
        alert_priority="info",
        alert_ack=True,
        connection_id=""
    ):
        # connection_id is used to ensure separate *physical* connections and prevent reuse
        self.server = server
        self.port = port
        self.lock = threading.Lock()
        self.password = password

        self.message_bus_name = message_bus_name
        self.connection = None

        # Defensive against None
        connection_id = connection_id or ""

        self.is_connected = False

        if not server:
            passive = True
        else:
            passive = False

        self.passive = passive

        server = server or str(uuid.uuid4())
        virtual = server.startswith("__virtual__")

        if passive and (not message_bus_name):
            raise ValueError(
                "No server specified. To create a passive connection you must specify an internal message_bus_name"
            )
        self.busPrefix = "/mqtt/" + server + \
            ":" + str(port) + (connection_id or "")

        self.subscriptions = {}
        logger.info("Creating connection object to: " + self.server)

        self.localStatusTopic = self.busPrefix + "/connectionStatus"

        # paho requires non-python stuff.
        try:
            import paho.mqtt.client as mqtt

            paho = True

        except ImportError:
            logging.exception(
                "PahoMQTT not installed. No MQTT connection possible here. continuing with dummy."
            )
            paho = False

        # When we wrap a function store a weakref to the original here,
        # Pplus the wrapper, so the wrapper doesn't get GCed till
        # The wearkref callback deletes it.
        self.subscribeWrappers = {}

        with lock:
            if connection_id:
                connection_id = "?" + connection_id
            self.connection_id = connection_id

            n = server + ":" + str(port) + connection_id
            if n in connections and connections[n]():
                raise RuntimeError("There is already a connection")
            torm = []
            for i in connections:
                if not connections[i]():
                    torm.append(i)
            for i in torm:
                del connections[i]
            connections[n] = weakref.ref(self)

            if message_bus_name:
                self.busPrefix = "/mqtt/" + message_bus_name

            try:
                if not virtual and not passive:

                    def out_handler(topic, message, timestamp, annotation):
                        self.connection.publish(
                            topic[len(self.busPrefix + "/out/"):],
                            payload=message,
                            qos=annotation[0],
                            retain=annotation[1],
                        )

                else:
                    if not passive:
                        # Virtual loopback server doesn't actually use a real server
                        def out_handler(topic, message, timestamp, annotation):
                            t = topic[len(self.busPrefix + "/out/"):]
                            messagebus.post_message(
                                self.busPrefix + "/in/" + t, message)

                if not passive:
                    messagebus.subscribe(
                        self.busPrefix + "/out/#", out_handler)
                    self.out_handler = out_handler

                if not virtual and not passive:
                    x = server.split("@")

                    if len(x) == 2:
                        host = x[1]
                        user = x[0]
                    elif len(x) == 1:
                        host = x[0]
                        user = None
                    else:
                        raise ValueError(
                            "More than one @ symbol in server name??")

                    self.username = user
                    self.password = password

                    self.configure_alert(alert_priority, alert_ack)

                else:
                    self.connection = None
                    self.configure_alert(alert_priority, alert_ack)
                    self.on_still_connected()

                if not passive:
                    connectionsByBusName[self.busPrefix] = self

            except Exception:
                # Attempt cleanup
                try:
                    self.connection.disconnect()
                    time.sleep(2)
                except Exception:
                    pass
                try:
                    del connections[server + ":" + str(port)]
                except Exception:
                    pass
                raise

    def on_connection_crash(self, tb):
        print(traceback.format_exc())
        self.reconnect()

    def on_still_connected(self):
        if not self.is_connected:
            messagebus.post_message(self.localStatusTopic, "connected")
        self.is_connected = True
        pass

    def on_disconnected(self):
        logging.warning(
            "A connection has dis_connected from MQTT server: " + self.server
        )
        if self.is_connected:
            messagebus.post_message(self.localStatusTopic, "dis_connected")
        self.is_connected = False

    def subscribe_to_status(self, f):
        messagebus.subscribe(self.localStatusTopic, f)

    def close(self):
        # Attempt cleanup
        try:
            self.connection.disconnect()
        except Exception:
            pass
        try:
            del connections[self.server + ":" +
                            str(self.port) + self.connection_id]
        except Exception:
            pass

    def __del__(self):
        if self.connection:
            self.connection.disconnect()

    def unsubscribe(self, topic, function):
        with self.lock:
            # Very expensive to search this dict like this, but unsub shouldn't happen much.
            try:
                torm = []
                # Find any subscriptions to the topic for this particular bus prefix and delete them
                for i in allSubscriptions:
                    if (
                        i[0] == self.busPrefix
                        and i[1] == topic
                        and allSubscriptions[i]() == function
                    ):
                        torm.append(i)
                for i in torm:
                    allSubscriptions.pop(i)
            except KeyError:
                print(traceback.format_exc())
                pass

            torm = []
            for i in self.subscribeWrappers:
                x = self.subscribeWrappers[i]
                if x[2] == topic and (x[0]() == function or x[0]() is None):
                    messagebus.unsubscribe(x[3], x[1])
                    torm.append(i)
            for i in torm:
                try:
                    del self.subscribeWrappers[i]
                except KeyError:
                    pass

            for i in self.subscribeWrappers:
                x = self.subscribeWrappers[i]
                if x[2] == topic:
                    return

            # We could not find even a single subscriber function
            # So we unsubscribe at the MQTT level
            logging.debug("MQTT Unsubscribe from " +
                          topic + " at " + self.server)
            if self.connection:
                self.connection.unsubscribe(topic)

    def configure_alert(self, *a):
        pass

    def _mqttSubscribe(topic, qos):
        if self.connection:
            self.connection.subscribe(topic, qos)

    def subscribe(self, topic, function, qos=2, encoding="json"):
        with lock:
            if self.connection:
                self.connection.subscribe(topic, qos)
            else:
                # We are a "Passive" connecytion relaying through a real connection elsewhere in code.
                if self.passive:
                    if self.busPrefix in connectionsByBusName:
                        try:
                            backend = connectionsByBusName[self.busPrefix]
                        except KeyError:
                            backend = None

                        if backend:
                            # The backend to relay through actually exists! So we have to actually tell them to physically
                            # subscribe to the MQTT topic.

                            # if they don't exist yet that is fine, they will look through the subscriptions master list and reconnect anything active anyway
                            backend.connection.subscribe(topic, qos)

        x = str(uuid.uuid4())

        def handleDel(*a):
            try:
                del self.subscribeWrappers[x]
            except KeyError:
                pass
            # We're really just using the "check if there's no subscribers"
            # Part of the function
            self.unsubscribe(topic, None)

        fID = id(function)
        function = util.universal_weakref(function, handleDel)

        # This is our master list of who is subscribed where. It is used for reconnection.
        # It is also used so that subscriptions can persist beyond any given connection object!!!
        # use fID in case of two subscribers to one topic needing to fit in one dict.
        with self.lock:
            allSubscriptions[self.busPrefix, topic, qos, fID] = function

        # Connection.subscribe was blocking forever.
        # Use a different thread, to hopefully avoid deadlocks

        def backgroundSubscribeTask():
            with self.lock:
                self.connection.subscribe(topic, qos)

        if encoding == "json":

            def wrapper(t, m):
                # Get rid of the extra kaithem framing part of the topic
                t = t[len(self.busPrefix + "/in/"):]
                if not isinstance(m, str):
                    m = m.decode("utf-8")
                try:
                    m = json.loads(m)
                except Exception:
                    logging.debug("Bad JSON:" + m[:64])
                function()(t, m)

        elif encoding == "msgpack":

            def wrapper(t, m):
                # Get rid of the extra kaithem framing part of the topic
                t = t[len(self.busPrefix + "/in/"):]
                function()(t, msgpack.unpackb(m, raw=False))

        elif encoding == "utf8":

            def wrapper(t, m):
                # Get rid of the extra kaithem framing part of the topic
                t = t[len(self.busPrefix + "/in/"):]
                if not isinstance(m, str):
                    m = m.decode("utf-8")
                function()(t, m)

        elif encoding == "raw":

            def wrapper(t, m):
                # Get rid of the extra kaithem framing part of the topic
                t = t[len(self.busPrefix + "/in/"):]
                function()(t, m)

        else:
            raise ValueError("Invalid encoding: " + encoding)

        # Correctly call message bus error handlers
        wrapper.messagebusWrapperFor = function

        internalTopic = self.busPrefix + "/in/" + topic

        # Extra data is mostly used for unsubscription
        self.subscribeWrappers[x] = (function, wrapper, topic, internalTopic)

        # logging.debug("MQTT subscribe to " + topic + " at " + self.server)
        # Ref to f exists as long as the original does because it's kept in subscribeWrappers
        messagebus.subscribe(internalTopic, wrapper)

        # Important we do this *after*, because the server might auto-send us something that could be important for.
        # Only the first function will get it, but whatever, at least we can see certain things when manually subscribing, for test purposes.
        # Or should we do it before, to resolve that bit of ambiguity and never get the message???
        if self.connection:
            workers.do(backgroundSubscribeTask)

    def publish(self, topic, message, qos=2, encoding="json", retain=False):
        if encoding == "json":
            message = json.dumps(message)
        elif encoding == "msgpack":
            message = msgpack.packb(message, use_bin_type=True)
        elif encoding == "utf8":
            message = message.encode("utf8")
        elif encoding == "raw":
            pass
        else:
            raise ValueError("Invalid encoding!")
        messagebus.post_message(
            self.busPrefix + "/out/" + topic, message, annotation=(qos, retain)
        )


def get_connection(
    server,
    port=1883,
    password=None,
    message_bus_name=None,
    *,
    alert_priority="info",
    alert_ack=True,
    connection_id=""
):
    # Kaithem is gonna monkeypatch kaithem with one that has better
    # logging
    global Connection

    # Blank password means no password
    password = password or None
    with lock:
        x = None

        connection_idSuffix = ""
        if connection_id:
            connection_idSuffix = "?" + connection_id

        if server + ":" + str(port) + connection_idSuffix in connections:
            x = connections[server + ":" + str(port) + connection_idSuffix]()

        if x:
            if not message_bus_name == x.message_bus_name:
                # We can safely use the existing one.   If t
                logging.warning(
                    "Using connection that already exists, but with a different message bus name:  "
                    + x.message_bus_name
                )

                message_bus_name = x.message_bus_name

            if x.password or password:
                if not x.password == password:
                    raise ValueError(
                        "There is already a connection to the same host and user, but with a different password."
                    )

            x.configure_alert(alert_priority, alert_ack)
            return x

        return Connection(
            server,
            port,
            password=password,
            alert_ack=True,
            alert_priority="info",
            message_bus_name=message_bus_name,
            connection_id=connection_id,
        )
