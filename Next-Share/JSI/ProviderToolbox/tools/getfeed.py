import json
import os
import sys
from optparse import OptionParser, OptionGroup

from JSI.ProviderToolbox.ContentSource import Channel, ContentUnit, RTVVoDContent
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils import log

_log = log.getLog('getfeed')
log.setLevel(log.DEBUG)

class GetFeed(object):

    def __init__(self):
        self.rmg = RichMetadataGenerator.getInstance()
        self.parser = None
        self.options = None  
        self.mapper = {'RTVVoDContent': RTVVoDContent(),
                       'BBC': ContentUnit()}

    def run(self):
        """
        Runs the getfeed tool, fetches the content, generate torrents
        and provides P2P-Next compliant feed on std out
        """
        channel = None
        if options.location != None:
            template = None
            if options.template:
                if self.mapper.get(options.template):
                    template = self.mapper[options.template]
            channel = Channel.getContentSource(options.location, 
                                               options.publish,
                                               template,
                                               options.feedexport,
                                               options.didbaseFile,
                                               options.window)
            _log.info("Feed is stored in path: %s",
                      channel.storage)
            _log.info("Resulting torrent files reside in path: %s",
                      settings.TORRENT_DIR)
            _log.info("DID Base used path: %s", options.didbaseFile)
            _log.info("Resulting feed should be published at location: %s",
                      channel.getExportFeedLink())
        elif options.directory != None:
            self.checkFeedDir(options.directory)
            c = Channel()
            channel = c.getCSFromDir(options.directory)
            if channel.location.startswith("file"):
                _log.debug("Mannually created feed in the directory %s, won't update", options.directory)
            else:
                channel.update()
                if options.fresh or options.contentfresh:
                    print ",".join(channel.getFresh(options.contentfresh))
                    self.exit()
        elif options.feeddir != None:
            self.checkFeedDir(options.feeddir)
            c = Channel()
            channel = c.getCSFromDir(options.feeddir)
        else:
            self.exitOnInputError("Neither location (-l), update directory (-u)\n                    or feed directory (-f) were specified.")
        # When all is done decide for std out
        if channel:
            if not options.json:
                print self.rmg.prettyPrint(channel.exportFeed(options.guid, options.image), 'utf-8')
            else:
                channel.exportFeed(options.guid, options.image)
                e = channel.getJsonExports()
                print json.dumps(e)


    def checkFeedDir(self, feedDir):
        if not os.path.exists(feedDir) or not os.path.isdir(feedDir):
            self.exitOnInputError("Feed directory is missing in path or is not a directory:\n                    " + feedDir) 
        if not os.path.exists(os.path.join(feedDir, settings.CONTENT_SOURCE_PROPERTIES)):
            self.exitOnInputError("Feed directory specified seems not to be populated.\n                    Feed properties file is missing in path: " + feedDir)

    def exit(self):
        sys.exit(0)

    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(1)

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Gets a feed content and metadata, creates torrent files and outputs P2P-Next\n  compliant feed on std out. Consult tool help (-h) for more options."

    # Command line options
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-l", "--location", help = "Location of the input feed", action="store", dest="location", default = None)
    parser.add_option("-p", "--publish", help = "Location of the absolute publishing link, default " + settings.CONTENT_PUBLISHING_LINK, action="store", dest="publish", default = settings.CONTENT_PUBLISHING_LINK)
    parser.add_option("-t", "--content-template", help = "Name of the content template (class) to use in exporting feed content, for example 'RTVVoDContent'", action="store", dest="template", default = None)
    parser.add_option("-e", "--export-link", help = "Location of the exported feed, default " + settings.EXPORT_FEED_LINK + " appended with the name of the feed (directory) with xml extension", action="store", dest="feedexport", default = settings.EXPORT_FEED_LINK)
    parser.add_option("-g", "--feed-id", help = "Feed identifier", action="store", dest="guid", default = None)
    parser.add_option("-i", "--feed-image", help = "Feed image", action="store", dest="image", default = None)
    parser.add_option("-d", "--did-base-file", help = "Common feed DID base file", action="store", dest="didbaseFile", default = None)
    parser.add_option("-w", "--window", help = "A number of content units to keep, None (default) collect, 0 same as source", action="store", dest="window", default = None)
    parser.add_option("-u", "--update", help = "Update the feed in specified directory and print fresh feed on std out", action="store", dest="directory", default = None)
    parser.add_option("-f", "--feed", help = "Print the feed of the specified feed directory. Feed guid (-g) or image (-i) can be specified on the command line as well", action="store", dest="feeddir", default = None)
    parser.add_option("-r", "--fresh", help = "Return instead of the feed the identifiers of the fresh content units are returned, requires update option (-u). The feed can be then obtained with feed option (-f).", action="store_true", dest="fresh", default = False)
    parser.add_option("-c", "--fresh-content", help = "Return instead of the feed the content files of the fresh content units, requires update option (-u). The feed can be then obtained with feed option (-f).", action="store_true", dest="contentfresh", default = False)
    parser.add_option("-j", "--json", help = "Returns a feed data in json format. Used only with location (-l), update (-u) and feed (-f) option.", action="store_true", dest="json", default = False)
    (options, args) = parser.parse_args()

    getfeed = GetFeed()
    getfeed.parser = parser
    getfeed.options = options.__dict__
    
    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The getfeed has been called with the following options:")
        for k, v in getfeed.options.items():
            _log.debug(k + ": " + str(v))

    try:
        getfeed.run()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt caught, quit!")
        getfeed.exit()
