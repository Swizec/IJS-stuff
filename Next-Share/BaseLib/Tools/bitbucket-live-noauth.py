import sys
import time
import random
import tempfile
from traceback import print_exc
from base64 import encodestring

from BaseLib.Core.API import *

DEBUG = True

RATE=32768

def vod_event_callback(d,event,params):
    if event == VODEVENT_START:
        stream = params["stream"]

        grandtotal = 0L
        st = time.time()
        while True:
            global RATE
            total = 0
            while total < int(RATE):
                data = stream.read(int(RATE))
                total += len(data)
                
            grandtotal += total
            et = time.time()
            diff = max(et - st,0.00001)
            grandrate = float(grandtotal) / diff
            print >>sys.stderr,"bitbucket: grandrate",grandrate,"~",RATE,"avail",stream.available()
            time.sleep(1.0)

def state_callback(ds):
    try:
        d = ds.get_download()
        p = "%.0f %%" % (100.0*ds.get_progress())
        dl = "dl %.0f" % (ds.get_current_speed(DOWNLOAD))
        ul = "ul %.0f" % (ds.get_current_speed(UPLOAD))
        print >>sys.stderr,dlstatus_strings[ds.get_status() ],p,dl,ul,"====="
    except:
        print_exc()

    return (1.0,False)


print "Loading",sys.argv
statedir = tempfile.mkdtemp()
port = random.randint(10000,20000)

scfg = SessionStartupConfig()
scfg.set_state_dir(statedir) 
scfg.set_listen_port(port)
scfg.set_megacache( False )
scfg.set_overlay( False )



s = Session( scfg )
tdef = TorrentDef.load(sys.argv[1])
RATE = tdef.get_bitrate()

dscfg = DownloadStartupConfig()
dscfg.set_video_event_callback( vod_event_callback )

# A Closed swarm - load the POA. Will throw an exception if no POA is available
if tdef.get_cs_keys():
    print >>sys.stderr, "Is a closed swarm, reading POA"
    try:
        poa = ClosedSwarm.trivial_get_poa(s.get_default_state_dir(),
                                          s.get_permid(),
                                          tdef.infohash)
    except Exception,e:
        print >>sys.stderr, "Failed to load POA for swarm",encodestring(tdef.infohash).replace("\n",""),"from",s.get_default_state_dir(),"(my permid is %s)"%encodestring(s.get_permid()).replace("\n",""),"Error was:",e
        raise SystemExit("Failed to load POA, aborting")

d = s.start_download( tdef, dscfg )

d.set_state_callback(state_callback,getpeerlist=False)

while True:
  time.sleep(60)

