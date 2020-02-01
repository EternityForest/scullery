#Copyright Daniel Dunn 2013
#This file is part of Kaithem Automation.

#Kaithem Automation is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, version 3.

#Kaithem Automation is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Kaithem Automation.  If not, see <http://www.gnu.org/licenses/>.

#This file manages a work queue that feeds a threadpool
#Tasks will be performed on a best effort basis and errors will be caught and ignored.

import threading,sys,traceback, logging
import atexit,time,collections
import random

#I'm reserving the system log for a reasonable low-rate log.
#So this is in a separate namespace that shows up elsewhere.
logger = logging.getLogger("workers")

syslogger = logging.getLogger("system")

lastWorkersError = 0 
backgroundFunctionErrorHandlers=[]


spawnLock = threading.RLock()

maxWorkers = 32
minWorkers=0

shutdownWait= 60
run=True
taskQueue = collections.deque()

def inWaiting():
    return len(taskQueue)

def waitingtasks():
    "Return the number of tasks in the task queue"
    return len(taskQueue)


def handleErrorInFunction(f):
    print("Error in: " +str(f))

def stop():
    global run
    logging.info("Stopping worker threads")
    run = False

def EXIT():
    #Tell all worker threads to stop and wait for them all to finish.
    #If they aren't finished within the time limit, just exit.
    t = time.time()
    stop()
    for i in workers:
        try:
            #All threads total must be finished within the time limit
            workers[i].join(shutdownWait  - (time.time()-t) )
            #If we try to exit befoe the thread even has time to start or something
        except RuntimeError:
            pass

workers = {}
workersMutable ={}

wakeupHandles = []
wakeupHandlesMutable = []


def testIntegrity():
    with spawnLock:
        assert len(wakeupHandles)==len(workers)

def makeWorker(e,q,id):
    #one worker that just pulls tasks from the queue and does them. Errors are caught and
    #We assume the tasks have their own error stuff
    e.on=True

    def workerloop():
        global workers

        f=None

        shouldRun=True

        lastActivity = time.monotonic()

        with spawnLock:
            wakeupHandlesMutable.append(e)
            wakeupHandles = wakeupHandlesMutable[:]

        while(run):
            try:
                e.on=True
                #While either our direct  queue or the overflow queue has things in it we do them.
                while(len(taskQueue)):
                    try:
                        f=taskQueue.pop()
                    except:
                        f=None

                    if f:
                        try:
                            f[0](*f[1])
                        except Exception:
                            global lastWorkersError
                            try:
                                if lastWorkersError<time.monotonic()-60:
                                    syslogger.exception("Error in function. This message is ratelimited, see debug logs for full.\r\nIn "+f[0].__name__ +" from " + f[0].__module__ +"\r\n")
                                    lastWorkersError= time.monotonic()

                                logger.exception("Error in function running in thread pool "+f[0].__name__ +" from " + f[0].__module__)
                            except:
                                print("Failed to handle error: "+traceback.format_exc(6))

                            for i in backgroundFunctionErrorHandlers:
                                try:
                                    i(f)
                                except:
                                    print("Failed to handle error: "+traceback.format_exc(6))
                        finally:
                            #We do not want f staying around, if might hold references that should be GCed away immediatly
                            f=None
                e.on=False

                e.clear()
                e.wait(timeout=1)


                if not e.is_set():
                    if not shouldRun:
                        return

                    #Fast prelim check. 
                    if len(workers)>minWorkers:
                        #The elements of handle are never copied anywhere,
                        #Once the list is clear, we can be sure there is no further inserts, and the next round will catch almost
                        #all race conditions. Any remaining one in a million ones will be caught in 1 second
                        with spawnLock:
                            if len(workers)>minWorkers:
                                shouldRun=None
                                del workersMutable[id]
                                workers = workersMutable.copy()
                                wakeupHandlesMutable.remove(e)
                                wakeupHandles = wakeupHandlesMutable[:]
            except:
                print("Exception in worker loop: "+traceback.format_exc(6))

    return workerloop



def addWorker():
    global workers
    with spawnLock:
        q = []
        e = threading.Event()
        id = time.time()
        t = threading.Thread(target = makeWorker(e,q,id), name = "ThreadPoolWorker-"+str(id))
        workersMutable[id] = t
        t.start()
        workers = workersMutable.copy()

def do(func,args=[]):
    """Run a function in the background

    funct(function):
        A function of 0 arguments to be ran in the background in another thread immediatly,
    """

    taskQueue.append((func,args))
    for i in wakeupHandles:
        if not i[0].on:
            i[0].set()
            return

    #Sleep 1/100th of a second for every item in the queue past the max number of threads
    #In an attempt to rate limit
    if len(taskQueue)>maxWorkers:
        time.sleep(max(0, (len(taskQueue)-maxWorkers)/100  ))

    #No unbusy threads? It must go in the overflow queue.
    #Soft rate limit here should work a bit better than the old hard limit at keeping away
    #the deadlocks.

    #Under lock
    with spawnLock:
        if len(workers)< maxWorkers:
            addWorker()


    
do_try=do

def start(count=8, qsize=64, shutdown_wait=60):
    global __queue, run,worker_wait,workers, maxWorkers
    run = True
    worker_wait = shutdown_wait
    
    maxWorkers = count
        
    syslogger.info("Started worker threads")
