import os
from optparse import OptionParser, OptionGroup
import signal
import sys
import threading
import time

from JSI.ProviderToolbox.Publisher import Publisher, UpdateService
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils import log

_log = log.getLog('seeder')
log.setLevel(log.DEBUG)

class Seeder(object):

    def __init__(self):
        self.parser = None
        self.options = None  
        self.seeder = None
        self.update_service = None

    def run(self):
        """
        Runs the publisher tool, and serves continusly the torrent
        files in default torrent directory
        """
        self.seeder = Publisher.getInstance()
        self.seeder.start()
        self.update_service = UpdateService.getInstance(getattr(self.seeder, "update"), options.update_interval)
        self.update_service.start()

    def update(self):
        self.seeder.update()

    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(0)

    def exit(self):
        self.update_service.stop()
        self.seeder.stop()
        sys.exit(0)


def sigCycleLog(signum, frame):
    logger = log.getLog('')
    log.cycleLevel()
    log.force('Log level has been changed to: ' + str(logger.level))

def sigHup(signum, frame):
    _log.info("Force updating the publisher")
    seeder.update()

def sigTerm(signum, frame):
    _log.info("Terminating the publisher")
    seeder.exit()

if __name__ == "__main__":

    # Signals that control the tool
    signal.signal(signal.SIGUSR1,sigCycleLog)
    signal.signal(signal.SIGTERM,sigTerm)
    signal.signal(signal.SIGHUP,sigHup)

    usage = "usage: %prog [options]\n\n  Runs publisher tool, and serves continusly the torrent files in\n  default torrent directory (" + settings.TORRENT_DIR + ")."

    # Command line options
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-i", "--update-interval", help = "Publisher update interval", action="store", dest="update_interval", default = settings.UPDATE_INTERVAL)
    (options, args) = parser.parse_args()

    seeder = Seeder()
    seeder.parser = parser
    seeder.options = options.__dict__
    thr_seeder = threading.Thread(target=seeder.run)
    thr_seeder.daemon = True

    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The publisher has been called with the following options:")
        for k, v in seeder.options.items():
            _log.debug(k + ": " + str(v))

    thr_seeder.start()

    while True:
        try: time.sleep(3600)
        except KeyboardInterrupt:
            _log.info("Keyboard interrupt caught, quit!")
            seeder.exit()
            break

