# Written by Andrea Reale
# see LICENSE.txt for license information

from __future__ import with_statement
from BaseLib.Core.Subtitles.MetadataDomainObjects.Languages import \
    LanguagesProvider
from BaseLib.Core.Subtitles.MetadataDomainObjects.MetadataExceptions import \
    MetadataDBException, RichMetadataException, DiskManagerException
from BaseLib.Core.CacheDB.Notifier import Notifier
from BaseLib.Core.Subtitles.SubtitleHandler.DiskManager import DiskManager, \
    DISK_FULL_DELETE_SOME, DELETE_OLDEST_FIRST
from BaseLib.Core.Subtitles.SubtitleHandler.SimpleTokenBucket import \
    SimpleTokenBucket
from BaseLib.Core.Subtitles.SubtitleHandler.SubsMessageHandler import \
    SubsMessageHandler
from BaseLib.Core.Utilities import utilities
from BaseLib.Core.Utilities.Crypto import sha
from BaseLib.Core.Utilities.utilities import bin2str, show_permid_short
from BaseLib.Core.simpledefs import NTFY_ACT_DISK_FULL, NTFY_SUBTITLE_CONTENTS, \
    NTFY_UPDATE
import os
import sys




SUBS_EXTENSION = ".srt"
SUBS_LOG_PREFIX = "subtitles: "

DEFAULT_MIN_FREE_SPACE = 0 #no treshold

MAX_SUBTITLE_SIZE = 1 * 1024 * 1024    # 1MB subtitles. too big?
MAX_SUBS_MESSAGE_SIZE = int(2 * MAX_SUBTITLE_SIZE / 1024) #in KBs


MAX_SUBTITLE_DISK_USAGE = 200 * (2 ** 10) #200 MBs

DEBUG = False

class SubtitlesHandler(object):
    
    
    __single = None
    
    def __init__(self):
        # notice that singleton pattern is not enforced.
        # This is better, since this way the code is more easy
        # to test.
        
        SubtitlesHandler.__single = self
        self.avg_subtitle_size = 100 # 100 KB, experimental avg
        self.languagesUtility = LanguagesProvider.getLanguagesInstance()
        

        #instance of MetadataDBHandler
        self.subtitlesDb = None
        self.registered = False
        self.subs_dir = None
        
        
        
        #other useful attributes are injected by the register method
        

    @staticmethod
    def getInstance(*args, **kw):
        if SubtitlesHandler.__single is None:
            SubtitlesHandler(*args, **kw)
        return SubtitlesHandler.__single
    
    def register(self, overlay_bridge, metadataDBHandler, session):
        """
        Injects the required dependencies on the instance.
        
        @param overlay_bridge: a reference to a working instance
                               of OverlayTrheadingBridge
        @param metadataDBHandler: a reference to the current instance of
                           L{MetadataDBHandler}
        @param session: a reference to the running session
        """
        self.overlay_bridge = overlay_bridge
        self.subtitlesDb = metadataDBHandler
        self.config_dir = os.path.abspath(session.get_state_dir())
        subs_path = os.path.join(self.config_dir, session.get_subtitles_collecting_dir())
        self.subs_dir = os.path.abspath(subs_path)
        
        self.min_free_space = DEFAULT_MIN_FREE_SPACE
        self._upload_rate = session.get_subtitles_upload_rate()
        self.max_subs_message_size = MAX_SUBS_MESSAGE_SIZE
        self._session = session
       
        #the upload rate is controlled by a token bucket.
        #a token corresponds to 1 KB.
        #The max burst size corresponds to 2 subtitles of the maximum size (2 MBs)
        tokenBucket = SimpleTokenBucket(self._upload_rate,
                                              self.max_subs_message_size)
       
        self._subsMsgHndlr = SubsMessageHandler(self.overlay_bridge, tokenBucket, 
                                                MAX_SUBTITLE_SIZE)
        self._subsMsgHndlr.registerListener(self)
        
    
        #assure that the directory exists
        
        if os.path.isdir(self.config_dir) :
            if not os.path.isdir(self.subs_dir):
                try:
                    os.mkdir(self.subs_dir)
                except:
                    msg = u"Cannot create collecting dir %s " % self.subs_dir
                    print >> sys.stderr, "Error: %s" % msg
                    raise IOError(msg)
        else:
            msg = u"Configuration dir %s does not exists" % self.subs_dir
            print >> sys.stderr, "Error: %s" % msg
            raise IOError(msg)
        
        
        
           
        diskManager = DiskManager(self.min_free_space, self.config_dir)
        self.diskManager = diskManager
        
        
        dmConfig = {"maxDiskUsage" : MAX_SUBTITLE_DISK_USAGE,
                    "diskPolicy" : DISK_FULL_DELETE_SOME | DELETE_OLDEST_FIRST,
                     "encoding" : "utf-8"}
        self.diskManager.registerDir(self.subs_dir, dmConfig)
        
        freeSpace = self.diskManager.getAvailableSpace()
        if DEBUG:
            print >> sys.stderr, SUBS_LOG_PREFIX + "Avaialble %d MB for subtitle collecting" % (freeSpace / (2 ** 20))
        
        #event notifier
        self._notifier = Notifier.getInstance()
        
        self.registered = True
    
    
    
    
    
    def sendSubtitleRequest(self, permid, channel_id, infohash, languages,
                            callback=None, selversion= -1):
        """
        Send a request for subtitle files. Only called by the OLThread
        
        Send a GET_SUBS request to the peer indentified by permid.
        The request asks for several subtitles file, for a given channel_id
        and torrent infohash. The subtitles file to request are specified
        by the languages parameter that is a list of 3 characters language
        codes.
        
        The contents of a GET_SUBS request are:
            - channel_id: the identifier of the channel for which the subtitles
              were added. (a permid). Binary.
            - infohash: the infohash of the torrent, the subtitles refer to.
              Binary.
            - bitmask:  a 32 bit bitmask (an integer) which specifies the 
              languages requested
                      
        
        
        @param permid: the destination of the request (binary)
        @param channel_id: the identifier of the channel for which the subtitle
                           was added (binary)
        @param infohash: the infohash of a torrent the subtitles refers to (binary).
        @param languages: a list of 3-characters language codes. It must be
                          on of the supported language codes (see Languages)
        @param callback: a function that will be called WHENEVER some of the
                         requested subtitles are received. It must have exactly
                         one parameter that will be bound to a list of 
                         the languages that were received
        @param selversion: the protocol version of the peer whe are sending 
                            the request to
        
        @raise SubtitleMsgHandlerException: if the message failed its attempt to be sent.
                                      Notice that also if the method returns without
                                      raising any exception it doesn't mean
                                      that the message has been sent.
        """
        
        assert utilities.isValidInfohash(infohash), \
            SUBS_LOG_PREFIX + "Invalid infohash %s" % infohash
        assert utilities.isValidPermid(permid), \
            SUBS_LOG_PREFIX + "Invlaid destination permid %s" % permid
        
        assert self.languagesUtility.isLangListSupported(languages), \
             SUBS_LOG_PREFIX + "Some of the languages where not supported"
            

        
        if DEBUG:
            print >> sys.stderr, SUBS_LOG_PREFIX + "preparing to send GET_SUBS to " + \
                  utilities.show_permid_short(permid)
        

        
# Better to leave up to the caller the responsibility to check
# if the subtitle is already available and as correct checsum and so on..
#        onDisk = []
#        for langCode in languages:
#            
#            filename = self.diskManager.isFilenOnDisk(self.subs_dir,
#                    getSubtitleFileRelativeName(channel_id, infohash, langCode))
#            
#            
#            # should I skip this part and just send the request anyway?
#            # (thus leaving to the caller the responsibility to avoid useless
#            # requests)
#            if filename:
#                log.debug(SUBS_LOG_PREFIX + langCode + 
#                          " subtitle already on disk. Skipping it"\
#                          " in the request")
#                onDisk.append(langCode)
#                self._notify_sub_is_in(channel_id, infohash, langCode, filename)
#        
#        for deleteme in onDisk:
#            languages.remove(deleteme)
            
        if len(languages) == 0:
            if DEBUG:
                print >> sys.stderr, SUBS_LOG_PREFIX + " no subtitles to request."
            return
            
        
        if not self.diskManager.tryReserveSpace(self.subs_dir, len(languages) * self.avg_subtitle_size):
            self._warn_disk_full()
            return False
        
        requestDetails = dict()
        requestDetails['channel_id'] = channel_id
        requestDetails['infohash'] = infohash
        requestDetails['languages'] = languages
        
        
        self._subsMsgHndlr.sendSubtitleRequest(permid, requestDetails,
                                                lambda e,d,c,i,b : \
                                                    self._subsRequestSent(e,d,c,i,b),
                                                    callback,
                                                    selversion)
            
        
    
    def _subsRequestSent(self,exception,dest, channel_id, infohash, bitmask ):
        '''
        Gets called when a subtitle request has been succesfully sent.
        '''
        pass

    def receivedSubsRequest(self, permid, request, selversion):
        """
        Reads a received GET_SUBS message and possibly sends a response.
        
        @param permid: the permid of the sender of the GET_SUBS message
        @param request: a tuple made of channel_id, infohash, language code
        @param selversion: the protocol version of the requesting peer
        
        @return: False if the message had something wrong. (a return value
                 of False makes the caller close the connection).
                 Otherwise True
        """
        
        assert self.registered, SUBS_LOG_PREFIX + "Handler not yet registered"

        
        channel_id, infohash, languages = request #happily unpacking
        
        
        #diction {lang : Subtitle}
        allSubtitles = self.subtitlesDb.getAllSubtitles(channel_id,
                                                        infohash)
        
        
        contentsList = {} #{langCode : path}
        #for each requested language check if the corresponding subtitle
        #is available
        for lang in sorted(languages):
            if lang in allSubtitles.keys():
                if allSubtitles[lang].subtitleExists():
                    content = self._readSubContent(allSubtitles[lang].path)
                    if content is not None:
                        contentsList[lang] = content 
                    
                else:
                    if DEBUG:
                        print >> sys.stderr, SUBS_LOG_PREFIX + "File not available for " + \
                              "channel %s, infohash %s, lang %s" % \
                              (show_permid_short(channel_id), bin2str(infohash),
                              lang)
                    self.subtitlesDb.updateSubtitlePath(channel_id,infohash,lang,None)
            else:
                if DEBUG:
                    print >> sys.stderr, SUBS_LOG_PREFIX + "Subtitle not available for " + \
                          "channel %s, infohash %s, lang %s" % \
                          (show_permid_short(channel_id), bin2str(infohash),
                          lang)
        
        if len(contentsList) == 0: #pathlist is empty
            if DEBUG:
                print >> sys.stderr, SUBS_LOG_PREFIX + "None of the requested subtitles " + \
                      " was available. No answer will be sent to %s" % \
                      show_permid_short(permid)
            return True
        
        
        
        return self._subsMsgHndlr.sendSubtitleResponse(permid, 
                                                (channel_id,infohash,contentsList), 
                                                selversion)

        
        
    
    def _readSubContent(self,path):

        try:
            relativeName = os.path.relpath(path, self.subs_dir)
            fileContent = self.diskManager.readContent(self.subs_dir,
                                                       relativeName)
        except IOError,e:
            if DEBUG:
                print >> sys.stderr, SUBS_LOG_PREFIX + "Error reading from subs file %s: %s" % \
                 (relativeName, e)
            fileContent = None
            
        if fileContent is not None and len(fileContent) <= MAX_SUBTITLE_SIZE:
            return fileContent
        else:
            print >> sys.stderr, "Warning: Subtitle %s dropped. Bigger then %d" % \
                (relativeName, MAX_SUBTITLE_SIZE)
            return None
                

            
        

    
   
        
    def _subs_send_callback(self, exception, permid):
        """
        Called by the overlay thread when the send action is completed
        """
        if exception is not None:
            if DEBUG:
                print >> sys.stderr, SUBS_LOG_PREFIX + "Failed to send metadata to %s: %s" % \
                      (show_permid_short(permid), str(exception))
        
    
    def receivedSubsResponse(self, permid, msg, callbacks, selversion):
        """
        Handles the reception of a SUBS message.
        
        Checks against integrity of the contents received in a SUBS message.
        If the message containes one or more subtitles that were not requested
        they are dropped.
        If the message is bigger in size then MAX_SUBS_MSG_SIZE it is dropped.
        If one subtitle is bigger in size then MAX_SUBTITLE_SIZE it is dropped.
        Otherwise the message is decoded, the subtitles saved to disk, and 
        their path added to database.
        
        @param permid: the permid of the sender
        @param msg: a triple of channel_id, infohash, and the contentsDictionary
        @param callbacks: a list of pairs. The first element is a function to call,
            the second a bitmask that help building back the parameters
            of the function
        @param selversion: the protocol version number of the other peer
        
        
        @return: False if the message is dropped becuase malformed. 
        """
        assert self.registered == True, SUBS_LOG_PREFIX + "Subtitles Handler"\
            " is not registered"
        
    
        channel_id, infohash, contentsDictionary = \
            msg
        
        
        metadataDTO = self.subtitlesDb.getMetadata(channel_id, infohash)
        
        assert metadataDTO is not None, SUBS_LOG_PREFIX + "Inconsistent " \
            "subtitles DB: a requested subtitle was not available in the db"
        
        filepaths = dict()
        somethingToWrite = False
        
        for lang, subtitleContent in contentsDictionary.iteritems():
            try:
                filename = self._saveSubOnDisk(channel_id, infohash, lang,
                                               subtitleContent)
                filepaths[lang] = filename
            except IOError,e:
                if DEBUG:
                    print >> sys.stderr, SUBS_LOG_PREFIX + "Unable to save subtitle for "\
                          "channel %s and infohash %s to file: %s" % \
                          (show_permid_short(channel_id), str(infohash), e)
                continue
            except Exception,e:
                if DEBUG:
                    print >> sys.stderr, "Unexpected error copying subtitle On Disk: " + str(e)
                raise e
            
            subToUpdate = metadataDTO.getSubtitle(lang)
            if subToUpdate is None:
                print >> sys.stderr, "Warning:" + SUBS_LOG_PREFIX + "Subtitles database inconsistency."
                #is it ok to throw a runtime error or should I gracefully fail?
                raise MetadataDBException("Subtitles database inconsistency!")
            
            subToUpdate.path = filename
            if not subToUpdate.verifyChecksum():
                if DEBUG:
                    print >> sys.stderr, "Received a subtitle having invalid checsum from %s" % \
                         show_permid_short(permid)
                subToUpdate.path = None
                
                relativeName = os.path.relpath(filename, self.subs_dir)
                self.diskManager.deleteContent(self.subs_dir, relativeName)
                continue
            self.subtitlesDb.updateSubtitlePath(channel_id, infohash, subToUpdate.lang, filename, False)
            somethingToWrite = True
        
        if somethingToWrite:
            self.subtitlesDb.commit()
        
        if DEBUG:    
            print >> sys.stderr, "Subtitle written on disk and informations on database."
        
        self._scheduleUserCallbacks(callbacks)
        
        return True
            
                
    def _scheduleUserCallbacks(self, callbacks):
        
        # callbacks is a list of tuples such as
        # (callback_func, bitmask)
        for entry in callbacks:
            callback = entry[0]
            if callback is None:
                pass
            else:
                listOfLanguages = self.languagesUtility.maskToLangCodes(entry[1])
                def callBack():
                    to_call = callback
                    return to_call(listOfLanguages)
                # Commented because had a problem related to the
                # scope of the closure
                #toCall = lambda : callback(listOfLanguages)
                self.overlay_bridge.add_task(callBack)

        
        
        
        
    
    def _saveSubOnDisk(self, channel_id, infohash, lang, subtitleContent):
        assert self.registered == True, SUBS_LOG_PREFIX + "Subtitles Handler"\
            " is not registered"
            
        filename = getSubtitleFileRelativeName(channel_id, infohash, lang)
        
        path = self.diskManager.writeContent(self.subs_dir,
                                             filename, subtitleContent)
            
        return path

    
    
    def _notify_sub_is_in(self, channel_id, infohash, langCode, filename):
        """
        Notify that a subtitle file is available.
        
        Notifies any interested receiver that a subtitle for 
        (channel_id, infohash, langCode) is available in the file
        located at path filename.
        
        Currently it just prints a cool debug message.
        """
        if DEBUG:
            print >> sys.stderr, SUBS_LOG_PREFIX + "Subtitle is in at" + filename
        
        if self._notifier is not None:
            self.notifier.notify(NTFY_SUBTITLE_CONTENTS, NTFY_UPDATE,
                                 (channel_id, infohash), langCode, filename)
    
    
    def _warn_disk_full(self):
        """
        Notifies the LaunchMany instance that the disk is full.
        """
        print >> sys.stderr, "Warning: " + SUBS_LOG_PREFIX + "GET_SUBS: Disk full!"
        drive, rdir = os.path.splitdrive(os.path.abspath(self.subs_dir))
        if not drive:
            drive = rdir
        self.launchmany.set_activity(NTFY_ACT_DISK_FULL, drive)
        

      
    def setUploadRate(self, uploadRate):
        """
        Sets the subtitles uploading rate, expressed in KB/s
        """
        assert self.registered
        
        self._upload_rate = float(uploadRate)
        self._subsMsgHndlr._tokenBucket.fill_rate = float(uploadRate)

    def getUploadRate(self):
        """
        Returns the current setting for the subtitles upload rate, in KB/s
        """
        return self._upload_rate
    
    def delUploadRate(self):
        """
        No, you can't delete the upload_rate property
        """
        raise RuntimeError("Operation not supported")
    
    upload_rate = property(getUploadRate, setUploadRate, delUploadRate,
                           "Controls the subtitles uploading rate. Expressed in KB/s")
    
    
    def copyToSubtitlesFolder(self,pathToMove, channel_id, infohash, langCode):
        """
        Given the path to an srt, moves it to the subtitle folder, also
        changing the name to the correct one
        
        @return: the complete path of the file if the file was succesfully copied,
        
        @raise RichMetadataException: if the subtitle cannot be copied.
        
        """
        
        if not os.path.isfile(pathToMove):
            raise RichMetadataException("File not found.")
        
        if os.path.getsize(pathToMove) >= MAX_SUBTITLE_SIZE :
            raise RichMetadataException("Subtitle bigger then %d KBs" % (MAX_SUBTITLE_SIZE/1024))
        
        # Not really strong check: anyone can change the extension of a file :)
        if not pathToMove.endswith(SUBS_EXTENSION):
            raise RichMetadataException("Only .srt subtitles are supported")
        
        filename = getSubtitleFileRelativeName(channel_id, infohash, langCode)

        
        if self.diskManager.isFilenOnDisk(self.subs_dir, filename):
            if DEBUG:
                print >> sys.stderr, "Overwriting previous subtitle %s" % filename
            try:
                deleted = self.diskManager.deleteContent(self.subs_dir, filename)
            except DiskManagerException,e:
                if DEBUG:
                    print >> sys.stderr, "Unable to remove subtitle %s" % filename
                raise RichMetadataException("Unable to remove subtile %s to overwrite: %s"\
                                            % (filename, str(e)))
            
            if not deleted:
                if DEBUG: 
                    print >> sys.stderr, "Unable to remove subtitle %s" % filename
                raise RichMetadataException("Old subtitle %s is write protected"% filename)
        
        
        with open(pathToMove,"rb") as toCopy:
            encoding = toCopy.encoding
            content = toCopy.read()
            
        if encoding is not None:
            #convert the contents from their original encoding 
            # to unicode, and replace possible unknown characters
            #with U+FFFD
            content = unicode(content, encoding, 'relplace')
        else:
            #convert using the system default encoding
            content = unicode(content, errors="replace")
        
        return self.diskManager.writeContent(self.subs_dir, filename, content)


    def getMessageHandler(self):
        return self._subsMsgHndlr.handleMessage                
        

        
    
    
        
def getSubtitleFileRelativeName(channel_id, infohash, langCode):
    #subtitles filenames are build from the sha1 hash
    #of the triple (channel_id, infohash, langCode)
    
    # channel_id and infohash are binary versions
    
    assert utilities.validPermid(channel_id), \
        "Invalid channel_id %s" % utilities.show_permid_short(channel_id)
    assert utilities.validInfohash(infohash), \
        "Invalid infohash %s" % bin2str(infohash)
    assert LanguagesProvider.getLanguagesInstance().isLangCodeSupported(langCode), \
        "Unsupported language code %s" % langCode
        
    hasher = sha()
    for data in (channel_id, infohash, langCode):
        hasher.update(data)
    subtitleName = hasher.hexdigest() + SUBS_EXTENSION
        
    return subtitleName


