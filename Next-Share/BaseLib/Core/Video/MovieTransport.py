# Written by Jan David Mol, Arno Bakker
# see LICENSE.txt for license information


import os,sys

from BaseLib.Core.osutils import *

DEBUG = False

class MovieTransport:
    
    def __init__(self):
        pass
        
    def start( self, bytepos = 0 ):
        pass
    
    def size(self ):
        pass

    def read(self):
        pass
        
    def stop(self):
        pass

    def done(self):
        pass
    
    def get_mimetype(self):
        pass
 
    def set_mimetype(self,mimetype):
        pass

    def available(self):
        pass
    
 
class MovieTransportStreamWrapper:
    """ Provide a file-like interface """
    def __init__(self,mt):
        self.mt = mt
        self.started = False

    def read(self,numbytes=None):
        if DEBUG:
            print >>sys.stderr,"MovieTransportStreamWrapper: read",numbytes

        if not self.started:
            self.mt.start(0)
            self.started = True
        if self.mt.done():
            return ''
        data = self.mt.read(numbytes)
        if data is None:
            print >>sys.stderr,"MovieTransportStreamWrapper: mt read returns None"
            data = ''
        return data

    def seek(self,pos,whence=os.SEEK_SET):
        # TODO: shift play_pos in PiecePicking + interpret whence
        if DEBUG:
            print >>sys.stderr,"MovieTransportStreamWrapper: seek:",pos,"whence",whence
        self.mt.seek(pos,whence=whence)
        # Arno, 2010-01-08: seek also means we've started.
        self.started = True
    
    def close(self):
        if DEBUG:
            print >>sys.stderr,"MovieTransportStreamWrapper: close"
        self.mt.stop()

    def available(self):
        return self.mt.available()
    
    def get_generation_time(self):
        # Overrriden by AuthStreamWrapper normally. Added to give sane warning
        # when playing unauthenticated stream as if it had auth.
        raise ValueError("This is an unauthenticated stream that provides no timestamp")
