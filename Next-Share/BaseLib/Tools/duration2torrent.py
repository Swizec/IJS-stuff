# Written by Riccardo Petrocco
# see LICENSE.txt for license information
#

import sys
import os
import shutil
import time
import tempfile
import random
import urllib2
from traceback import print_exc
from threading import Condition

from BaseLib.Core.API import *
import BaseLib.Core.BitTornado.parseargs as parseargs

argsdef = [('torrent', '', 'source torrent to be modified'),
           ('destdir', '.','dir to save torrent'),
           ('newtorrent', '', 'name of the new torrent, if not specified the original torrent will be replaced'),
           ('duration', '', 'duration of the stream in hh:mm:ss format')]


def get_usage(defs):
    return parseargs.formatDefinitions(defs,80)
    
    
if __name__ == "__main__":

    config, fileargs = parseargs.parseargs(sys.argv, argsdef, presets = {})
    print >>sys.stderr,"config is",config
    
    if config['torrent'] == '':
        print "Usage:  ",get_usage(argsdef)
        sys.exit(0)
                
    tdef = TorrentDef.load(config['torrent'])
    metainfo = tdef.get_metainfo()
    
    if config['duration'] != '':
        metainfo['playtime'] = config['duration']
        
    tdef.finalize()
    
    if config['newtorrent'] == '':
        torrentbasename = config['torrent']
    else:
        torrentbasename = config['newtorrent'] + '.torrent'

    torrentfilename = os.path.join(config['destdir'],torrentbasename)
    tdef.save(torrentfilename)
