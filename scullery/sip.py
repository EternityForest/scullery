import re,os,logging,subprocess,weakref, shutil,threading,uuid, select,time

def readAllSoFar(pipe, retVal=b''): 
  counter = 1024
  while counter:
    x =(select.select([pipe],[],[],0.1)[0])
    if x:   
        retVal+=pipe.read(1)
    else:
        break
    counter -=1
  return retVal

def makePollerThread(a):
    a=weakref.ref(a)
    def f():
        while 1:
            try:
                d = a()
                if d:
                    if not d.poll():
                        break
                else:
                    break
            except:
                logging.exception("Error in SIP manager thread")
    return f
                
                
tmpdir = "/dev/shm/"

class LocalSipAgent():
    def __init__(self, username, audiodriver="alsa", audioport="default",port=5060):
        self.pollf = makePollerThread(self)
        self.pollt = threading.Thread(target=self.pollf,daemon=True)
        self.running= True
    
        self.buf = b''
        
        cnfdir = os.path.join(tmpdir, "ScullerySIP"+str(port))
        self.cnfdir=cnfdir
        try:
            #Remove any existing
            shutil.rmtree(self.cnfdir)
        except:
            pass



        os.mkdir(os.path.join(tmpdir, "ScullerySIP"+str(port)))


        
        self.cnfdir = cnfdir
        #Using the template, create a configuration dir for
        #the baresip instance we are about to make.
        f = os.path.join(os.path.dirname(__file__),"baresip_template")
        
        for i in os.listdir(f):
            with open(os.path.join(f,i)) as fd:
                x  = fd.read()
                
            x=x.replace("USERNAME", username)
            x=x.replace("AUDIODRIVER", audiodriver)
            x=x.replace("AUDIOPORT", audioport)
            x=x.replace("PORT", str(port))

            with open(os.path.join(cnfdir,i),"w") as fd:
                fd.write(x)

        self.p = subprocess.Popen(['baresip','-f', self.cnfdir],stdin=subprocess.PIPE, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
        self.pollt.start()

    def poll(self):
        self.onBytesFromProcess(readAllSoFar(self.p.stdout))
        err = readAllSoFar(self.p.stderr)
        print("err", err)
        
        return self.running


    def __del__(self):
        try:
            self.close()
        except:
            pass

    def close(self):
        self.running =False
        self.process.terminate()
        shutil.rmtree(self.cnfdir)
        

    def onBytesFromProcess(self,b):
        self.buf+=b
        
        if b'\n' in self.buf:
            data, self.buf = self.buf.split(b"\n",1)
            self.onProcessLine(data)
            
    def onProcessLine(self,line):
        print(line)
        if b'terminated' in line or b'closed' in line:
            self.currentcall = None
            
        line= line.decode(errors="replace")
        
        incoming = re.search(r"Incoming call from: (.*?) sip\:(.*?)\@(.*?) \-",line)
        if incoming:
            displayName = incoming.groups(1)
            username = incoming.groups(2)
            hostname = incoming.groups(3)
            self.incoming=(displayName,hostname,username)
            self.onIncomingCall(displayName, username, hostname)
            
            
        evt = re.search(r"received event\: *?\'(.*?)\'", line)
        
        if evt:
            self.onDTMF(evt.groups(0))
            
            
        
    def onDTMF(self, code):
        pass
    
    def onIncomingCall(self, displayName, username, hostname):
        pass
    
    def onCallStart(self,displayName,username,hostname):
        pass
    
    def onCallEnd(self):
        pass
    
    def accept(self):
        self.onCallStart(*self.incoming)
        pass
    
    def reject(self):
        pass
    
    def call(self, other):
        pass
    
    def end(self,other):
        pass


s = LocalSipAgent("danny")

time.sleep(60)