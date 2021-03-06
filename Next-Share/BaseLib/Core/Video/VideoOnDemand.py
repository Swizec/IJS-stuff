# Written by Jan David Mol, Arno Bakker
# see LICENSE.txt for license information

import sys
from math import ceil
from threading import Condition,currentThread
from traceback import print_exc,print_stack
from tempfile import mkstemp
import collections
import os
import base64
import os,sys,time
import re
from base64 import b64encode

from BaseLib.Core.BitTornado.CurrentRateMeasure import Measure
from BaseLib.Core.Video.MovieTransport import MovieTransport,MovieTransportStreamWrapper
from BaseLib.Core.simpledefs import *
from BaseLib.Core.osutils import *
from BaseLib.Core.Statistics.Status.Status import get_status_holder

# pull all video data as if a video player was attached
FAKEPLAYBACK = False

DEBUG = False
DEBUG_HOOKIN = True

class PieceStats:
    """ Keeps track of statistics for each piece as it flows through the system. """

    def __init__(self):
        self.pieces = {}
        self.completed = {}

    def set(self,piece,stat,value,firstonly=True):
        if piece not in self.pieces:
            self.pieces[piece] = {}

        if firstonly and stat in self.pieces[piece]:
            return

        self.pieces[piece][stat] = value

    def complete(self,piece):
        self.completed[piece] = 1

    def reset(self):
        for x in self.completed:
            self.pieces.pop(x,0)

        self.completed = {}

    def pop_completed(self):
        completed = {}

        for x in self.completed.keys():
            completed[x] = self.pieces.pop(x,{})

        self.completed = {}
        return completed

class MovieOnDemandTransporter(MovieTransport):
    """ Takes care of providing a bytestream interface based on the available pieces. """

    # seconds to prebuffer if bitrate is known
    PREBUF_SEC_LIVE = 10.0
    PREBUF_SEC_VOD  = 10.0
    
    # Arno, 2010-01-14: prebuf is controlled with the above params. Buffering
    # while playback for VOD is handled by increasing the high range, see
    # VideoStatus self.high_prob_curr_*

    # max number of seconds in queue to player
    # Arno: < 2008-07-15: St*pid vlc apparently can't handle lots of data pushed to it
    # Arno: 2008-07-15: 0.8.6h apparently can
    BUFFER_TIME = 5.0
    
    # polling interval to refill buffer
    #REFILL_INTERVAL = BUFFER_TIME * 0.75
    # Arno: there is no guarantee we got enough (=BUFFER_TIME secs worth) to write to output bug!
    REFILL_INTERVAL = 0.1

    # amount of time (seconds) to push a packet into
    # the player queue ahead of schedule
    VLC_BUFFER_SIZE = 0
    PIECE_DUE_SKEW = 0.1 + VLC_BUFFER_SIZE

    # Arno: If we don't know playtime and FFMPEG gave no decent bitrate, this is the minimum
    # bitrate (in KByte/s) that the playback birate-estimator must have to make us
    # set the bitrate in movieselector.
    MINPLAYBACKRATE = 32*1024
    
    # If not yet playing and if the difference between the peer's first chosen
    # hookin time and the newly calculated hookin time is larger than 
    # PREBUF_REHOOKIN_SECS (because his peer environment changed), then rehookin. 
    PREBUF_REHOOKIN_SECS = 5.0

    # maximum delay between pops when live streaming before we force a restart (seconds)
    MAX_POP_TIME = 10

    def __init__(self,bt1download,videostatus,videoinfo,videoanalyserpath,vodeventfunc,httpsupport=None):

        # dirty hack to get the Tribler Session
        from BaseLib.Core.Session import Session
        session = Session.get_instance()

        # hack: we should not import this since it is not part of the
        # core nor should we import here, but otherwise we will get
        # import errors
        #
        # _event_reporter stores events that are logged somewhere...
        # from BaseLib.Core.Statistics.StatusReporter import get_reporter_instance
        self._event_reporter = get_status_holder("LivingLab")
        self.b64_infohash = b64encode(bt1download.infohash)
            
        # add an event to indicate that the user wants playback to
        # start
        def set_nat(nat):
            self._event_reporter.create_and_add_event("nat", [self.b64_infohash, nat])
        self._event_reporter.create_and_add_event("play-init", [self.b64_infohash])
        self._event_reporter.create_and_add_event("piece-size", [self.b64_infohash, videostatus.piecelen])
        self._event_reporter.create_and_add_event("num-pieces", [self.b64_infohash, videostatus.movie_numpieces])
        self._event_reporter.create_and_add_event("bitrate", [self.b64_infohash, videostatus.bitrate])
        self._event_reporter.create_and_add_event("nat", [self.b64_infohash, session.get_nat_type(callback=set_nat)])

        # self._complete = False
        self.videoinfo = videoinfo
        self.bt1download = bt1download
        self.piecepicker = bt1download.picker
        self.rawserver = bt1download.rawserver
        self.storagewrapper = bt1download.storagewrapper
        self.fileselector = bt1download.fileselector

        self.vodeventfunc = vodeventfunc
        self.videostatus = vs = videostatus
        # Diego : Http seeding video support
        self.http_support = httpsupport
        self.traker_peers_report = None
        self.http_first_run = None
        
        # Add quotes around path, as that's what os.popen() wants on win32
        if sys.platform == "win32" and videoanalyserpath is not None and videoanalyserpath.find(' ') != -1:
            self.video_analyser_path='"'+videoanalyserpath+'"'
        else:
            self.video_analyser_path=videoanalyserpath

        # counter for the sustainable() call. Every X calls the
        # buffer-percentage is updated.
        self.sustainable_counter = sys.maxint

        # boudewijn: because we now update the downloadrate for each
        # received chunk instead of each piece we do not need to
        # average the measurement over a 'long' period of time. Also,
        # we only update the downloadrate for pieces that are in the
        # high priority range giving us a better estimation on how
        # likely the pieces will be available on time.
        self.overall_rate = Measure(10)
        self.high_range_rate = Measure(2)

        # buffer: a link to the piecepicker buffer
        self.has = self.piecepicker.has

        # number of pieces in buffer
        self.pieces_in_buffer = 0

        self.data_ready = Condition()
        
        # Arno: Call FFMPEG only if the torrent did not provide the 
        # bitrate and video dimensions. This is becasue FFMPEG 
        # sometimes hangs e.g. Ivaylo's Xvid Finland AVI, for unknown 
        # reasons
        
        # Arno: 2007-01-06: Since we use VideoLan player, videodimensions not important
        if vs.bitrate_set:
            self.doing_ffmpeg_analysis = False
            self.doing_bitrate_est = False
            self.videodim = None #self.movieselector.videodim
        else:
            self.doing_ffmpeg_analysis = True
            self.doing_bitrate_est = True
            self.videodim = None

        self.player_opened_with_width_height = False
        self.ffmpeg_est_bitrate = None
        
        # number of packets required to preparse the video
        # I say we need 128 KB to sniff size and bitrate
        
        # Arno: 2007-01-04: Changed to 1MB. It appears ffplay works better with some
        # decent prebuffering. We should replace this with a timing based thing, 
        
        if not self.doing_bitrate_est:
            if vs.live_streaming:
                prebufsecs = self.PREBUF_SEC_LIVE
            else:
                prebufsecs = self.PREBUF_SEC_VOD

            if vs.bitrate <=  (256 * 1024 / 8):
                print >>sys.stderr,"vod: trans: Increasing prebuffer for low-bitrate feeds"
                prebufsecs += 5.0
            # assumes first piece is whole (first_piecelen == piecelen)
            piecesneeded = vs.time_to_pieces( prebufsecs )
        else:
            # Arno, 2010-01-13: For torrents with unknown bitrate, prebuf more
            # following Boudewijn's heuristics
            piecesneeded = 2 * vs.get_high_range_length()

        if vs.wraparound:
            self.max_prebuf_packets = min(vs.wraparound_delta, piecesneeded)
        else:
            self.max_prebuf_packets = min(vs.movie_numpieces, piecesneeded)
            
        if DEBUG:
            if self.doing_ffmpeg_analysis:
                print >>sys.stderr,"vod: trans: Want",self.max_prebuf_packets,"pieces for FFMPEG analysis, piecesize",vs.piecelen
            else:
                print >>sys.stderr,"vod: trans: Want",self.max_prebuf_packets,"pieces for prebuffering"

        self.nreceived = 0
        
        if DEBUG:
            print >>sys.stderr,"vod: trans: Setting MIME type to",self.videoinfo['mimetype']
        
        self.set_mimetype(self.videoinfo['mimetype'])

        # some statistics
        self.stat_playedpieces = 0 # number of pieces played successfully
        self.stat_latepieces = 0 # number of pieces that arrived too late
        self.stat_droppedpieces = 0 # number of pieces dropped
        self.stat_stalltime = 0.0 # total amount of time the video was stalled
        self.stat_prebuffertime = 0.0 # amount of prebuffer time used
        self.stat_pieces = PieceStats() # information about each piece

        # start periodic tasks
        self.curpiece = ""
        self.curpiece_pos = 0
        self.outbuf = []
        self.outbuflen = None
        self.last_pop = None # time of last pop
        self.rehookin = False
        self.reset_bitrate_prediction()

        self.lasttime=0
        # For DownloadState
        self.prebufprogress = 0.0
        self.prebufstart = time.time()
        self.playable = False
        self.usernotified = False
        

        # LIVESOURCEAUTH
        if vs.live_streaming:
            from BaseLib.Core.Video.LiveSourceAuth import ECDSAAuthenticator,RSAAuthenticator

            if vs.authparams['authmethod'] == LIVE_AUTHMETHOD_ECDSA:
                self.authenticator = ECDSAAuthenticator(vs.first_piecelen,vs.movie_numpieces,pubkeypem=vs.authparams['pubkey'])
                vs.sigsize = vs.piecelen - self.authenticator.get_content_blocksize()
            elif vs.authparams['authmethod'] == LIVE_AUTHMETHOD_RSA:
                self.authenticator = RSAAuthenticator(vs.first_piecelen,vs.movie_numpieces,pubkeypem=vs.authparams['pubkey'])
                vs.sigsize = vs.piecelen - self.authenticator.get_content_blocksize()
            else:
                self.authenticator = None
                vs.sigsize = 0
        else:
            self.authenticator = None

        self.video_refillbuf_rawtask()
        if False:
            self.video_printstats_tick_second()

        # link to others (last thing to do)
        self.piecepicker.set_transporter( self )
        if not vs.live_streaming:
            self.complete_from_persistent_state(self.storagewrapper.get_pieces_on_disk_at_startup())
        #self.start()

        if FAKEPLAYBACK:
            import threading
            
            class FakeReader(threading.Thread):
                def __init__(self,movie):
                    threading.Thread.__init__(self)
                    self.movie = movie
                    
                def run(self):
                    self.movie.start()
                    while not self.movie.done():
                        self.movie.read()
            
            t = FakeReader(self)
            t.start()
          
        #self.rawserver.add_task( fakereader, 0.0 )

        if self.videostatus.live_streaming:
            self.live_streaming_timer()

        self.update_prebuffering()

    def calc_live_startpos(self,prebufsize=2,have=False):
        """ When watching a live stream, determine where to 'hook in'. Adjusts 
            self.download_range[0] accordingly, never decreasing it. If 'have' 
            is true, we need to have the data ourself. If 'have' is false, we 
            look at availability at our neighbours.

            Return True if successful, False if more data has to be collected. 
            
            This is called periodically until playback has started. After that,
            the hookin point / playback position is either fixed, or determined 
            by active pausing and resuming of the playback by this class, see
            refill_buffer().
        """

        if DEBUG_HOOKIN:
            print >>sys.stderr,"vod: calc_live_startpos: prebuf",prebufsize,"have",have

        # ----- determine highest known piece number
        if have:
            # I am already hooked in and downloaded stuff, now do the final
            # hookin based on what I have.
            numseeds = 0
            numhaves = self.piecepicker.has 
            totalhaves = self.piecepicker.numgot
            sourcehave = None

            threshold = 1
        else:
            # Check neighbours playback pos to see where I should hookin.
            numseeds = self.piecepicker.seeds_connected
            numhaves = self.piecepicker.numhaves # excludes seeds
            totalhaves = self.piecepicker.totalcount # excludes seeds
            sourcehave = self.piecepicker.get_live_source_have()
            
            if DEBUG and DEBUG_HOOKIN:
                if sourcehave is not None:
                    print >>sys.stderr,"vod: calc_live_offset: DEBUG: testing for multiple clients at source IP (forbidden!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!, but used in CS testing). Source have numtrue",sourcehave.get_numtrue()
                    if sourcehave.get_numtrue() < 100:
                        print >>sys.stderr,"vod: calc_live_offset: Source sent near empty BITFIELD, CS testing bug? Not tuning in as source"
                        sourcehave = None

            numconns = self.piecepicker.num_nonempty_neighbours()
            if sourcehave is None:
                # We don't have a connection to the source, must get at least 2 votes 
                threshold = max( 2, numconns/2 )
            else:
                if DEBUG_HOOKIN:
                    print >>sys.stderr,"vod: calc_live_offset: Connected to source, hookin on that" 
                    #print >>sys.stderr,"vod: calc_live_offset: sourcehave",`sourcehave.tostring()`
                threshold = 1

        # FUDGE: number of pieces we subtract from maximum known/have,
        # to start playback with some buffer present. We need enough
        # pieces to do pass the prebuffering phase. when still
        # requesting pieces, FUDGE can probably be a bit low lower,
        # since by the time they arrive, we will have later pieces anyway.
        # NB: all live torrents have the bitrate set.
        FUDGE = prebufsize #self.max_prebuf_packets

        if numseeds == 0 and totalhaves == 0:
            # optimisation: without seeds or pieces, just wait
            if DEBUG_HOOKIN:
                print >>sys.stderr,"vod: calc_live_offset: no pieces"
            return False

        # pieces are known, so we can determine where to start playing
        vs = self.videostatus

        bpiece = vs.first_piece
        epiece = vs.last_piece

        if not vs.wraparound:
            if numseeds > 0 or numhaves[epiece] > 0:
                # special: if full video is available, do nothing and enter VoD mode
                if DEBUG_HOOKIN:
                    print >>sys.stderr,"vod: calc_live_offset: vod mode"
                vs.set_live_startpos( 0 )
                return True

        # maxnum = highest existing piece number owned by more than half of the neighbours
        maxnum = None
        if sourcehave is None:
            # Look at peer neighbourhood
            inspecthave = numhaves
        else:
            # Just look at source
            inspecthave = sourcehave
        
        for i in xrange(epiece,bpiece-1,-1):
            #if DEBUG_HOOKIN:
            #    if 0 < inspecthave[i] < threshold:
            #        print >>sys.stderr,"vod: calc_live_offset: discarding piece %d as it is owned by only %d<%d neighbours" % (i,inspecthave[i],threshold)

            if inspecthave[i] >= threshold:
                maxnum = i
                if not have:
                    if inspecthave == numhaves:
                        print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by %d>=%d neighbours (prewrap)" % (i,inspecthave[i],threshold)
                    else:
                        print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by the source (prewrap)" % (i)
                else:
                    print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by me (prewrap)" % (i)
                        
                break

        if maxnum is None:
            print >>sys.stderr,"vod: calc_live_offset: Failed to find quorum for any piece"
            return False

        # if there is wraparound, newest piece may actually have wrapped
        if vs.wraparound and maxnum > epiece - vs.wraparound_delta:
            delta_left = vs.wraparound_delta - (epiece-maxnum)

            for i in xrange( vs.first_piece+delta_left-1, vs.first_piece-1, -1 ):
                if inspecthave[i] >= threshold:
                    maxnum = i
                    if DEBUG_HOOKIN:
                        if not have:
                            if inspecthave == numhaves:
                                print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by %d>=%d neighbours (wrap)" % (i,inspecthave[i],threshold)
                            else:
                                print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by the source (wrap)" % (i)
                        else:
                            print >>sys.stderr,"vod: calc_live_offset: chosing piece %d as it is owned by me (wrap)" % (i)
                            
                    break

        print >>sys.stderr,"vod: calc_live_offset: hookin candidate (unfudged)",maxnum
        
        # start watching from maximum piece number, adjusted by fudge.
        if vs.wraparound:
            maxnum = vs.normalize( maxnum - FUDGE )
            #f = bpiece + (maxnum - bpiece - FUDGE) % (epiece-bpiece)
            #t = bpiece + (f - bpiece + vs.wraparound_delta) % (epiece-bpiece)

            # start at a piece known to exist to avoid waiting for something that won't appear
            # for another round. guaranteed to succeed since we would have bailed if noone had anything
            while not inspecthave[maxnum]:
                maxnum = vs.normalize( maxnum + 1 )
        else:
            maxnum = max( bpiece, maxnum - FUDGE )

            if maxnum == bpiece:
                # video has just started -- watch from beginning
                return True

        # If we're connected to the source, and already hooked in,
        # don't change the hooking point unless it is really far off
        oldstartpos = vs.get_live_startpos()
        if not have and threshold == 1 and oldstartpos is not None:
            diff = vs.dist_range(oldstartpos,maxnum)
            diffs = float(diff) * float(vs.piecelen) / vs.bitrate
            print >>sys.stderr,"vod: calc_live_offset: m o",maxnum,oldstartpos,"diff",diff,"diffs",diffs
            if diffs < self.PREBUF_REHOOKIN_SECS: 
                return True
            

        print >>sys.stderr,"vod: === HOOKING IN AT PIECE %d (based on have: %s) ===" % (maxnum,have)

        (toinvalidateset,toinvalidateranges) = vs.set_live_startpos( maxnum )
        #print >>sys.stderr,"vod: invalidateset is",`toinvalidateset`
        mevirgin = oldstartpos is None
        if len(toinvalidateranges) == 0 or (len(toinvalidateranges) == 0 and not mevirgin): # LAST condition is bugcatch
            for piece in toinvalidateset:
                self.live_invalidate_piece_globally(piece,mevirgin)
        else:
            self.live_invalidate_piece_ranges_globally(toinvalidateranges,toinvalidateset)

        try:
            self._event_reporter.create_and_add_event("live-hookin", [self.b64_infohash, maxnum])
        except:
            print_exc()

        return True
    

    def live_streaming_timer(self):
        """ Background 'thread' to check where to hook in if live streaming. """
        
        if DEBUG:
            print >>sys.stderr,"vod: live_streaming_timer: Checking hookin"
        nextt = 1
        try:
            try:
                vs = self.videostatus
            
                if vs.playing and not self.rehookin:
                    # Stop adjusting the download range via this mechanism, see 
                    # refill_buffer() for the new pause/resume mechanism.
                    
                    # Arno, 2010-03-04: Reactivate protection for live.
                    if vs.live_streaming and self.last_pop is not None and time.time() - self.last_pop > self.MAX_POP_TIME:
                        # Live: last pop too long ago, rehook-in
                        print >>sys.stderr,"vod: live_streaming_timer: Live stalled too long, reaanounce and REHOOK-in !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                        self.last_pop = time.time()
                        
                        # H4x0r: if conn to source was broken, reconnect
                        self.bt1download.reannounce()
                        
                        # Give some time to connect to new peers, so rehookin in 2 seconds
                        nextt = 2 
                        self.rehookin = True
                    return
                    
                # JD:keep checking correct playback pos since it can change if we switch neighbours
                # due to faulty peers etc
                if self.calc_live_startpos( self.max_prebuf_packets, False ):
                    self.rehookin = False
            except:
                print_exc()
        finally:
            # Always executed
            self.rawserver.add_task( self.live_streaming_timer, nextt )

    def parse_video(self):
        """ Feeds the first max_prebuf_packets to ffmpeg to determine video bitrate. """

        vs = self.videostatus
        width = None
        height = None

        # Start ffmpeg, let it write to a temporary file to prevent 
        # blocking problems on Win32 when FFMPEG outputs lots of
        # (error) messages.
        #
        [loghandle,logfilename] = mkstemp()
        os.close(loghandle)
        if sys.platform == "win32":
            # Not "Nul:" but "nul" is /dev/null on Win32
            sink = 'nul'
        else:
            sink = '/dev/null'
        # DON'T FORGET 'b' OTHERWISE WE'RE WRITING BINARY DATA IN TEXT MODE!
        (child_out,child_in) = os.popen2( "%s -y -i - -vcodec copy -acodec copy -f avi %s > %s 2>&1" % (self.video_analyser_path, sink, logfilename), 'b' )
        """
        # If the path is "C:\Program Files\bla\bla" (escaping left out) and that file does not exist
        # the output will say something cryptic like "vod: trans: FFMPEG said C:\Program" suggesting an
        # error with the double quotes around the command, but that's not it. Be warned!
        cmd = self.video_analyser_path+' -y -i - -vcodec copy -acodec copy -f avi '+sink+' > '+logfilename+' 2>&1'
        print >>sys.stderr,"vod: trans: Video analyser command is",cmd
        (child_out,child_in) = os.popen2(cmd,'b')  # DON'T FORGET 'b' OTHERWISE THINGS GO WRONG!
        """

        # feed all the pieces
        first,last = vs.download_range()
        for i in xrange(first,last):
            piece = self.get_piece( i )

            if piece is None:
                break

            # remove any signatures etc
            if self.authenticator is not None:
                piece = self.authenticator.get_content( piece )

            try:
                child_out.write( piece )
            except IOError:
                print_exc(file=sys.stderr)
                break

        child_out.close()
        child_in.close()

        logfile = open(logfilename, 'r')

        # find the bitrate in the output
        bitrate = None

        r = re.compile( "bitrate= *([0-9.]+)kbits/s" )
        r2 = re.compile( "Video:.* ([0-9]+x[0-9]+)," )    # video dimensions WIDTHxHEIGHT

        founddim = False
        for x in logfile.readlines():
            if DEBUG:
                print >>sys.stderr,"vod: trans: FFMPEG said:",x
            occ = r.findall( x )
            if occ:
                # use the latest mentioning of bitrate
                bitrate = float( occ[-1] ) * 1024 / 8
                if DEBUG:
                    if bitrate is not None:
                        print >>sys.stderr,"vod: trans: Bitrate according to FFMPEG: %.2f KByte/s" % (bitrate/1024)
                    else:
                        print >>sys.stderr,"vod: trans: Bitrate could not be determined by FFMPEG"
            occ = r2.findall( x )
            if occ and not founddim:
                # use first occurence
                dim = occ[0]
                idx = dim.find('x')
                width = int(dim[:idx])
                height = int(dim[idx+1:])
                founddim = True
                
                if DEBUG:
                    print >>sys.stderr,"vod: width",width,"heigth",height
        logfile.close()
        try:
            os.remove(logfilename)
        except:
            pass

        return [bitrate,width,height]

    def peers_from_tracker_report( self, num_peers ):
        #print >>sys.stderr,"DIEGO DEBUG Got from tracker : ", num_peers
        if self.traker_peers_report is None:
            self.traker_peers_report = num_peers
            self.update_prebuffering()
        else:
            self.traker_peers_report += num_peers

    def update_prebuffering(self,received_piece=None):
        """ Update prebuffering process. 'received_piece' is a hint that we just received this piece;
            keep at 'None' for an update in general. """

        vs = self.videostatus

        if not vs.prebuffering:
            return
        else:
            if self.http_support is not None:
                # Diego : Give the possibility to other peers to give bandwidth.
                # Wait a few seconds depending on the tracker response and
                # on the number of peers connected
                if self.http_first_run is None:
                    if self.traker_peers_report is None:
                        self.rawserver.add_task( lambda: self.peers_from_tracker_report(0), 1 ) # wait 1 second for tracker response
                    elif self.traker_peers_report:
                        self.http_support.start_video_support( 0, 2 ) # wait 2 seconds for connecting to peers
                        self.http_first_run = True
                    else:
                        self.http_support.start_video_support( 0 ) # no peers to connect to. start immediately
                        self.http_first_run = True
                elif self.http_first_run:
                    if not self.http_support.is_slow_start():
                        # Slow start is possible only if video support is off
                        self.http_first_run = False
                        self.http_support.stop_video_support()
                        num_peers = len( self.piecepicker.peer_connections )
                        if num_peers == 0: # no peers connected. start immediately
                            self.http_support.start_video_support( 0 )
                        elif num_peers <= 3: # few peers connected. wait 2 second to get bandwidth. TODO : Diego : tune peer threshold
                            self.http_support.start_video_support( 0, 2 )
                        else: # many peers connected. wait 5 seconds to get bandwidth.
                            self.http_support.start_video_support( 0, 5 )
                else:
                    self.http_support.start_video_support( 0 )

        if vs.live_streaming and vs.live_startpos is None:
            # first determine where to hook in
            return

        if received_piece:
            self.nreceived += 1

        # Arno, 2010-01-13: This code is only used when *pre*buffering, not
        # for in-playback buffering. See refill_buffer() for that.
        # Restored original code here that looks at max_prebuf_packets
        # and not highrange. The highrange solution didn't allow the prebuf
        # time to be varied independently of highrange width. 
        #
        f,t = vs.playback_pos, vs.normalize( vs.playback_pos + self.max_prebuf_packets )
        prebufrange = vs.generate_range( (f, t) )
        missing_pieces = filter( lambda i: not self.have_piece( i ), prebufrange)

        gotall = not missing_pieces
        self.prebufprogress = float(self.max_prebuf_packets-len(missing_pieces))/float(self.max_prebuf_packets)
        
        if DEBUG:
            print >>sys.stderr,"vod: trans: Already got",(self.prebufprogress*100.0),"% of prebuffer"
        
        if not gotall and DEBUG:
            print >>sys.stderr,"vod: trans: Still need pieces",missing_pieces,"for prebuffering/FFMPEG analysis"

        if vs.dropping:
            if not self.doing_ffmpeg_analysis and not gotall and not (0 in missing_pieces) and self.nreceived > self.max_prebuf_packets:
                perc = float(self.max_prebuf_packets)/10.0
                if float(len(missing_pieces)) < perc or self.nreceived > (2*self.max_prebuf_packets):
                    # If less then 10% of packets missing, or we got 2 times the packets we need already,
                    # force start of playback
                    gotall = True
                    if DEBUG:
                        print >>sys.stderr,"vod: trans: Forcing stop of prebuffering, less than",perc,"missing, or got 2N packets already"

        if gotall and self.doing_ffmpeg_analysis:
            [bitrate,width,height] = self.parse_video()
            self.doing_ffmpeg_analysis = False
            if DEBUG:
                print >>sys.stderr,"vod: trans: after parse",bitrate,self.doing_bitrate_est
            if bitrate is None or round(bitrate)== 0:
                if self.doing_bitrate_est:
                    # Errr... there was no playtime info in the torrent
                    # and FFMPEG can't tell us...
                    bitrate = (1*1024*1024/8) # 1mbps
                    if DEBUG:
                        print >>sys.stderr,"vod: trans: No bitrate info avail, wild guess: %.2f KByte/s" % (bitrate/1024)

                    vs.set_bitrate(bitrate)
                    self._event_reporter.create_and_add_event("bitrate-guess", [self.b64_infohash, bitrate])
            else:
                if self.doing_bitrate_est:
                    # There was no playtime info in torrent, use what FFMPEG tells us
                    self.ffmpeg_est_bitrate = bitrate
                    bitrate *= 1.1  # Make FFMPEG estimation 10% higher
                    if DEBUG:
                        print >>sys.stderr,"vod: trans: Estimated bitrate: %.2f KByte/s" % (bitrate/1024)

                    vs.set_bitrate(bitrate)
                    self._event_reporter.create_and_add_event("bitrate-ffmpeg", [self.b64_infohash, bitrate])

            if width is not None and height is not None:
                diff = False
                if self.videodim is None:
                    self.videodim = (width,height)
                    self.height = height
                elif self.videodim[0] != width or self.videodim[1] != height:
                    diff =  True
                if not self.player_opened_with_width_height or diff:
                    #self.user_setsize(self.videodim)
                    pass

        # # 10/03/09 boudewijn: For VOD we will wait for the entire
        # # buffer to fill (gotall) before we start playback. For live
        # # this is unlikely to happen and we will therefore only wait
        # # until we estimate that we have enough_buffer.
        # if (gotall or vs.live_streaming) and self.enough_buffer():
        if gotall and self.enough_buffer():
            # enough buffer and could estimated bitrate - start streaming
            if DEBUG:
                print >>sys.stderr,"vod: trans: Prebuffering done",currentThread().getName()
            self.data_ready.acquire()
            vs.prebuffering = False

            if self.http_support is not None:
                self.http_support.stop_video_support()
            self.stat_prebuffertime = time.time() - self.prebufstart
            self._event_reporter.create_and_add_event("prebuf", [self.b64_infohash, self.stat_prebuffertime])
            self.notify_playable()
            self.data_ready.notify()
            self.data_ready.release()

        """
        elif DEBUG:
            if self.doing_ffmpeg_analysis:
                print >>sys.stderr,"vod: trans: Prebuffering: waiting to obtain the first %d packets" % (self.max_prebuf_packets)
            else:
                print >>sys.stderr,"vod: trans: Prebuffering: %.2f seconds left" % (self.expected_buffering_time())
        """

    def got_have(self,piece):
        # Arno, 2010-04-15: STBSPEED Not called anymore, to speedup VOD.
        vs = self.videostatus

        # update stats
        self.stat_pieces.set( piece, "known", time.time() )
        """
        if vs.playing and vs.wraparound:
            # check whether we've slipped back too far
            d = vs.wraparound_delta
            n = max(1,self.piecepicker.num_nonempty_neighbours()/2)
            if self.piecepicker.numhaves[piece] > n and d/2 < (piece - vs.playback_pos) % vs.movie_numpieces < d:
                # have is confirmed by more than half of the neighours and is in second half of future window
                print >>sys.stderr,"vod: trans: Forcing restart. Am at playback position %d but saw %d at %d>%d peers." % (vs.playback_pos,piece,self.piecepicker.numhaves[piece],n)

                self.start(force=True)
        """

    def got_piece(self, piece_id, begin, length):
        """
        Called when a chunk has been downloaded. This information can
        be used to estimate download speed.
        """
        if self.videostatus.in_high_range(piece_id):
            self.high_range_rate.update_rate(length)
            # if DEBUG: print >>sys.stderr, "vod: high priority rate:", self.high_range_rate.get_rate()

    def complete_from_persistent_state(self,myhavelist):
        """ Arno, 2010-04-20: STBSPEED: Net effect of calling complete(piece,downloaded=False) 
        for pieces available from disk """
        vs = self.videostatus
        for piece in myhavelist:
            if vs.in_download_range(piece):
                self.pieces_in_buffer += 1

        self.update_prebuffering()

    
    def complete(self,piece,downloaded=True):
        """ Called when a movie piece has been downloaded or was available from the start (disk).
        Arno, 2010-04-20: STBSPEED: Never called anymore for available from start.  
        """

        vs = self.videostatus
 
        if vs.in_high_range(piece):
            self._event_reporter.create_and_add_event("hipiece", [self.b64_infohash, piece])
        else:
            self._event_reporter.create_and_add_event("piece", [self.b64_infohash, piece])

        # if not self._complete and self.piecepicker.am_I_complete():
        #     self._complete = True
        #     self._event_reporter.create_and_add_event(self.b64_infohash, "complete")
        #     self._event_reporter.flush()

        if vs.wraparound:
            assert downloaded

        self.stat_pieces.set( piece, "complete", time.time() )

        #if DEBUG:
        #    print >>sys.stderr,"vod: trans: Completed",piece

        if downloaded:
            self.overall_rate.update_rate( vs.real_piecelen( piece ) )

        # Arno, 2010-04-20: STBSPEED: vs.in_download_range( piece ) is equiv to downloaded=False
        if vs.in_download_range( piece ):
            self.pieces_in_buffer += 1
        else:
            if DEBUG:
                print >>sys.stderr,"vod: piece %d too late [pos=%d]" % (piece,vs.playback_pos)
            self.stat_latepieces += 1

        if vs.playing and vs.playback_pos == piece:
            # we were delaying for this piece
            self.refill_buffer()

        self.update_prebuffering( piece )

    def set_pos(self,pos):
        """ Update the playback position. Called when playback is started (depending
        on requested offset). """

        vs = self.videostatus

        #print >>sys.stderr,"vod: trans: set_pos",vs.playback_pos,"->",pos

        # Arno,2010-01-08: if all was pushed to buffer (!= read by user!) 
        # then playbackpos = last+1
        oldpos = min(vs.playback_pos,vs.last_piece) 
        vs.playback_pos = pos

        if vs.wraparound:
            # recalculate
            self.pieces_in_buffer = 0
            for i in vs.generate_range( vs.download_range() ):
                if self.has[i]:
                    self.pieces_in_buffer += 1
        else:
            # fast forward
            for i in xrange(oldpos,pos+1):
                if self.has[i]:
                    self.pieces_in_buffer -= 1

            # fast rewind
            for i in xrange(pos,oldpos+1):
                if self.has[i]:
                    self.pieces_in_buffer += 1

    def inc_pos(self):
        vs = self.videostatus

        if self.has[vs.playback_pos]:
            self.pieces_in_buffer -= 1

        vs.inc_playback_pos()
        
        if vs.live_streaming:
            self.live_invalidate_piece_globally(vs.live_piece_to_invalidate())

#    def buffered_time_period(self):
#        """Length of period of Buffered pieces"""
#        if self.movieselector.bitrate is None or self.movieselector.bitrate == 0.0:
#            return 0
#        else:
#            return self.pieces_in_buffer * self.movieselector.piece_length / self.movieselector.bitrate
#    
#    def playback_time_position(self):
#        """Time of playback_pos and total duration
#            Return playback_time in seconds
#        """
#        if self.movieselector.bitrate is None or self.movieselector.bitrate == 0.0:
#            return 0
#        else:
#            return self.playback_pos * self.movieselector.piece_length / self.movieselector.bitrate
    
    def expected_download_time(self):
        """ Expected download time left. """
        vs = self.videostatus
        if vs.wraparound:
            return float(2 ** 31)

        pieces_left = vs.last_piece - vs.playback_pos - self.pieces_in_buffer
        if pieces_left <= 0:
            return 0.0

        # list all pieces from the high priority set that have not
        # been completed
        uncompleted_pieces = filter(self.storagewrapper.do_I_have, vs.generate_high_range())

        # when all pieces in the high-range have been downloaded,
        # we have an expected download time of zero
        if not uncompleted_pieces:
            return 0.0

        # the download time estimator is very inacurate when we only
        # have a few chunks left. therefore, we will put more emphesis
        # on the overall_rate as the number of uncompleted_pieces goes
        # down.
        total_length = vs.get_high_range_length()
        uncompleted_length = len(uncompleted_pieces)
        expected_download_speed = self.high_range_rate.get_rate() * (1 - float(uncompleted_length) / total_length) + \
                                  self.overall_rate.get_rate() * uncompleted_length / total_length
        if expected_download_speed < 0.1:
            return float(2 ** 31)

        return pieces_left * vs.piecelen / expected_download_speed

    def expected_playback_time(self):
        """ Expected playback time left. """

        vs = self.videostatus

        if vs.wraparound:
            return float(2 ** 31)

        pieces_to_play = vs.last_piece - vs.playback_pos + 1

        if pieces_to_play <= 0:
            return 0.0

        if not vs.bitrate:
            return float(2 ** 31)

        return pieces_to_play * vs.piecelen / vs.bitrate

    def expected_buffering_time(self):
        """ Expected time required for buffering. """
        download_time = self.expected_download_time()
        playback_time = self.expected_playback_time()
        #print >>sys.stderr,"EXPECT",self.expected_download_time(),self.expected_playback_time()
        # Infinite minus infinite is still infinite
        if download_time > float(2 ** 30) and playback_time > float(2 ** 30):
            return float(2 ** 31)
        return abs(download_time - playback_time)

    def enough_buffer(self):
        """ Returns True if we can safely start playback without expecting to run out of
            buffer. """

        if self.videostatus.wraparound:
            # Wrapped streaming has no (known) limited duration, so we cannot predict
            # whether we have enough download speed. The only way is just to hope
            # for the best, since any buffer will be emptied if the download speed
            # is too low.
            return True

        return max(0.0, self.expected_download_time() - self.expected_playback_time()) == 0.0

    def video_printstats_tick_second(self):
        self.rawserver.add_task( self.video_printstats_tick_second, 1.0 )

        vs = self.videostatus

        # Adjust estimate every second, but don't display every second
        display = True # (int(time.time()) % 5) == 0
        if DEBUG: # display
            print >>sys.stderr,"vod: Estimated download time: %5.1fs [priority: %7.2f Kbyte/s] [overall: %7.2f Kbyte/s]" % (self.expected_download_time(), self.high_range_rate.get_rate()/1024, self.overall_rate.get_rate()/1024)

        if vs.playing and round(self.playbackrate.rate) > self.MINPLAYBACKRATE and not vs.prebuffering:
            if self.doing_bitrate_est:
                if display:
                    print >>sys.stderr,"vod: Estimated playback time: %5.0fs [%7.2f Kbyte/s], doing estimate=%d" % (self.expected_playback_time(),self.playbackrate.rate/1024, self.ffmpeg_est_bitrate is None)
                if self.ffmpeg_est_bitrate is None:
                    vs.set_bitrate( self.playbackrate.rate )

        if display:
            sys.stderr.flush()

    #
    # MovieTransport interface
    #
    # WARNING: these methods will be called by other threads than NetworkThread!
    #
    def size( self ):
        if self.videostatus.get_wraparound():
            return None
        else:
            return self.videostatus.selected_movie["size"]

    def read(self,numbytes=None):
        """ Read at most numbytes from the stream. If numbytes is not given,
            pieces are returned. The bytes read will be returned, or None in
            case of an error or end-of-stream. """
            
        if not self.curpiece:
            # curpiece_pos could be set to something other than 0! 
            # for instance, a seek request sets curpiece_pos but does not
            # set curpiece.

            piecetup = self.pop()
            if piecetup is None:
                return None
            
            piecenr,self.curpiece = piecetup
            if DEBUG:
                print >>sys.stderr,"vod: trans: %d: popped piece to transport to player" % piecenr

        curpos = self.curpiece_pos
        left = len(self.curpiece) - curpos

        if numbytes is None:
            # default on one piece per read
            numbytes = left

        if left > numbytes:
            # piece contains enough -- return what was requested
            data = self.curpiece[curpos:curpos+numbytes]

            self.curpiece_pos += numbytes
        else:
            # return remainder of the piece, could be less than numbytes
            
            data = self.curpiece[curpos:]

            self.curpiece = ""
            self.curpiece_pos = 0

        return data

    def start( self, bytepos = 0, force = False ):
        """ Initialise to start playing at position `bytepos'. """
        self._event_reporter.create_and_add_event("play", [self.b64_infohash])

        if DEBUG:
            print >>sys.stderr,"vod: trans: start:",bytepos

        # ARNOTODO: we don't use start(bytepos != 0) at the moment. See if we 
        # should. Also see if we need the read numbytes here, or that it
        # is better handled at a higher layer. For live it is currently
        # done at a higher level, see VariableReadAuthStreamWrapper because
        # we have to strip the signature. Hence the self.curpiece buffer here
        # is superfluous. Get rid off it or check if 
        #
        #    curpiece[0:piecelen]
        #
        # returns curpiece if piecelen has length piecelen == optimize for
        # piecesized case.
        #
        # For VOD seeking we may use the numbytes facility to seek to byte offsets
        # not just piece offsets.
        #
        vs = self.videostatus

        if vs.playing and not force:
            return

        # lock before changing startpos or any other playing variable
        self.data_ready.acquire()
        try:
            if vs.live_streaming:
                # Determine where to start playing. There may be several seconds
                # between starting the download and starting playback, which we'll
                # want to skip.
                self.calc_live_startpos( self.max_prebuf_packets, True )

                # override any position request by VLC, we only have live data
                piece = vs.playback_pos
                offset = 0
            else:
                # Determine piece number and offset
                if bytepos < vs.first_piecelen:
                    piece = vs.first_piece
                    offset = bytepos
                else:
                    newbytepos = bytepos - vs.first_piecelen

                    piece  = vs.first_piece + newbytepos / vs.piecelen + 1
                    offset = newbytepos % vs.piecelen

            if DEBUG:
                print >>sys.stderr,"vod: trans: === START at offset %d (piece %d) (forced: %s) ===" % (bytepos,piece,force),currentThread().getName()

            # Initialise all playing variables
            self.curpiece = "" # piece currently being popped
            self.curpiece_pos = offset
            self.set_pos( piece )
            self.outbuf = []
            self.last_pop = time.time()
            self.reset_bitrate_prediction()
            vs.playing = True
            self.playbackrate = Measure( 60 )

        finally:
            self.data_ready.release()

        # ARNOTODO: start is called by non-NetworkThreads, these following methods
        # are usually called by NetworkThread.
        #
        # We now know that this won't be called until notify_playable() so
        # perhaps this can be removed?
        #
        # CAREFUL: if we use start() for seeking... that's OK. User won't be
        # able to seek before he got his hands on the stream, so after 
        # notify_playable()
        
        # See what we can do right now
        self.update_prebuffering()
        self.refill_buffer()

    def stop( self ):
        """ Playback is stopped. """
        self._event_reporter.create_and_add_event("stop", [self.b64_infohash])
        # self._event_reporter.flush()

        vs = self.videostatus
        if DEBUG:
            print >>sys.stderr,"vod: trans: === STOP  = player closed conn === ",currentThread().getName()
        if not vs.playing:
            return
        vs.playing = False

        # clear buffer and notify possible readers
        self.data_ready.acquire()
        self.outbuf = []
        self.last_pop = None
        vs.prebuffering = False
        self.data_ready.notify()
        self.data_ready.release()

    def pause( self, autoresume = False ):
        """ Pause playback. If `autoresume' is set, playback is expected to be
        resumed automatically once enough data has arrived. """
        self._event_reporter.create_and_add_event("pause", [self.b64_infohash])

        vs = self.videostatus
        if not vs.playing or not vs.pausable:
            return

        if vs.paused:
            vs.autoresume = autoresume
            return

        if DEBUG:
            print >>sys.stderr,"vod: trans: paused (autoresume: %s)" % (autoresume,)

        vs.paused = True
        vs.autoresume = autoresume
        self.paused_at = time.time()
        #self.reset_bitrate_prediction()
        self.videoinfo["usercallback"](VODEVENT_PAUSE,{ "autoresume": autoresume })

    def resume( self ):
        """ Resume paused playback. """
        self._event_reporter.create_and_add_event("resume", [self.b64_infohash])

        vs = self.videostatus

        if not vs.playing or not vs.paused or not vs.pausable:
            return

        if DEBUG:
            print >>sys.stderr,"vod: trans: resumed"

        vs.paused = False
        vs.autoresume = False
        self.stat_stalltime += time.time() - self.paused_at
        self.addtime_bitrate_prediction( time.time() - self.paused_at )
        self.videoinfo["usercallback"](VODEVENT_RESUME,{})

        self.update_prebuffering()
        self.refill_buffer()

    def autoresume( self, testfunc = lambda: True ):
        """ Resumes if testfunc returns True. If not, will test every second. """

        vs = self.videostatus

        if not vs.playing or not vs.paused or not vs.autoresume:
            return

        if not testfunc():
            self.rawserver.add_task( lambda: self.autoresume( testfunc ), 1.0 )
            return

        if DEBUG:
            print >>sys.stderr,"vod: trans: Resuming, since we can maintain this playback position"
        self.resume()

    def done( self ):
        vs = self.videostatus

        if not vs.playing:
            return True

        if vs.wraparound:
            return False

        # Arno, 2010-01-08: Adjusted EOF condition to work well with seeking/HTTP range queries
        return vs.playback_pos == vs.last_piece+1 and len(self.outbuf) == 0 and self.curpiece_pos == 0 and len(self.curpiece) == 0

    def seek(self,pos,whence=os.SEEK_SET):
        """ Seek to the given position, a number in bytes relative to both
        the "whence" reference point and the file being played.
        
        We currently actually seek at byte level, via the start() method.
        We support all forms of seeking, including seeking past the current
        playback pos. Note this may imply needing to prebuffer again or 
        being paused.
        
        vs.playback_pos in NetworkThread domain. Does data_ready lock cover 
        that? Nope. However, this doesn't appear to be respected in any
        of the MovieTransport methods, check all.
        
        Check
        * When seeking reset other buffering, e.g. read()'s self.curpiece
           and higher layers.
        
        """
        vs = self.videostatus
        length = self.size()

        # lock before changing startpos or any other playing variable
        self.data_ready.acquire()
        try:
            if vs.live_streaming:
                # Arno, 2010-07-16: Raise error on seek, is clearer to stream user.
                raise ValueError("seeking not possible for live")
            if whence == os.SEEK_SET:
                abspos = pos
            elif whence == os.SEEK_END:
                if pos > 0:
                    raise ValueError("seeking beyond end of stream")
                else:
                    abspos = length+pos
            else: # SEEK_CUR
                raise ValueError("seeking does not currently support SEEK_CUR")
            
            self.stop()
            self.start(pos)
        finally:
            self.data_ready.release()



    def get_mimetype(self):
        return self.mimetype

    def set_mimetype(self,mimetype):
        self.mimetype = mimetype
        
    def available(self):
        self.data_ready.acquire()
        try:
            return self.outbuflen    
        finally:
            self.data_ready.release()
        
        
    #
    # End of MovieTransport interface
    #

    def have_piece(self,piece):
        return self.piecepicker.has[piece]

    def get_piece(self,piece):
        """ Returns the data of a certain piece, or None. """

        vs = self.videostatus

        if not self.have_piece( piece ):
            return None

        begin = 0
        length = vs.piecelen

        if piece == vs.first_piece:
            begin = vs.movie_range[0][1]
            length -= begin

        if piece == vs.last_piece:
            cutoff = vs.piecelen - (vs.movie_range[1][1] + 1)
            length -= cutoff

        #print >>sys.stderr,"get_piece",piece
        data = self.storagewrapper.do_get_piece(piece, begin, length)
        if data is None:
            return None
        return data.tostring()

    def reset_bitrate_prediction(self):
        self.start_playback = None
        self.last_playback = None
        self.history_playback = collections.deque()

    def addtime_bitrate_prediction(self,seconds):
        if self.start_playback is not None:
            self.start_playback["local_ts"] += seconds

    def valid_piece_data(self,i,piece):
        if not piece:
            return False

        if not self.start_playback or self.authenticator is None:
            # no check possible
            return True

        s = self.start_playback

        seqnum = self.authenticator.get_seqnum( piece )
        source_ts = self.authenticator.get_rtstamp( piece )

        if seqnum < s["absnr"] or source_ts < s["source_ts"]:
            # old packet???
            print >>sys.stderr,"vod: trans: **** INVALID PIECE #%s **** seqnum=%d but we started at seqnum=%d, ts=%f but we started at %f" % (i,seqnum,s["absnr"],source_ts,s["source_ts"])
            return False

        return True


    def update_bitrate_prediction(self,i,piece):
        """ Update the rate prediction given that piece i has just been pushed to the buffer. """

        if self.authenticator is not None:
            seqnum = self.authenticator.get_seqnum( piece )
            source_ts = self.authenticator.get_rtstamp( piece )
        else:
            seqnum = i
            source_ts = 0

        d = {
            "nr": i,
            "absnr": seqnum,
            "local_ts": time.time(),
            "source_ts": source_ts,
        }

        # record 
        if self.start_playback is None:
            self.start_playback = d

        if self.last_playback and self.last_playback["absnr"] > d["absnr"]:
            # called out of order
            return

        self.last_playback = d

        # keep a recent history
        MAX_HIST_LEN = 10*60 # seconds

        self.history_playback.append( d )

        # of at most 10 entries (or minutes if we keep receiving pieces)
        while source_ts - self.history_playback[0]["source_ts"] > MAX_HIST_LEN:
            self.history_playback.popleft()

        if DEBUG:
            vs = self.videostatus
            first, last = self.history_playback[0], self.history_playback[-1]
            
            if first["source_ts"] and first != last:
                divd = (last["source_ts"] - first["source_ts"])
                if divd == 0:
                    divd = 0.000001
                bitrate = "%.2f kbps" % (8.0 / 1024 * (vs.piecelen - vs.sigsize) * (last["absnr"] - first["absnr"]) / divd,)
            else:
                bitrate = "%.2f kbps (external info)" % (8.0 / 1024 * vs.bitrate)

            print >>sys.stderr,"vod: trans: %i: pushed at t=%.2f, age is t=%.2f, bitrate = %s" % (i,d["local_ts"]-self.start_playback["local_ts"],d["source_ts"]-self.start_playback["source_ts"],bitrate)

    def piece_due(self,i):
        """ Return the time when we expect to have to send a certain piece to the player. For
        wraparound, future pieces are assumed. """

        if self.start_playback is None:
            return float(2 ** 31) # end of time

        s = self.start_playback
        l = self.last_playback
        vs = self.videostatus

        if not vs.wraparound and i < l["nr"]:
            # should already have arrived!
            return time.time()

        # assume at most one wrap-around between l and i
        piecedist = (i - l["nr"]) % vs.movie_numpieces

        if s["source_ts"]:
            # ----- we have timing information from the source
            first, last = self.history_playback[0], self.history_playback[-1]

            if first != last:
                # we have at least two recent pieces, so can calculate average bitrate. use the recent history
                # do *not* adjust for sigsize since we don't want the actual video speed but the piece rate
                bitrate = 1.0 * vs.piecelen * (last["absnr"] - first["absnr"]) / (last["source_ts"] - first["source_ts"])
            else:
                # fall-back to bitrate predicted from torrent / ffmpeg
                bitrate = vs.bitrate
           
            # extrapolate with the average bitrate so far
            return s["local_ts"] + l["source_ts"] - s["source_ts"] + piecedist * vs.piecelen / bitrate - self.PIECE_DUE_SKEW
        else:
            # ----- no timing information from pieces, so do old-fashioned methods
            if vs.live_streaming:
                # Arno, 2008-11-20: old-fashioned method is well bad,
                # ignore.
                return time.time() + 60.0
            else:
                i =  piecedist + (l["absnr"] - s["absnr"])
                
                if s["nr"] == vs.first_piece:
                    bytepos = vs.first_piecelen + (i-1) * vs.piecelen
                else:
                    bytepos = i * vs.piecelen
                
                return s["local_ts"] + bytepos / vs.bitrate - self.PIECE_DUE_SKEW
            

    def max_buffer_size( self ):
        vs = self.videostatus
        if vs.dropping:
            # live
            # Arno: 1/2 MB or based on bitrate if that is above 5 Mbps
            return max( 0*512*1024, self.BUFFER_TIME * vs.bitrate )
        else:
            # VOD
            # boudewijn: 1/4 MB, bitrate, or 2 pieces (wichever is higher)
            return max(256*1024, vs.piecelen * 2, self.BUFFER_TIME * vs.bitrate)


    def refill_buffer( self ):
        """ Push pieces into the player FIFO when needed and able. This counts as playing
            the pieces as far as playback_pos is concerned."""
            
        # HttpSeed policy: if the buffer is underrun we start asking pieces from http (always available)
        # till the next refill_buffer call. As soon as refill_buffer is called again we stop asking http
        # and start again in case the buffer is still underrun. We never stop asking till prefuffering.

        self.data_ready.acquire()

        vs = self.videostatus

        if vs.prebuffering or not vs.playing:
            self.data_ready.release()
            return

        if vs.paused:
            self.data_ready.release()
            return

        mx = self.max_buffer_size()
        self.outbuflen = sum( [len(d) for (p,d) in self.outbuf] )
        now = time.time()

        if self.http_support is not None:
            if self.outbuflen < ( mx / 4 ):
                if not self.done(): # TODO : Diego : correct end test?
                    self.http_support.start_video_support( 0 )
                else:
                    self.http_support.stop_video_support() # Download finished
            else:
                self.http_support.stop_video_support()

        def buffer_underrun():
            return self.outbuflen == 0 and self.start_playback and now - self.start_playback["local_ts"] > 1.0

        # Arno, 2010-04-16: STBSPEED: simplified. If we cannot pause, we
        # just push everything we got to the player this buys us time to 
        # retrieve more data.
        if buffer_underrun() and vs.pausable:

            if vs.dropping: # live
                def sustainable():
                    # buffer underrun -- check for available pieces
                    num_future_pieces = 0
                    for piece in vs.generate_range( vs.download_range() ):
                        if self.has[piece]:
                            num_future_pieces += 1

                    goal = mx / 2
                    # progress
                    self.prebufprogress = min(1.0,float(num_future_pieces * vs.piecelen) / float(goal))
                    
                    # enough future data to fill the buffer
                    return num_future_pieces * vs.piecelen >= goal
            else: # vod
                def sustainable():
                    # num_immediate_packets = 0
                    # for piece in vs.generate_range( vs.download_range() ):
                    #     if self.has[piece]:
                    #         num_immediate_packets += 1
                    #     else:
                    #         break
                    # else:
                    #     # progress                                                                              
                    #     self.prebufprogress = 1.0
                    #     # completed loop without breaking, so we have everything we need                        
                    #     return True
                    #
                    # # progress                                                                                  
                    # self.prebufprogress = min(1.0,float(num_immediate_packets) / float(self.max_prebuf_packets))
                    #
                    # return num_immediate_packets >= self.max_prebuf_packets

                    self.sustainable_counter += 1
                    if self.sustainable_counter > 10:
                        self.sustainable_counter = 0
                        
                        high_range_length = vs.get_high_range_length()
                        have_length = len(filter(lambda n:self.has[n], vs.generate_high_range()))

                        # progress                                                                                  
                        self.prebufprogress = min(1.0, float(have_length) / max(1, high_range_length))

                        return have_length >= high_range_length

                    else:
                        num_immediate_packets = 0
                        high_range_length = vs.get_high_range_length()
                        # for piece in vs.generate_range(vs.download_range()): 
                        for piece in vs.generate_high_range(): 
                            if self.has[piece]:
                                num_immediate_packets += 1
                                if num_immediate_packets >= high_range_length:
                                    break
                            else:
                                break
                        else:
                            # progress                                                                              
                            self.prebufprogress = 1.0
                            # completed loop without breaking, so we have everything we need                        
                            return True

                        return num_immediate_packets >= high_range_length

            sus = sustainable()
            if not sus:
                if DEBUG:
                    print >>sys.stderr,"vod: trans:                        BUFFER UNDERRUN -- PAUSING"
                    
                # TODO : Diego : The Http support level should be tuned according to the sustainability level
                if self.http_support is not None:
                    self.http_support.start_video_support( 0 ) # TODO : Diego : still needed? here the buffer is 0 so already asking for support
                self.pause( autoresume = True )
                self.autoresume( sustainable )

                # boudewijn: increase the minimum buffer size
                vs.increase_high_range()
                        
                self.data_ready.release()
                return
                    
        def push( i, data ):
            # force buffer underrun:
            #if self.start_playback and time.time()-self.start_playback["local_ts"] > 60:
            #    # hack: dont push after 1 minute
            #    return

            # push packet into queue
            if DEBUG:
                print >>sys.stderr,"vod: trans: %d: pushed l=%d" % (vs.playback_pos,piece)

            # update predictions based on this piece
            self.update_bitrate_prediction( i, data )

            self.stat_playedpieces += 1
            self.stat_pieces.set( i, "tobuffer", time.time() )
                    
            self.outbuf.append( (vs.playback_pos,data) )
            self.outbuflen += len(data)

            self.data_ready.notify()
            self.inc_pos()

        def drop( i ):
            # drop packet
            if DEBUG:
                print >>sys.stderr,"vod: trans: %d: dropped pos=%d; deadline expired %.2f sec ago !!!!!!!!!!!!!!!!!!!!!!" % (piece,vs.playback_pos,time.time()-self.piece_due(i))

            self.stat_droppedpieces += 1
            self.stat_pieces.complete( i )
            self.inc_pos()

        for piece in vs.generate_range( vs.download_range() ): 
            ihavepiece = self.has[piece]
            forcedrop = False

            # check whether we have room to store it
            if self.outbuflen > mx:
                # buffer full
                break

            # final check for piece validity
            if ihavepiece:
                data = self.get_piece( piece )
                if not self.valid_piece_data( piece, data ):
                    # I should have the piece, but I don't: WAAAAHH!
                    forcedrop = True
                    ihavepiece = False

            if ihavepiece:
                # have piece - push it into buffer
                if DEBUG:
                    print >>sys.stderr,"vod: trans:                        BUFFER STATUS (max %.0f): %.0f kbyte" % (mx/1024.0,self.outbuflen/1024.0)

                # piece found -- add it to the queue
                push( piece, data )
            else:
                # don't have piece, or forced to drop
                if not vs.dropping and forcedrop:
                    print >>sys.stderr,"vod: trans: DROPPING INVALID PIECE #%s, even though we shouldn't drop anything." % piece
                if vs.dropping or forcedrop:
                    if time.time() >= self.piece_due( piece ) or (vs.pausable and buffer_underrun()) or forcedrop:
                        # piece is too late or we have an empty buffer (and future data to play, otherwise we would have paused) -- drop packet
                        drop( piece )
                    else:
                        # we have time to wait for the piece and still have data in our buffer -- wait for packet
                        if DEBUG:
                            print >>sys.stderr,"vod: trans: %d: due in %.2fs  pos=%d" % (piece,self.piece_due(piece)-time.time(),vs.playback_pos)
                    break
                else: # not dropping
                    if DEBUG:
                        print >>sys.stderr,"vod: trans: %d: not enough pieces to fill buffer." % (piece)
                    break

        self.data_ready.release()

    def video_refillbuf_rawtask( self ):
        self.refill_buffer()

        self.rawserver.add_task( self.video_refillbuf_rawtask, self.REFILL_INTERVAL )

    def pop( self ):
        self.data_ready.acquire()
        vs = self.videostatus

        while vs.prebuffering and not self.done():
            # wait until done prebuffering
            self.data_ready.wait()

        while not self.outbuf and not self.done():
            # wait until a piece is available
            #if DEBUG:
            #    print >>sys.stderr,"vod: trans: Player waiting for data"
            self.data_ready.wait()

        if not self.outbuf:
            piecetup = None
        else:
            piecetup = self.outbuf.pop( 0 ) # nr,data pair
            # Arno, 2010-02-01: Grrrr...
            self.outbuflen -= len(piecetup[1])
            self.playbackrate.update_rate( len(piecetup[1]) )

        self.last_pop = time.time()

        lenoutbuf = len(self.outbuf)

        self.data_ready.release()

        if piecetup:
            self.stat_pieces.set( piecetup[0], "toplayer", time.time() )
            self.stat_pieces.complete( piecetup[0] )

        # Arno, 2010-02-11: STBSPEEDMERGE: Do we want this for STB?
        if vs.pausable:
            # 23/06/09 Boudewijn: because of vlc buffering the self.outbuf
            # almost always gets emptied. This results in periodic (every
            # few seconds) pause signals to VLC. 
            #
            # To 'solve' this we delay the delivery to VLC based on the
            # current buffer size. More delay when there is less data
            # available.
            #
            # 24/06/09 Boudewijn: smaller is (much) better for live as
            # they never get over a certain amount of outstanding
            # pieces. So this will need to be made dependent. VOD can be
            # higher than live.
            if lenoutbuf < 5:
                if lenoutbuf > 0:
                    delay = min(0.1, 3 * 0.1 / lenoutbuf)
                else:
                    delay = 0.1
                if DEBUG: print >>sys.stderr, "Vod: Delaying pop to VLC by", delay, "seconds"
                time.sleep(delay)

        return piecetup


    def notify_playable(self):
        """ Tell user he can play the media, 
        cf. BaseLib.Core.DownloadConfig.set_vod_event_callback()
        """
        #if self.bufferinfo:
        #    self.bufferinfo.set_playable()
        #self.progressinf.bufferinfo_updated_callback()
        
        # triblerAPI
        if self.usernotified:
            return
        self.usernotified = True
        self.prebufprogress = 1.0
        self.playable = True
        
        #print >>sys.stderr,"vod: trans: notify_playable: Calling usercallback to tell it we're ready to play",self.videoinfo['usercallback']
        
        # MIME type determined normally in LaunchManyCore.network_vod_event_callback
        # However, allow for recognition by videoanalyser
        mimetype = self.get_mimetype()
        complete = self.piecepicker.am_I_complete()
        if complete:
            endstream = None
            filename = self.videoinfo["outpath"]
        else:
            stream = MovieTransportStreamWrapper(self)
            if self.videostatus.live_streaming and self.videostatus.authparams['authmethod'] != LIVE_AUTHMETHOD_NONE:
                from BaseLib.Core.Video.LiveSourceAuth import AuthStreamWrapper,VariableReadAuthStreamWrapper

                intermedstream = AuthStreamWrapper(stream,self.authenticator)
                endstream = VariableReadAuthStreamWrapper(intermedstream,self.authenticator.get_piece_length()) 
            else:
                endstream = stream
            filename = None 
            
        # Call user callback
        print >>sys.stderr,"vod:::::::::: trans: notify_playable: calling:",self.vodeventfunc
        try:
            self.vodeventfunc( self.videoinfo, VODEVENT_START, {
                "complete":  complete,
                "filename":  filename,
                "mimetype":  mimetype,
                "stream":    endstream,
                "length":      self.size(),
                "bitrate":   self.videostatus.bitrate,
            } )
        except:
            print_exc()


    #
    # Methods for DownloadState to extract status info of VOD mode.
    #
    def get_stats(self):
        """ Returns accumulated statistics. The piece data is cleared after this call to save memory. """
        """ Called by network thread """
        
        s = { "played": self.stat_playedpieces,
              "late": self.stat_latepieces,
              "dropped": self.stat_droppedpieces,
              "stall": self.stat_stalltime,
              "pos": self.videostatus.playback_pos,
              "prebuf": self.stat_prebuffertime,
              "pp": self.piecepicker.stats,
              "pieces": self.stat_pieces.pop_completed(),
              "firstpiece":self.videostatus.first_piece,
              "npieces":self.videostatus.movie_numpieces}
        return s

    def get_prebuffering_progress(self):
        """ Called by network thread """
        return self.prebufprogress
    
    def is_playable(self):
        """ Called by network thread """
        if not self.playable or self.videostatus.prebuffering:
            self.playable = (self.prebufprogress == 1.0 and self.enough_buffer())
        return self.playable
        
    def get_playable_after(self):
        """ Called by network thread """
        return self.expected_buffering_time()
    
    def get_duration(self):
        return 1.0 * self.videostatus.selected_movie["size"] / self.videostatus.bitrate

    #
    # Live streaming
    #
    def live_invalidate_piece_globally(self, piece, mevirgin=False):
        """ Make piece disappear from this peer's view of BT world.
        mevirgen indicates whether we already downloaded stuff,
        skipping some cleanup if not.
        """
        #print >>sys.stderr,"vod: trans: live_invalidate",piece
                 
        self.piecepicker.invalidate_piece(piece)
        self.piecepicker.downloader.live_invalidate(piece, mevirgin)

    def live_invalidate_piece_ranges_globally(self,toinvalidateranges,toinvalidateset):
        # STBSPEED optimization
        # v = Set()
        for s,e in toinvalidateranges:
            for piece in xrange(s,e+1):
                # v.add(piece)
                self.piecepicker.invalidate_piece(piece)
                
        """
        diffleft = v.difference(toinvalidateset)
        diffright = toinvalidateset.difference(v)
        print >>sys.stderr,"vod: live_invalidate_piece_ranges_globally: diff: in v",diffleft,"in invset",diffright
        assert v == toinvalidateset
        """
        self.piecepicker.downloader.live_invalidate_ranges(toinvalidateranges,toinvalidateset)


    # LIVESOURCEAUTH
    def piece_from_live_source(self,index,data):
        if self.authenticator is not None:
            return self.authenticator.verify(data,index=index)
        else:
            return True
    
