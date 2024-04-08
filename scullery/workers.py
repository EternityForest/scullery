# SPDX-FileCopyrightText: Copyright Daniel Dunn
# SPDX-License-Identifier: LGPL-2.1-or-later

import threading
import traceback
import logging
import time
import collections
import random

from typing import Callable, List, Optional, Any

# I'm reserving the system log for a reasonable low-rate log.
# So this is in a separate namespace that shows up elsewhere.
logger = logging.getLogger("workers")

syslogger = logging.getLogger("system")

lastWorkersError = 0
backgroundFunctionErrorHandlers = []


def testLatency():
    start_time = time.monotonic()
    x = [0]

    def f():
        x[0] = time.monotonic()

    do(f)

    while time.monotonic() - start_time < 10:
        time.sleep(0.0001)
        if x[0]:
            return x[0] - start_time
    raise RuntimeError("No response")


spawnLock = threading.RLock()

maxWorkers = 32
minWorkers = 4

shutdownWait = 60
run = True
taskQueue = collections.deque()


def inWaiting():
    return len(taskQueue)


def waitingtasks():
    "Return the number of tasks in the task queue"
    return len(taskQueue)


def handle_errorInFunction(f):
    print("Error in: " + str(f))


def stop():
    global run
    logging.info("Stopping worker threads")
    run = False


def EXIT():
    # Tell all worker threads to stop and wait for them all to finish.
    # If they aren't finished within the time limit, just exit.
    t = time.time()
    stop()
    for i in workers:
        try:
            # All threads total must be finished within the time limit
            workers[i].join(shutdownWait - (time.time() - t))
            # If we try to exit befoe the thread even has time to start or something
        except RuntimeError:
            pass


workers = {}
workersMutable = {}

wakeupHandles = []
wakeupHandlesMutable = []


def testIntegrity():
    with spawnLock:
        assert len(wakeupHandles) == len(workers)


lastStoppedThread = 0


def _makeWorker(e, q, id, fastMode=False):
    # one worker that just pulls tasks from the queue and does them. Errors are caught and
    # We assume the tasks have their own error stuff
    def workerloop():
        global workers
        global lastStoppedThread
        global wakeupHandles

        f = None

        shouldRun = True

        monotonic = time.monotonic

        lastActivity = monotonic()
        pop = taskQueue.pop

        runningState = [True]
        handle = (e, runningState)
        with spawnLock:
            wakeupHandlesMutable.append(handle)
            wakeupHandles = wakeupHandlesMutable[:]

        while run:
            try:
                runningState[0] = True
                # While either our direct  queue or the overflow queue has things in it we do them.
                while len(taskQueue):
                    try:
                        f = pop()
                    except Exception:
                        f = None

                    if f:
                        try:
                            f[0](*f[1])
                            lastActivity = monotonic()
                        except Exception:
                            global lastWorkersError
                            try:
                                if lastWorkersError < monotonic() - 60:
                                    syslogger.exception(
                                        "Error in function. This message is ratelimited, see debug logs for full.\r\nIn "
                                        + f[0].__name__
                                        + " from "
                                        + f[0].__module__
                                        + "\r\n"
                                    )
                                    lastWorkersError = monotonic()

                                logger.exception(
                                    "Error in function running in thread pool "
                                    + f[0].__name__
                                    + " from "
                                    + f[0].__module__
                                )
                            except Exception:
                                print(
                                    "Failed to handle error: " + traceback.format_exc(6)
                                )

                            for i in backgroundFunctionErrorHandlers:
                                try:
                                    i(f)
                                except Exception:
                                    print(
                                        "Failed to handle error: "
                                        + traceback.format_exc(6)
                                    )
                        finally:
                            # We do not want f staying around, if might hold references that should be GCed away immediatly
                            f = None
                # Ensure the lock is acqured so we can sto the next time
                # We try in blocking mode
                e.acquire(False)
                runningState[0] = False

                # This check happens *after* setting e.on false, so that if we
                # set it false right after they checked and put something in
                # the queue we get it next loop
                if not taskQueue:
                    # Randomize, so they don't all sync up
                    # FastMode polls at 100Hz
                    x = e.acquire(
                        timeout=(random.random() * 1) if not fastMode else 0.01
                    )
                    runningState[0] = True

                if not x and not taskQueue:
                    if not shouldRun:
                        return

                    # Fast prelim check.  Allow going below min workers if no activity for 5s
                    # Otherwise stay at min workers
                    if (len(workers) > minWorkers) or (
                        lastActivity < (monotonic() - 5)
                    ):
                        # The elements of handle are never copied anywhere,
                        # Once the list is clear, we can be sure there is no further inserts, and the next round will catch almost
                        # all race conditions. Any remaining one in a million ones will be caught in 1 second
                        if lastActivity < (monotonic() - 1):
                            # This should not block.
                            if spawnLock.acquire(timeout=2):
                                try:
                                    if (len(workers) > minWorkers) or (
                                        lastActivity < (monotonic() - 5)
                                    ):
                                        # Only stop one thread per second to prevent
                                        # chattering

                                        if lastStoppedThread < (monotonic() - 1):
                                            lastStoppedThread = monotonic()
                                            del workersMutable[id]
                                            workers = workersMutable.copy()
                                            wakeupHandlesMutable.remove(handle)
                                            wakeupHandles = wakeupHandlesMutable[:]
                                            return
                                finally:
                                    spawnLock.release()
            except Exception:
                print("Exception in worker loop: " + traceback.format_exc(6))

    return workerloop


def addWorker():
    global workers
    if spawnLock.acquire(timeout=60):
        try:
            q = []
            e = threading.Lock()
            e.acquire()

            id = time.time()
            # First worker always polls at 100hz
            t = threading.Thread(
                target=_makeWorker(e, q, id),
                name="nostartstoplog.ThreadPoolWorker-" + str(id),
            )
            workersMutable[id] = t
            t.start()
            workers = workersMutable.copy()
        finally:
            spawnLock.release()
    else:
        raise RuntimeError("Could not get the lock!")


_append = taskQueue.append


def do(func: Callable[..., Any], args: Optional[List[Any]] = None):
    """Run a function in the background

    funct(function):
        A function of 0 arguments to be ran in the background in another thread immediatly,
    """

    args = args or []
    if not callable(func):
        raise ValueError("Non callable value")

    _append((func, args))

    for i in wakeupHandles:
        try:
            if i[0].locked():
                i[0].release()
                return
        except RuntimeError:
            pass

    if len(workers) > 4:
        # Wait and retry before attempting to spawn a new thread, if there is probable already enough.
        # that is a slow problematic thing
        time.sleep(0.001)
        time.sleep(0.0001)

        for i in wakeupHandles:
            try:
                if i[0].locked():
                    i[0].release()
                    return
            except RuntimeError:
                pass

    # Sleep 1/25000th of a second for every item in the queue past the max number of threads
    # In an attempt to rate limit
    if len(taskQueue) > maxWorkers:
        time.sleep(max(0, (len(taskQueue) - maxWorkers) / 25000))

    # No unbusy threads? It must go in the overflow queue.
    # Soft rate limit here should work a bit better than the old hard limit at keeping away
    # the deadlocks.
    # Under lock

    # We also need this fast preliminary check to use that lock as rarely as possible.
    if len(workers) < maxWorkers:
        if spawnLock.acquire(timeout=15):
            try:
                if len(workers) < maxWorkers:
                    addWorker()
                    return
            finally:
                spawnLock.release()
        else:
            print("COULD NOT GET SPAWN LOCK TO CREATE THREAD. RESTART SUGGESTED")

    # If we can't spawn a new thread
    # Wait a maximum of 15ms before
    # just giving up and leaving
    # it for when somethin
    # wakes up
    for n in range(25):
        if not taskQueue:
            return
        for i in wakeupHandles:
            try:
                if i[0].locked():
                    i[0].release()
                    return
            except RuntimeError:
                pass
        time.sleep(0.0005)


do_try = do


def start(count=12, qsize=64, shutdown_wait=60):
    "Now just sets parameters, threads are made and destroyed on-demand"
    global __queue, run, workers, maxWorkers
    run = True

    maxWorkers = count

    syslogger.info("Started worker threads")
