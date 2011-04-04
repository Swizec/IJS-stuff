import json
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
        Runs the managefeed tool and creates or modifies a feed according to 
        specified options (items)
        """
        core = None
        if options.coremetafile:
            core = self.rmg.getRichMetadata(options.coremetafile)                
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
                core = self.rmg.getRichMetadata()
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
            self.checkFeedDir(options.feeddir)            
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
                core = self.rmg.getRichMetadata()
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
            channel.items[cu.identifier] = cu
            # Closed Swarm
            if options.cs or options.cskeys:
                csargs = None
                if not options.cskeys:
                    csargs = {"generate_cs": 'yes'}
                else:
                    keys = ";".join(options.cskeys.split(","))
                    csargs = {"generate_cs": 'no',
                              "cs_keys": keys}
                channel.createTorrent(cu, None, None, 
                                      settings.TORRENT_DIR, **csargs)
            else: 
                cu.fresh = True
                channel.exportTorrent()
        # Removes the item, add the removing of the feed as well!
        elif options.removeitem:
            if not options.feeddir:
                self.exitOnInputError("For removing the feed item feed directory needs to be\n                        specified (-d option)!")
            self.checkFeedDir(options.feeddir)            
            c = Channel()
            channel = c.restore(options.feeddir)
            if channel.items.has_key(options.removeitem):
                channel.removeContentUnit(options.removeitem)
            else:
                self.exitOnInputError("Cannot remove nonexistent content unit, identifier " + options.removeitem + " not registred")
        # List the feed
        elif options.list:
            if os.path.exists(options.list) and os.path.isdir(options.list):
                c = Channel()
                channel = c.getCSFromDir(options.list)
                if options.listlong:
                    print channel.toString()
                elif options.json:
                    print json.dumps(channel.listJson())
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
                            print "     Torrent:    " + str(v.torrent)
                            if v.cskeyfile:
                                print "     CS keys:    " + str(v.cskeyfile)
                            i += 1
                        else:
                            _log.warn("Programmable error: identifier in sorter that does not exists in source")
            else:
                self.exitOnInputError("Feed directory is missing in path or is not a directory:\n                    " + options.list)                
        # Outputs feed as atom feed or otputs a set of json outputs
        elif options.feed:
            self.checkFeedDir(options.feed)
            c = Channel()
            channel = c.getCSFromDir(options.feed)
            if not options.json:
                print self.rmg.prettyPrint(channel.exportFeed(options.id, options.image))
            else:
                channel.exportFeed(options.id, options.image)
                e = channel.getJsonExports()
                print json.dumps(e)
        # Find the identifier according to torrent, xml or media file
        elif options.fileName:
            if not options.feeddir:
                self.exitOnInputError("For finding the identifier of an item the feed\n                        directory need to be specified (-d option)!")
            self.checkFeedDir(options.feeddir)
            c = Channel()
            channel = c.getCSFromDir(options.feeddir)
            lids = channel.getItemIdentifier(options.fileName)
            if not options.json:
                print ",".join(lids)
            else:
                print json.dumps(lids)
        # Find CS key according to identifier
        elif options.identifier:
            if not options.feeddir:
                self.exitOnInputError("For finding the CS key according to item identifier\n                        the feed directory needs to be specified (-d option)!")
            self.checkFeedDir(options.feeddir)
            c = Channel()
            channel = c.getCSFromDir(options.feeddir)
            for k, v in channel.items.items():
                if k == options.identifier:
                    if v.cskeyfile:
                        if options.json:
                            print json.dumps([os.path.join(settings.CS_PUBLISH_DIR, v.cskeyfile)])
                        else:
                            print os.path.join(settings.CS_PUBLISH_DIR, v.cskeyfile)
        else:
            self.exitOnInputError("None of the main options -c, -a, -r, -l, -f or --identifier specified!")

    def checkFeedDir(self, feedDir):
        if not os.path.exists(feedDir) or not os.path.isdir(feedDir):
            self.exitOnInputError("Feed directory is missing in path or is not a directory:\n                    " + feedDir) 
        if not os.path.exists(os.path.join(feedDir, settings.CONTENT_SOURCE_PROPERTIES)):
            self.exitOnInputError("Feed directory specified seems not to be populated.\n                    Feed properties file is missing in path: " + feedDir)

    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(1)

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Creates a feed from scratch or manages the feed. Consult tool help (-h)\n  for more options."

    # Command line options
    # abcdefghijklmnoprstvuxyz
    # xxxxxxxxxxxxxxxxxxxxxxxx
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    publish = OptionGroup(parser, "Publishing options", "Options used for publishing the content")
    metaopt = OptionGroup(parser, "Metadata options", "Options used for specifying the feed or item metadata")
    mainopt = OptionGroup(parser, "Main options", "One of this options needs to be specified")
    csopt = OptionGroup(parser, "ClosedSwarm options")
    miscopt = OptionGroup(parser, "Miscellaneous options")
    ###
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    mainopt.add_option("-c", "--create-feed", help = "Create or modify feed metadata or parameters, the feed directory should be specified as option argument", action="store_true", dest="feedmod", default = False)
    mainopt.add_option("-a", "--add-item", help = "Add feed item. The feed should be specified with feed dir option (-d)", action="store_true", dest="additem", default = False)
    mainopt.add_option("-r", "--remove-item", help = "Remove feed item by identifier (use list to find the right one and specify the feed directory with -d)", action="store", dest="removeitem", default = None)
    mainopt.add_option("-l", "--list", help = "List the feed storage directory as specified in option", action="store", dest="list", default = None)
    miscopt.add_option("--long", help = "List the feed storage in detail", action="store_true", dest="listlong", default = False)
    mainopt.add_option("-f", "--feed", help = "Get the feed specified by the feed storage directory. Feed guid (-u) or image (-i) can be specified on the command line as well", action="store", dest="feed", default = None)
    mainopt.add_option("-d", "--feed-storage", help = "Feed storage. Not usable on its own but needs to be specified together with other options (-r, -a, --identifier, ---find-cs-key)", action="store", dest="feeddir", default = None)
    miscopt.add_option("-m", "--media-root", help = "Location of feeds storage, other then media root (settings.MEDIA_ROOT)", action="store", dest="mediaroot", default = None)
    metaopt.add_option("-t", "--title-name", help = "Name of the title, feed or item", action="store", dest="title", default = None)
    metaopt.add_option("-k", "--series-title", help = "Feed series title (description)", action="store", dest="description", default = None)
    metaopt.add_option("-n", "--language", help = "Feed language", action="store", dest="language", default = None)
    metaopt.add_option("-g", "--originator", help = "Feed originator", action="store", dest="originator", default = None)
    publish.add_option("-e", "--feed-export-url", help = "URL where the feed will be accessible, default " + settings.EXPORT_FEED_LINK + " appended with the name of the feed (directory) with xml extension", action="store", dest="exporturl", default = settings.EXPORT_FEED_LINK)
    metaopt.add_option("-j", "--author", help = "Publisher of the feed", action="store", dest="publisher", default = None)
    publish.add_option("-u", "--id", help = "Unique identifier of the feed", action="store", dest="id", default = None)
    publish.add_option("-i", "--image", help = "Image of the feed", action="store", dest="image", default = None)
    publish.add_option("-p", "--publish-link", help = "Publish link of the feed (absolute), default " + settings.CONTENT_PUBLISHING_LINK, action="store", dest="publish", default = settings.CONTENT_PUBLISHING_LINK)
    publish.add_option("-o", "--cu-class-instance", help = "Content unit class instance used in an export of the feed. Enables custumization of the export per unit", action="store", dest="cuci", default = None)
    publish.add_option("-b", "--did-base", help = "Feed DID base file", action="store", dest="didbase", default = None)
    metaopt.add_option("-x", "--core-metadata", help = "Core metadata file used as template for the feed or an item. Caution: if used with the item the channel metadata gets overwritten by this metadata. In this case the item metadata should specify the channel metadata as well.", action="store", dest="coremetafile", default = None)    
    publish.add_option("-y", "--mime-type", help = "Item mime type", action="store", dest="mimetype", default = None)
    metaopt.add_option("-s", "--synopsis", help = "Item synopsis", action="store", dest="synopsis", default = None)
    publish.add_option("-z", "--content", help = "Content file pointed to in an item", action="store", dest="content", default = None)
    miscopt.add_option("--identifier", help = "Return an identifier list (comma separated) according to specified file name, either content, metadata or torrent file. Requires an option feed storage (-d) as well.", action="store", dest="fileName", default = None)
    csopt.add_option("--cs", help = "Protect the item with the closed swarm. Used only with add item (-a)", action="store_true", dest="cs", default = False)
    csopt.add_option("--cs-keys", help = "Specify a comma separated list of keys to be used with closed swarm. Used only with add item (-a). Not tested yet.", action="store", dest="cskeys", default = None)
    csopt.add_option("--find-cs-key", help = "Find CS key file for specified content unit identifyer, if any. Use with feed directory (-d)", action="store", dest="identifier", default = None)
    miscopt.add_option("--json", help = "Output feed data in json format. Makes sense only in combination with list feed (-l), feed (-f), --identifier and --find-cs-key.", action="store_true", dest="json", default = False)
    parser.add_option_group(mainopt)
    parser.add_option_group(metaopt)
    parser.add_option_group(publish)
    parser.add_option_group(csopt)
    parser.add_option_group(miscopt)
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
