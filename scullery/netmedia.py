import os, subprocess, time,logging,select,threading,sys

log = logging.getLogger("scullery.netmedia")

default_dir = os.path.expanduser("~/Videos/IceFlow Cache/")

audioExtensions = ['.m4a','.ogg','.mp3','.wma','.opus','.flac','.wav']



def cleanupName(n):
    return n.replace("/","slash").replace("\\","backslash").replace(":",".").replace('"','').replace("[","").replace("]",'').replace("-","")

def _readStdout(proc, retVal=b''): 
  counter = 1024
  while counter:
    x =(select.select([proc.stdout],[],[],0.1)[0])
    if x: 
        x=proc.stdout.read(1)
        retVal+=x
        if(x):
            pass#sys.stdout.write(x.decode(errors="ignore"))
    else:
        break
    counter -=1
  return retVal

def downloadVideo(vid, directory=default_dir,format="", timeout=10):
    """Downoad a video by any valid youtube-dl specifier, 
    and return it's filename as soon as it starts. The file will be downloaded into directory.
    
    Should directory already contain a request bty that name, simply return that, with no extra
    network activity.
    """    
    if not os.path.isdir(directory):
        os.mkdir(directory)
    if not os.path.isdir(os.path.join(directory,"searches")):
        os.mkdir(os.path.join(directory,"searches"))
    
    searchfile=os.path.join(directory,"searches",format+"."+cleanupName(vid))

    if os.path.isfile(searchfile):
        with open(searchfile) as f:
            return os.path.join(directory,f.read())


    x = os.listdir(directory)
    log.info("Downloading:",vid)
    cmd = ['youtube-dl',"--no-part"]

    cmd+=["-o",os.path.join(directory,r'%(title)s.%(ext)s')]
    if format:
        cmd += ["-f",format]
    cmd.append(vid)
    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stdin=subprocess.PIPE)
  
    op = b''
    for i in range(0,(int(timeout)*10)):
        op += _readStdout(p)
        time.sleep(0.1)
        for j in os.listdir(directory):
            #Look for the same vid that it's redownloading
            if j.encode("utf8") in op:
                if not os.path.isfile(searchfile):
                    with open(searchfile,"w") as f:
                        f.write(j)
                return os.path.join(directory, j)


            #Look for a file that was not there before
            if not j in x:
                for word in vid.split(" "):
                    #Basic check to ensure it's not unrelated crap
                    if word.lower() in j.lower():
                        #Wait to see if the command fails, if it does, delete the search file.
                        #So we can possibly try again
                        def checkSuccess():
                            if p.wait():
                                os.remove(searchfile)
                        t = threading.Thread(target=checkSuccess)


                        #Keep track of that exact search term, for cache purposes.
                        with open(searchfile,"w") as f:
                            f.write(j)
                        t.start()
                        return os.path.join(directory, j)


    raise RuntimeError("No video found")
