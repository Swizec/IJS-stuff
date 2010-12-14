import os
import sys
from optparse import OptionParser, OptionGroup

from JSI.ProviderToolbox.ContentSource import ContentSource, Channel, ContentUnit, RTVVoDContent
from JSI.ProviderToolbox.FeedGenerator import P2PNextAtomFeed
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils import log

_log = log.getLog('discoveryfeed')
log.setLevel(log.DEBUG)

class DiscoveryFeed(object):

    def __init__(self):
        self.rmg = RichMetadataGenerator.getInstance()
        self.parser = None
        self.options = None  
        self.default_title = "P2P-Next project discovery feed"
        self.default_publisher = "P2P-Next (http://www.p2p-next.org)"
        self.default_image = "http://stream.e5.ijs.si/images/p2p-next-logo.jpg" 

    def run(self):
        """
        Runs the feed tool and creates a feed according to specified
        options
        """
        if not options.title:
            options.title = self.default_title
        if not options.exporturl:
            self.exitOnInputError("Export url must be defined")
        if not options.publisher:
            options.publisher = self.default_publisher
        if not options.id:
            options.id = options.exporturl
        if not options.image:
            options.image = self.default_image
        df = P2PNextAtomFeed(title=options.title,
                             feed_url=options.exporturl,
                             author_name=options.publisher,
                             feed_guid=options.id,
                             image=options.image)
        storage = settings.MEDIA_ROOT
        if options.mediaroot:
            if os.path.isdir(options.mediaroot):
                storage = options.mediaroot
            else:
                self.exitOnInputError("Specified media root is not a directory")
        for e in os.listdir(storage):
            fdir = os.path.join(storage, e)
            _log.debug(fdir)
            if os.path.isdir(fdir):
                if os.path.exists(os.path.join(fdir, settings.CONTENT_SOURCE_PROPERTIES)):
                    _log.debug(fdir)
                    # Will need to adapt when live streams are supported
                    cs = Channel.getContentSource(fdir)
                    _log.debug(cs.toString())
                    image = options.image
                    if cs.image:
                        image = cs.image
                    fid = settings.URN + settings.P2P_NEXT + settings.COLON + cs.identifier
                    if cs.guid:
                        fid = cs.guid
                    video = False
                    for i, v in cs.items.items():
                        if v.metadata:
                            if v.metadata.getVideoCoding():
                                video = True
                                break
                    if video:
                        cat = [(settings.CATEGORY_TV, settings.CATEGORY_SCHEME_ST)]
                    else:
                        cat = [(settings.CATEGORY_RADIO, settings.CATEGORY_SCHEME_ST)]
                    df.add_item(title=cs.name, 
                                link=cs.exportFeedLink,
                                link_type="application/atom+xml",
                                unique_id=fid,
                                description=cs.metadata.getTitleSeriesTitle(),
                                image=image,
                                categories=cat)
        print self.rmg.prettyPrint(df.writeString(), 'utf-8')

    def exit(self):
        sys.exit(0)

    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(0)

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Create discoveryfeed from scratch. Consult tool help (-h) for more options."

    # Command line options
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-m", "--media-root", help = "Location of feeds storage, other then media root (settings.MEDIA_ROOT)", action="store", dest="mediaroot", default = None)
    parser.add_option("-t", "--feed-title", help = "Feed title", action="store", dest="title", default = None)
    parser.add_option("-e", "--feed-export-url", help = "URL where the feed will be accessible", action="store", dest="exporturl", default = None)
    parser.add_option("-p", "--author", help = "Publisher of the feed", action="store", dest="publisher", default = None)
    parser.add_option("-u", "--id", help = "Feed unique identifier", action="store", dest="id", default = None)
    parser.add_option("-i", "--image", help = "Feed image", action="store", dest="image", default = None)
    (options, args) = parser.parse_args()

    discoveryfeed = DiscoveryFeed()
    discoveryfeed.parser = parser
    discoveryfeed.options = options.__dict__
    
    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The discoveryfeed has been called with the following options:")
        for k, v in discoveryfeed.options.items():
            _log.debug(k + ": " + str(v))

    try:
        discoveryfeed.run()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt caught, quit!")
        discoveryfeed.exit()
