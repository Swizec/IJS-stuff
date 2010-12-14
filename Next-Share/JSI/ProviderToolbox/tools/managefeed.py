import os
import sys
from optparse import OptionParser, OptionGroup

from JSI.ProviderToolbox.ContentSource import ContentSource, Channel, ContentUnit, RTVVoDContent, classpath
from JSI.ProviderToolbox.FeedGenerator import P2PNextAtomFeed
from JSI.ProviderToolbox.MetadataGenerator import Item, Media
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils import log
from JSI.ProviderToolbox.utils.utilities import textify, classImport
from JSI.RichMetadata.conf import metadata

_log = log.getLog('managefeed')
log.setLevel(log.DEBUG)

class ManageFeed(object):

    def __init__(self):
        self.rmg = RichMetadataGenerator.getInstance()
        self.parser = None
        self.options = None  

    def run(self):
        """
        Runs the managefeed tool and creates a feed according to specified
        options or modifies feed content (items)
        """
        core = None
        rmg = RichMetadataGenerator.getInstance()
        if options.coremetafile:
            core = rmg.getRichMetadata(options.coremetafile)                
            if core:
                if core.metadataType != metadata.METADATA_CORE:
                    self.exitOnInputError("Core metadata of wrong type: " + core.metadataType)
            else:
                self.exitOnInputError("Cannot read core metadata from supplied file: " + options.coremetafile)
        # Creates a feed
        if options.feedmod:
            if not options.title and not options.coremetafile:
                self.exitOnInputError("Feed title or core metadata must be defined")
            channel = Channel()
            if core:
                if not core.getTitleMain():
                    self.exitOnInputError("Feed title or core metadata title mainmust be defined")
                channel.name = core.getTitleMain()
                channel.metadata = core
            else:
                channel.name = options.title
            channel.storage = settings.MEDIA_ROOT + os.path.sep + textify(channel.name)
            channel.location = "file://" + channel.storage
            channel.identifier = channel.identify(channel.location)
            if options.cuci:
                cuci = classImport(classpath, options.cuci)
                if cuci:
                    channel.contentUnitClassInstance = cuci.__class.__name__
                    channel.cuci = cuci
            if os.path.isdir(channel.storage):
                channel = channel.restore(channel.storage, channel)
                if core: # core metadata supplied on command line, prevail
                    channel.metadata = core
            if options.publish:
                channel.publish = options.publish
            if options.exporturl:
                channel.exportFeedLink = options.exporturl
            if options.didbase:
                channel.setDIDBaseFile(options.didbase)
            if options.image:
                channel.image = options.image
            if not core:
                core = rmg.getRichMetadata()
            old = core
            if options.language:
                core.setLanguage(options.language)
            if options.description:
                core.setTitleSeriesTitle(options.description)
            if options.publisher:
                core.setPublisher(options.publisher)
            if options.originator:
                core.setOriginator(options.originator)
            if options.title:
                core.setTitleMain(options.title)
            if core != old or not channel.metadata:
                channel.metadata = core
            channel.store(True)
        # Adds an item to the feed
        elif options.additem:
            if not options.feeddir:
                self.exitOnInputError("For adding the feed item feed directory needs\n                    to be specified! (-d option)")
            if not os.path.exists(os.path.join(options.feeddir, settings.CONTENT_SOURCE_PROPERTIES)):
                self.exitOnInputError("Feed directory specified seems not to be populated.\n                    Feed properties file is missing in path: " + options.feeddir)
            c = Channel()
            channel = c.restore(options.feeddir)
            cu = channel.getContentUnitInstance()
            cu.acquire = channel.acquire
            if options.content:
                if os.path.exists(options.content) and os.path.isfile(options.content):
                    cu.contentFile = os.path.basename(options.content)
                else:
                    self.exitOnInputError("Content file is missing in path or is not a file:\n                    " + options.content)
            else:
                self.exitOnInputError("Content file should be specified while adding an item")
            item = Item()
            item._items.append(Media.getMetadata(options.content))
            if not core: 
                core = rmg.getRichMetadata()
            if options.title:
                core.setTitleEpisodeTitle(options.title)
            if options.synopsis:
                core.setSynopsis(options.synopsis)
            # Problem turned round. From RM set the item attributes
            for k, v in settings.MMM_ITEM.items():
                if v:
                    m = "get" + v.lstrip("set")
                    f = getattr(core, m)
                    setattr(item, k, f())
            if options.coremetafile:
                cu.metadata = item.getRichMetadata(core)
            else:
                cu.metadata = item.getRichMetadata(channel.metadata)
            cu.name = cu.metadata.getTitleEpisodeTitle()
            cu.identifier = cu.identify()
            if cu.identifier in channel.items:
                self.exitOnInputError("You are trying to add the content " + options.content + " with metadata that seems already added to the feed with name " + channel.name)
            cu.feedStore = channel.storage
            (b, e) = os.path.splitext(cu.contentFile)
            cu.storeMeta(os.path.join(channel.storage, b))
            if channel.storage != os.path.basename(options.content):
                if os.path.exists(os.path.join(channel.storage, cu.contentFile)):
                    self.exitOnInputError("You are trying to add the content " + cu.contentFile + "\n                    to the feed with name '" + channel.name + "' that already\n                    exists in the feed.")     
                os.symlink(options.content, os.path.join(channel.storage, cu.contentFile))
            cu.fresh = True
            channel.items[cu.identifier] = cu
            channel.exportTorrent()
        # Removes the item
        elif options.removeitem:
            if not options.feeddir:
                self.exitOnInputError("For removing the feed item feed directory needs to be\n                        specified (-d option)!")
            if os.path.exists(options.feeddir) and os.path.isdir(options.feeddir):
                c = Channel()
                channel = c.restore(options.feeddir)
                if channel.items.has_key(options.removeitem):
                    channel.removeContentUnit(options.removeitem)
                else:
                    self.exitOnInputError("Cannot remove nonexistent content unit, identifier " + options.removeitem + " not registred")
            else:
                self.exitOnInputError("Feed directory is missing in path or is not a directory:\n                    " + options.feeddir)                
        # List the feed
        elif options.list:
            if os.path.exists(options.list) and os.path.isdir(options.list):
                c = Channel()
                channel = c.getCSFromDir(options.list)
                if options.listlong:
                    print channel.toString()
                else:
                    print "'" + channel.name + "', stored in " + channel.storage
                    print "Location: " + channel.location
                    i = 1
                    sitems = channel.timesort.sort()
                    sitems.reverse()
                    for k in sitems:
                        if channel.items.get(k):
                            v = channel.items[k]
                            print '{0:>3}'.format(i) + ") " + v.name 
                            print "     Identifier: " + v.identifier
                            print "     Content:    " + v.contentFile
                            print "     Metadata:   " + v.metaFile
                            print "     Torrent:    " + str(v.findTorrentFile())
                            i += 1
                        else:
                            _log.warn("Programmable error: identifier in sorter that does not exists in source")
            else:
                self.exitOnInputError("Feed directory is missing in path or is not a directory:\n                    " + options.list)                
        else:
            self.exitOnInputError("None of the main options -c, -a, -r or -l specified!")

    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(0)

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Creates a feed from scratch or manages the feed. Consult tool help (-h)\n  for more options."

    # Command line options
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-c", "--create-feed", help = "Create or modify feed metadata or parameters", action="store_true", dest="feedmod", default = False)
    parser.add_option("-a", "--add-item", help = "Add feed item", action="store_true", dest="additem", default = False)
    parser.add_option("-r", "--remove-item", help = "Remove feed item by identifier (use list to find the right one)", action="store", dest="removeitem", default = None)
    parser.add_option("-l", "--list", help = "List the feed storage", action="store", dest="list", default = False)
    parser.add_option("--long", help = "List the feed storage in detail", action="store_true", dest="listlong", default = False)
    parser.add_option("-m", "--media-root", help = "Location of feeds storage, other then media root (settings.MEDIA_ROOT)", action="store", dest="mediaroot", default = None)
    parser.add_option("-t", "--title-name", help = "Name of the title, feed or item", action="store", dest="title", default = None)
    parser.add_option("-k", "--series-title", help = "Feed series title (description)", action="store", dest="description", default = None)
    parser.add_option("-n", "--language", help = "Feed language", action="store", dest="language", default = None)
    parser.add_option("-g", "--originator", help = "Feed originator", action="store", dest="originator", default = None)
    parser.add_option("-d", "--feed-storage", help = "Feed storage", action="store", dest="feeddir", default = None)
    parser.add_option("-e", "--feed-export-url", help = "URL where the feed will be accessible, default " + settings.EXPORT_FEED_LINK + " appended with the name of the feed (directory) with xml extension", action="store", dest="exporturl", default = settings.EXPORT_FEED_LINK)
    parser.add_option("-j", "--author", help = "Publisher of the feed", action="store", dest="publisher", default = None)
    parser.add_option("-u", "--id", help = "Unique identifier of the feed", action="store", dest="id", default = None)
    parser.add_option("-i", "--image", help = "Image of the feed", action="store", dest="image", default = None)
    parser.add_option("-p", "--publish-link", help = "Publish link of the feed (absolute), default " + settings.CONTENT_PUBLISHING_LINK, action="store", dest="publish", default = settings.CONTENT_PUBLISHING_LINK)
    parser.add_option("-o", "--cu-class-instance", help = "Content unit class instance used in an export of the feed. Enables custumization of the export per unit", action="store", dest="cuci", default = None)
    parser.add_option("-b", "--did-base", help = "Feed DID base file", action="store", dest="didbase", default = None)
    parser.add_option("-x", "--core-metadata", help = "Core metadata file used as template for the feed or an item. Caution: if used with the item the channel metadata gets overwritten by this metadata. In this case the item metadata should specify the channel metadata as well.", action="store", dest="coremetafile", default = None)    
    parser.add_option("-y", "--mime-type", help = "Item mime type", action="store", dest="mimetype", default = None)
    parser.add_option("-s", "--synopsis", help = "Item synopsis", action="store", dest="synopsis", default = None)
    parser.add_option("-z", "--content", help = "Content file pointed to in an item", action="store", dest="content", default = None)
    (options, args) = parser.parse_args()

    managefeed = ManageFeed()
    managefeed.parser = parser
    managefeed.options = options.__dict__
    
    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The managefeed has been called with the following options:")
        for k, v in managefeed.options.items():
            _log.debug(k + ": " + str(v))

    try:
        managefeed.run()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt caught, quit!")
        managefeed.exit()
