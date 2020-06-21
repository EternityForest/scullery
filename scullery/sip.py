
from . thirdparty import baresipy
import weakref
from . import jack
import time

def wrapFunction(f):
    f = weakref.ref(f)

    def f2(*a,**k):
        f(*a,**k)
    return f2


class LocalBareSIP(baresipy.BareSIP):
    def __init__(self,*a, jackSink=None, jackSource=None,**k):
        super().__init__(pwd='', gateway='',*a,**k)
        self.jackSink = jackSink
        self.jackSource = jackSource

        self.useJack = jackSink or jackSource
        self.mostRecentCall = ''
        self.jackName = "baresip"

    def call(self, number):
        self.mostRecentCall= number
        super().call(self,number)

    def handle_incoming_call(self, number):
        time.sleep(0.1)
        self.controller().onIncomingCall(number)
        self.mostRecentCall = number

    def handle_call_established(self):
        if self.useJack:
            self.controller().inJackAirwire = jack.Airwire(self.jackSource, self.jackName)
            self.controller().outJackAirwire = jack.Airwire(self.jackSink, self.jackName)
            self.controller().onIncomingCall(self.mostRecentCall)

    
    def onJackEstablished(self, name):
        if self.useJack:
            self.controller().inJackAirwire = jack.Airwire(self.controller().jackSource, self.jackName)
            self.controller().outJackAirwire = jack.Airwire(self.controller().jackSink, self.jackName)



class SipUserAgent():
    def __init__(self,username, audioDriver="alsa,default", port=5060, jackSource=None, jackSink=None):
        super().__init__()
        self.agent = LocalBareSIP(username, audiodriver=audioDriver, 
            port=port, jackSource=jackSource, jackSink=jackSink,block=False)
        self.agent.controller = weakref.ref(self)
    
    def __del__(self):
        self.agent.quit()

    def call(self,number):
        self.agent.call(number)

    def onIncomingCall(self,number):
        print(number)
        self.accept()
        time.sleep(8)
        self.accept()

    def accept(self):
        self.agent.accept_call()


