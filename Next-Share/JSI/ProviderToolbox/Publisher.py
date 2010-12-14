import binascii
import os
import time
from threading import Thread

from JSI.ProviderToolbox.utils import log 
from JSI.ProviderToolbox.utils.utilities import Service, strtime
from JSI.ProviderToolbox.conf import settings

# Import after the JSI imports so the logging gets properly
# initialized
from BaseLib.Core.Session import *
from BaseLib.Core.SessionConfig import *
from BaseLib.Core.DownloadConfig import DownloadStartupConfig
from BaseLib.Core.TorrentDef import TorrentDef

_log = log.getLog('TestPublisher')
log.setLevel(log.DEBUG)


__author__ = 'D. Gabrijelcic (dusan@e5.ijs.si)'
__revision__ = '0.2'
__all__ = ['Publisher', 'UpdateService']


class Publisher(Service):

    __single = None
    plock = RLock()


    def __init__(self, working_directory=None, config_file=None):
        Service.__init__(self)
        # Running config
        self.config = None
        # Executable path
        self.install_path = None
        # Session config
        self.ssc = None
        # Session
        self.session = None
        # Directory to store torrent files
        self.torrent_dir = None
        # What is published (infohash, download)
        self.publications = {}
        # Where the content resides (content, directory mapping)
        self.content = {}
        # Torrent files mapping (torrent file, infohash)
        self.torrents = {}
        # Content to torrent mapping
        self.cont2torr = {}
        self.__init(working_directory, config_file)
        Publisher.__single = self

    def getInstance(*args, **kw):
        if Publisher.__single is None:
            Publisher.plock.acquire()
            try:
                Publisher(*args, **kw)
            finally:
                Publisher.plock.release()
        return Publisher.__single
    getInstance = staticmethod(getInstance)

    def __init(self, working_directory, config_file):        
        self.install_path = self.getInstallPath()
        if working_directory != None:
            self.working_directory = working_directory
        else:
            self.working_directory = settings.TORRENT_SERVER_DEFAULT_DIRECTORY
        if config_file != None:
            self.config_file = config_file
        if not os.path.isdir(self.working_directory):
            try: 
                os.makedirs(self.working_directory)
                _log.debug("Working directory created: " + self.working_directory)
            except Exception, e:
                _log.warn("Cannot create specified working directory: '" + self.working_directory + "'.")
                return None
        if self.config_file == None:
            try:
                self.config_file = Session.get_default_config_filename(self.working_directory)
                self.ssc = SessionStartupConfig.load(self.config_file)
            except:
                # Directory exists but config file could not be loaded
                # Load defaults
                self.ssc = SessionStartupConfig()
        else: # Session config file is supplied, load
            try:
                self.ssc = SessionStartupConfig.load(self.config_file)
            except:
                _log.warn("Cannot load supplied config file '" + self.config_file + "'.")
                return None
        self.config = self.ssc.sessconfig
        self.config['state_dir'] = self.working_directory
        self.torrent_dir = settings.TORRENT_DIRECTORY
        _log.debug("Setting defaults")
        self.setServerDefaults()
        self.initializeServer()
        _log.debug(self.configuration())

    def getInstallPath(self):
        """ Returns the path in filesystem the server was run from."""
        return os.path.abspath('.')

    def setServerDefaults(self):
        # Set server session defaults, more related to ability to
        # start limitations then real defaults. 
        _log.debug("Setting torrent server defaults")
        if settings.INTERNAL_TRACKER_IP != None:
            self.ssc.set_ip_for_tracker(settings.INTERNAL_TRACKER_IP)
        if settings.INTERNAL_TRACKER_PORT != None:
            self.ssc.set_listen_port(settings.INTERNAL_TRACKER_PORT)
        self.ssc.set_megacache(settings.MEGACACHE)
        self.ssc.set_overlay(settings.OVERLAY)
        self.ssc.set_buddycast(settings.BUDDYCAST)
        self.ssc.set_download_help(settings.DOWNLOAD_HELP)
        self.ssc.set_torrent_collecting(settings.TORRENT_COLLECTING)
        self.ssc.set_torrent_checking(settings.TORRENT_CHECKING)
        self.ssc.set_dialback(settings.DIALBACK)
        self.ssc.set_social_networking(settings.SOCIAL_NETWORKING)
        self.ssc.set_remote_query(settings.REMOTE_QUERY)
        self.ssc.set_bartercast(settings.BARTERCAST)
        self.ssc.set_internal_tracker(settings.INTERNAL_TRACKER)
        self.ssc.set_mainline_dht(settings.DHT)
        self.ssc.set_superpeer(settings.SUPERPEER)
        self.ssc.set_nat_detect(settings.NAT_DETECT)
        self.ssc.set_crawler(settings.CRAWLER)
        self.ssc.set_multicast_local_peer_discovery(settings.PEER_DISCOVERY)
        self.ssc.set_start_recommender(settings.START_RECOMMENDER)
        self.ssc.set_install_dir(self.install_path)

    def initializeServer(self):
        if not os.path.exists(self.torrent_dir):
            os.makedirs(self.torrent_dir)
        else:
            if not os.path.isdir(self.torrent_dir):
                _log.warn("Torrent directory specified is not a directory: %s", self.torrent_dir)

    def configuration(self, watch=None):
        out = 'Server configuration:\n'
        if self.config != None:
            for key in self.config.keys():
                if watch != None:
                    if key in watch:
                        out += ":-> " + key + ": " + unicode(self.config[key]) + "\n"
                else:
                    out += ":-> " + key + ": " + unicode(self.config[key]) + "\n"
        return out

    def start(self):
        _log.debug("Starting the server of type %s.", self.type)
        self.session = Session(self.ssc)
        if settings.SHUT_UP_OTHER_LOGGERS:
            log.shutUpOtherLoggers()
        # Try to load all existing dowloads, if any
        _log.info("Checkpointing the torrent server in working directory %s", self.working_directory)
        self.session.load_checkpoint()
        self.findContent()
        self.findShared()
        new = self.exportTorrents()
        self.running = True
        _log.info("Server is checkpointed, %s new exports shared and serving %d content items", new, len(self.publications))

    def stop(self):
        if self.running == True:
            self.session.shutdown()
            time.sleep(settings.SERVER_SLEEP_ON_EXIT)
            self.running = False
        else:
            _log.warn("Trying to stop idle server with working directory: " + self.working_directory)

    def exportTorrents(self):
        """
        Exports all torrent in the default torrent dir. Does nothing
        if the ContentSource lock file is found in the
        directory. Waits for the next update.
        """
        if os.path.isdir(self.torrent_dir):
            torr = os.listdir(self.torrent_dir)
            torr.sort()
            for t in torr:
                if t.startswith(settings.LOCK):
                    _log.debug("Lock hit, waiting for the next update.")
                    return
            c = 0
            for t in torr:
                if t.endswith('tstream') or t.endswith('url'):
                    if self.share(os.path.join(self.torrent_dir, t)):
                        c += 1
            return c

    def share(self, torrent_file):
        """
        Shares a content unit torrent. Updates bindings between (1)
        infohashes and Download instances (publications), (2) torrent
        files and infohashes (torrents) and (3) content and torrent
        files (cont2torr). If the publication already exists only the
        (2) and (3) will be updated. Publications (1) are already
        updated in findShared method.
        """
        if os.path.exists(torrent_file):
            tdef = TorrentDef.load(torrent_file)
            files = tdef.get_files()
            # Still sharing only one file
            if len(files) == 1:
                f = files[0]
                if self.content.get(f):
                    ih = binascii.hexlify(tdef.get_infohash())
                    if self.publications.get(ih):
                        self.torrents[os.path.basename(torrent_file)] = ih
                        self.cont2torr[f] = os.path.basename(torrent_file)
                        return
                    _dscfg = DownloadStartupConfig()
                    _dscfg.set_dest_dir(self.content[f])
                    self.session.add_to_internal_tracker(tdef)
                    download = self.session.start_download(tdef, _dscfg)
                    self.publications[ih] = download
                    self.torrents[os.path.basename(torrent_file)] = ih
                    self.cont2torr[f] = os.path.basename(torrent_file)
                    return True
                else:
                    _log.error("No directory mapping provided for the torrent file: %s, sharing a file %s!", torrent_file, f)
            else:
                _log.error("At the moment only a single file torrent could be shared, not multiple file as specified: %s in case of torrent file %s!", files, torrent_file)
        else:
            _log.error("Trying to share nonexistent torrent file: %s!", torrent_file)

    def findContent(self):
        """
        Finds publishable content in the feeds, e.g. all content not
        beeing xml or feed properties. Clears and fills the dict
        content with content as a key and corresponding directory as a
        value. Hopes at the moment that symbolic links are shared as
        well with Next-Share (manually created feeds).
        """
        self.content.clear()
        if os.path.isdir(settings.MEDIA_ROOT):
            feeds = os.listdir(settings.MEDIA_ROOT)
            for f in feeds:
                fd = os.path.join(settings.MEDIA_ROOT, f)
                if os.path.exists(os.path.join(fd, settings.CONTENT_SOURCE_PROPERTIES)):
                    content = os.listdir(fd)
                    t = list()
                    for c in content:
                        if not c.endswith(settings.METADATA_EXT) and c != settings.CONTENT_SOURCE_PROPERTIES:
                            t.append(c)
                    for c in t:
                        self.content[c] = fd

    def findShared(self):
        down = self.session.get_downloads()
        for d in down:
            tdef = d.get_def()
            ih = binascii.hexlify(tdef.get_infohash())
            self.publications[ih] = d


    def update(self):
        # Lock guards against being called too soon if a lot of new
        # content is comming in
        self.plock.acquire()
        oldcontent = self.content.copy()
        self.findContent()
        removed = list()
        for k in oldcontent:
            if not self.content.get(k):
                removed.append(k)
        cr = 0
        for r in removed:
            torr = None
            if self.cont2torr.get(r):
                torr = self.cont2torr[r]
            else:
                _log.error("Programmable error, trying to remove content %s without registred torrent file", r)
                continue
            infohash = None
            if self.torrents.get(torr):
                infohash = self.torrents[torr]
            else:
                _log.error("Programmable error, trying to remove content %s with torrent file %s but no registred infohash", r, torr)
                continue
            if self.unshare(infohash):
                del self.cont2torr[r] # content is already updated
                _log.debug("Publication of content %s with torrent file %s has been unshared.", r, torr)
                cr += 1
        # takes care of new arrivals
        new = self.exportTorrents()
        _log.info("Publisher has been updated, %s torrents were added and %s removed, serving %d", new, cr, len(self.publications))
        self.plock.release()

    def unshare(self, infohash):
        """
        Unshares a torrent file. Removes bindings in publications and
        torrents being published.

        @param infohash Infohash as hexlified string
        @return True if removed othervise False
        """
        if self.publications.get(infohash):
            download = self.publications[infohash]
            torr = None
            for k, v in self.torrents.items():
                if v == infohash:
                    torr = k
                    break
            if download != None:
                try:
                    self.session.remove_download(download)
                    del self.publications[infohash]
                    if torr:
                        del self.torrents[torr]
                        return True
                    else:
                        _log.error("Programmable error, trying to remove nonexistent torrent with infohash: %s", infohash)
                except Exception, e:
                    _log.error("Unable to remove the publication with infohash %s of the torrent %s, exception thrown: '%s'", infohash, torrent, e)
                    if settings.LOG_LEVEL == log.DEBUG:
                        _mye = ServerError(e)
                        _mye.trace()
            else:
                _log.error("Download is undefined, cannot remove the publication with infohash %s for torrent file %s!", infohash, torr)
        else:
            _log.warn("Trying to remove non existing publication with infohash %s", infohash)
        return False

    def status(self):
        return "Serving in total " + str(len(self.publications)) + " torrents"

    def run(self):
        return self.status()

class UpdateService(Service):

    def __init__(self):
        Service.__init__(self, "Update")
        self.updater = None
        self.waitTime = 2

    def getInstance(method, updateInterval=settings.UPDATE_INTERVAL):
        us = UpdateService()
        us.updater = Updater(method, updateInterval)
        return us
    getInstance = staticmethod(getInstance)

    def stop(self):
        _log.info(self.status())
        _log.info("Update service terminating.")
        self.updater.working = False
        self.updater.join(self.waitTime)
        self.running = False

    def start(self):
        self.running = True
        self.updater.start()

    def setInterval(self, updateInterval):
        """
        Sets global interval for the update
        """
        if updateInterval > 5:
            self.updater.setInterval(updateInterval)
            _log.info("The update interval set to %d seconds.", updateInterval)
        else:
            _log.warn("Trying to set update interval to unreasonable value (%d)", updateInterval)

    def status(self):
        out = "Updater status: "
        out += "running: " + str(self.running) + ", "
        out += "update interval: " + str(self.updater.getInterval()) + ", "
        out += "updates: " + str(self.updater.getCounter()) + ", "
        out += "running time: " + strtime(self.updater.getRunTime())
        return out + "\n"

class Updater(Thread):

    def __init__(self, method, updateInterval=None):
        Thread.__init__(self)
        self.updateInterval = updateInterval
        self.counter = 0
        self.startTime = int(time.time())
        self.keepCounter = 0
        self.method = method
        self.steps = 0
        self.working = True
        self.stepping = False
        self.intervalChanged = False

    def setInterval(self, updateInterval):
        self.keepCounter = self.getCounter()
        self.counter = 0
        self.updateInterval = updateInterval
        self.intervalChanged = True
        
    def getInterval(self):
        if self.stepping:
            return self.steps*2
        return self.updateInterval

    def getRunTime(self):
        return int(time.time()) - self.startTime

    def getCounter(self):
        return self.keepCounter + self.counter

    def calcSteps(self):
        if self.updateInterval > 2:
            self.steps = self.updateInterval/2
            self.stepping = True
        else:
            self.steps = 1

    def run(self):
        # All isuses with the steps, two while loops, working and
        # changed var is being able to interupt the loop
        # gracefully on exit as well to adapt the update interval.
        while True:
            self.calcSteps()
            # A string is required for calling remote interface
            self.method()
            self.counter += 1
            i = 0
            while i <= self.steps: 
                i += 1
                if self.working: 
                    if self.intervalChanged:
                        # Step out of the inner loop ...
                        i = self.steps + 1
                        self.intervalChanged = False
                    else:
                        time.sleep(2)
                else:
                    return

