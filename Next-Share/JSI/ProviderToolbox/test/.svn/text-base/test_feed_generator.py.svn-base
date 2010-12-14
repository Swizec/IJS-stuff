import os
import shutil
import tempfile
import unittest
import urlparse
import logging
from cStringIO import StringIO

from JSI.ProviderToolbox.MetadataGenerator import Feed, Item, Media, Stream, RTVSLOLiveFeed, BBCLiveFeed
from JSI.ProviderToolbox.FeedGenerator import P2PNextAtomFeed, P2PNextLiveAtomFeed
from JSI.ProviderToolbox.external import feedparser
from JSI.ProviderToolbox.utils import log 
from JSI.ProviderToolbox.utils.exceptions import FeedGeneratorError
from JSI.ProviderToolbox.utils.utilities import textify
from JSI.ProviderToolbox.conf import settings
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

_log = log.getLog('TestFeedGenerator')
log.setLevel(log.DEBUG)

class TestFeedGenerator(unittest.TestCase):
    """ 
    Test framework for testing feeds and content sources
    """
    data = None
    
    alpha = "ABCDEFGHIJKLMNOPRSTUXYWZ"
    test_counter = 0
    run_test = True
    tests = {"A": True, #testAGenerateP2PNextAtomFeed
             "B": True, #testBParseP2PNextAtomFeed
             "C": True, #testCCopyVoDFeed
             "D": True, #testDCopyLiveFeed
             "E": True, #testEDiscoveryFeed
             }

    def setUp(self):
        """ Set up method """
        if not TestFeedGenerator.tests.get(TestFeedGenerator.alpha[TestFeedGenerator.test_counter]):
            TestFeedGenerator.run_test = False
        TestFeedGenerator.test_counter += 1

    def tearDown(self):
        """ Tear down method """
        TestFeedGenerator.run_test = True

    def testAGenerateP2PNextAtomFeed(self):
        _log.debug("Generate P2P-Next Atom feeds ------------")
        if not TestFeedGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feed = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone", language=u"en", author_name=u"BBC", feed_guid=u"urn:bbc-bbcone", image="http://p2pnextfeed1.rad0.net/images/bbcone.png")
        feed.add_item(title="Weatherview", link=u"http://p2pnextfeed1.rad0.net/content/info/bbc/bbcone/b00vk4xq", link_type=u"application/atom+xml", unique_id=u"urn:bbc-bbcone-b00vk4xq", description=u"Detailed weather forecast.", image="http://www.bbc.co.uk/iplayer/images/progbrand/b007yy70_150_84.jpg")
        rmg = RichMetadataGenerator.getInstance()
        _log.debug(rmg.prettyPrint(feed.writeString(), 'utf-8'))
        #### Test some changes we have done to the Django feedgenerator
        # 0.) Default generator
        self.assertTrue(isinstance(feed, P2PNextAtomFeed))
        # 1.) Can generate feed without description and swapped
        # feed_url and link
        self.assertTrue(P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone"))
        # 2.) Without specified link the id is not None
        self.assertTrue(P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone").feed['id'] != None)
        # 3.) Specifying an image turns on p2pnext namespace
        self.assertTrue(feed.root_attributes().has_key("xmlns:p2pnext"))
        self.assertTrue(feed.feed.has_key("image"))
        self.assertTrue(feed.feed["image"] != None)
        self.assertTrue(feed.items[0].has_key("image"))
        self.assertTrue(feed.items[0]["image"] != None)
        # 4.) Specifying an image in an item turns on p2pnext namespace
        feed2 = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone", language=u"en", author_name=u"BBC", feed_guid=u"urn:bbc-bbcone")
        feed2.add_item(title="Weatherview", link=u"http://p2pnextfeed1.rad0.net/content/info/bbc/bbcone/b00vk4xq", link_type=u"application/atom+xml", unique_id=u"urn:bbc-bbcone-b00vk4xq", description=u"Detailed weather forecast.", image="http://www.bbc.co.uk/iplayer/images/progbrand/b007yy70_150_84.jpg")
        self.assertTrue(feed2.root_attributes().has_key("xmlns:p2pnext"))
        self.assertTrue(feed2.feed.has_key("image"))
        self.assertTrue(feed2.feed["image"] == None)
        self.assertTrue(feed2.items[0].has_key("image"))
        self.assertTrue(feed2.items[0]["image"] != None)
        # 5.) Only title and description (summary) are needed for an
        # item, since link || content, id still MUST be provided
        feed3 = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone")
        feed3.add_item(title="Weatherview",  description=u"Detailed weather forecast.")
        # In this case we generate id on the fly from the item link on build
        self.assertTrue(feed3.items[0]['unique_id'] == None)
        # 6.) But the build will fail if either link nor content are
        # available
        self.assertRaises(FeedGeneratorError, feed3.writeString)
        # 7.) So try with some content
        feed4 = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone")
        feed4.add_item(title="Weatherview",  description=u"Detailed weather forecast.", content="Still need better specification how to  be encoded")
        pf = feedparser.parse(StringIO(feed4.writeString()))
        self.assertTrue(pf.entries[0]['id'] != None)
        _log.debug("Unique id generated based on content: %s", pf.entries[0]['id'])
        # 8.) And with a link
        feed5 = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone")
        feed5.add_item(title="Weatherview",  description=u"Detailed weather forecast.", link=u"http://p2pnextfeed1.rad0.net/content/info/bbc/bbcone/b00vk4xq")
        pf = feedparser.parse(StringIO(feed5.writeString()))
        self.assertTrue(pf.entries[0]['id'] != None)
        _log.debug("Unique id generated based on a link: %s", pf.entries[0]['id'])
        linkBasedId = pf.entries[0]['id']
        # 9.) And if we try both, link prevails (content is discarded)
        feed6 = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone")
        feed6.add_item(title="Weatherview",  description=u"Detailed weather forecast.", content="Still need better specification how to  be encoded", link=u"http://p2pnextfeed1.rad0.net/content/info/bbc/bbcone/b00vk4xq")
        pf = feedparser.parse(StringIO(feed6.writeString()))
        self.assertTrue(pf.entries[0]['id'] != None)
        self.assertTrue(pf.entries[0]['id'] == linkBasedId)

    def testBParseP2PNextAtomFeed(self):
        _log.debug("Parse P2P-Next Atom feed ------------")
        if not TestFeedGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feed = P2PNextAtomFeed(title=u"BBC One London", feed_url=u"http://p2pnextfeed1.rad0.net/content/feed/bbc/bbcone", language=u"en", author_name=u"BBC", feed_guid=u"urn:bbc-bbcone", image="http://p2pnextfeed1.rad0.net/images/bbcone.png")
        feed.add_item(title="Weatherview", link=u"http://p2pnextfeed1.rad0.net/content/info/bbc/bbcone/b00vk4xq", link_type=u"application/atom+xml", unique_id=u"urn:bbc-bbcone-b00vk4xq", description=u"Detailed weather forecast.", image="http://www.bbc.co.uk/iplayer/images/progbrand/b007yy70_150_84.jpg")
        meta = Feed.getMetadata(StringIO(feed.writeString()))
        _log.debug(meta.toString())
        self.assertTrue(meta.title == feed.feed['title'])
        self.assertTrue(meta.links_href == feed.feed['feed_url'])
        self.assertTrue(meta.language == feed.feed['language'])
        # Updated not defined in the feed, added on the fly
        self.assertTrue(meta.updated != feed.feed.get('updated'))
        self.assertTrue(meta.author == feed.feed['author_name'])
        self.assertTrue(meta.id == feed.feed['id'])
        self.assertTrue(meta.p2pnext_image_src == feed.feed['image'])
        count = 0
        for i in meta._items:
            self.assertTrue(i.title == feed.items[count]['title'])
            self.assertTrue(i.links_href == feed.items[count]['link'])
            self.assertTrue(i.links_type == feed.items[count]['link_type'])
            self.assertTrue(i.id == feed.items[count]['unique_id'])
            self.assertTrue(i.p2pnext_image_src == feed.items[count]['image'])
            self.assertTrue(i.summary == feed.items[count]['description'])
            count += 1

    def testCCopyVoDFeed(self):
        _log.debug("Copy VoD feed ------------")
        if not TestFeedGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/gori_doli_naokoli.xml",
                 "http://www.rtvslo.si/podcasts/vreme.xml",
                 "http://www.rtvslo.si/podcasts/studio_city.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]
        rmg = RichMetadataGenerator.getInstance()
        for f in feeds:
            _log.debug("Reading the feed %s", f)
            fmeta = Feed.getMetadata(f)
            _log.debug("Writting p2p-next feed %s", f)
            if fmeta.title_detail_base != None:
                furl = fmeta.title_detail_base
            else:
                furl = f
            p2pfeed = P2PNextAtomFeed(title=fmeta.title, feed_url=furl, language=fmeta.language, author_name=fmeta.author, feed_guid=fmeta.id, image=fmeta.image_href)
            for i in fmeta._items:
                if i.p2pnext_image_src == None:
                    i.p2pnext_image_src = fmeta.image_href
                ilink_type = None
                if i.media_content_type != None:
                    ilink_type = i.media_content_type
                elif i.extension != None:
                    if settings.MIME_TYPES_MAP.get(i.extension) != None:
                        ilink_type = settings.MIME_TYPES_MAP[i.extension]
                p2pfeed.add_item(title=i.title, link=i.links_href, link_type=ilink_type, unique_id=i.id, description=i.summary, image=i.p2pnext_image_src)

            _log.debug(rmg.prettyPrint(p2pfeed.writeString(), 'utf-8'))
            
    def testDCopyLiveFeed(self):
        _log.debug("Copy live feed ------------")
        if not TestFeedGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feeds = {"http://www.rtvslo.si/modload.php?&c_mod=rspored-v2&s_content=xml&izbran_program=1": "http://193.138.1.109:19951",
                 "http://www.bbc.co.uk/bbctwo/programmes/schedules/england/today.xml": None}
        parser = {"RTVSLOLiveFeed": lambda x: RTVSLOLiveFeed.getMetadata(x),
                  "BBCLiveFeed": lambda x: BBCLiveFeed.getMetadata(x),}
        # Provisional links to the stream
        links = {"www.rtvslo.si": "http://stream.e5.ijs.si/ch1.html",
                  "www.bbc.co.uk": "http:/to.uknown.net/bbctwo"}
        rmg = RichMetadataGenerator.getInstance()
        for f, v in feeds.items():
            url = urlparse.urlparse(f)
            if settings.LIVE_FEED_PARSER.get(url[1]) != None:
                p = parser.get(settings.LIVE_FEED_PARSER.get(url[1]))
                if p != None:
                    lfmeta = p(f)
                if v != None:
                    lfmeta.identifyMedia(v)
#                _log.debug(lfmeta.toString())
                p2pfeed = P2PNextLiveAtomFeed(title=lfmeta.title, feed_url=lfmeta.title_detail_base, language=lfmeta.language, author_name=lfmeta.author, feed_guid="Should be id of the stream", image=lfmeta.image_href)
                for i in lfmeta._items:
                    if links.get(url[1]) != None:
                        ilink = links[url[1]]
                        ilink_type = "text/html"
                    iadditional_id_data = ""
                    if i.subtitle != None:
                        iadditional_id_data += i.subtitle
                    if i.duration != None:
                        iadditional_id_data += i.duration
                    p2pfeed.add_item(title=i.title, link=ilink, link_type=i.link_type, unique_id=i.id, description=i.summary, image=i.p2pnext_image_src, additional_id_data=iadditional_id_data)
                _log.debug(rmg.prettyPrint(p2pfeed.writeString(), 'utf-8'))

    def testEDiscoveryFeed(self):
        _log.debug("Discovery feed ------------")
        if not TestFeedGenerator.run_test:
            _log.debug("Test avoided.")
            return
        rmg = RichMetadataGenerator.getInstance()
        # Just copy original BBC feed
        radfeed = "http://p2pnextfeed1.rad0.net/content/feed/bbc"
        meta = Feed.getMetadata(radfeed, False)
        _log.debug(meta.toString())
        p2pfeed = P2PNextAtomFeed(title=meta.title, feed_url=meta.title_detail_base, author_name=meta.author, feed_guid=meta.id, image=meta.p2pnext_img_src)
        for i in meta._items:
            cat = [(i.tags_term, i.tags_scheme)]
            p2pfeed.add_item(title=i.title, link=i.links_href, link_type=i.links_type, unique_id=i.id, description=i.summary, image=i.p2pnext_image_src, categories=cat)
        _log.debug(rmg.prettyPrint(p2pfeed.writeString(), 'utf-8'))
        # Now create something on our own, this is how I would imagine
        # a top level discovery tree
        dfeed = P2PNextAtomFeed(title="P2P-Next project discovery feed", feed_url="http://whereever.you.want", author_name="P2P-Next (http://www.p2p-next.org)", feed_guid=settings.URN + settings.P2P_NEXT, image="http://stream.e5.ijs.si/images/p2p-next-logo.jpg")
        dfeed.add_item(title=meta.title, link=meta.title_detail_base, link_type="application/atom+xml", unique_id=meta.id, description="BBC discovery feed", image=meta.p2pnext_image_src, categories=[("discovery", "urn:service-type")]) 
        dfeed.add_item(title="RTV SLO", link="htt://stream.e5.ijs.si/feeds/rtv-slo-discovery.xml", link_type="application/atom+xml", unique_id=settings.URN + settings.P2P_NEXT + settings.COLON + settings.RTV_SLO, description="RTV SLO MMC discovery feed", image="http://stream.e5.ijs.si/images/mmc.jpg", categories=[("discovery", "urn:service-type")])
        _log.debug(rmg.prettyPrint(dfeed.writeString(), 'utf-8'))
        # And fake an RTV SLO discovery feed. Fake in sense that the
        # content isn't copied, torrents are not made and only
        # metadata gets processed.
        feeds = ["http://www.rtvslo.si/podcasts/18-vzporednik.xml",
                 "http://www.rtvslo.si/podcasts/arsov_logos.xml",
                 "http://www.rtvslo.si/podcasts/dogodki_in_odmevi.xml",
                 "http://www.rtvslo.si/podcasts/utrip.xml",
                 "http://www.rtvslo.si/podcasts/vecerni_gost.xml",
                 "http://www.rtvslo.si/podcasts/vreme.xml"]
        rtvfeed = P2PNextAtomFeed(title="RTV SLO", feed_url="htt://stream.e5.ijs.si/feeds/rtv-slo-discovery.xml", author_name="RTV SLO MMC", feed_guid=settings.URN + settings.P2P_NEXT + settings.COLON + settings.RTV_SLO, image="http://stream.e5.ijs.si/images/mmc.jpg")
        identify = settings.IDENTIFY_HELPER[settings.PUBLISHER_RTV_SLO_MMC]
        for f in feeds:
            _log.debug("--------> Metadating a feed %s", f)
            meta = Feed.getMetadata(f)
            # Cycle through feed items
            for i in meta._items:
                video = False
                # Cycle through items media
                for m in i._items:
                    # Cycle through media streams
                    for s in m._items:
                        if s.type == "video":
                            video = True
                        # Decide on the first item
                        break
                    break
                break
            if video:
                cat = [(settings.CATEGORY_TV, settings.CATEGORY_SCHEME_ST)]
            else:
                cat = [(settings.CATEGORY_RADIO, settings.CATEGORY_SCHEME_ST)]
            rtvfeed.add_item(title=meta.title, link=meta.title_detail_base, link_type="application/atom+xml", unique_id=settings.URN + settings.P2P_NEXT + settings.COLON + settings.RTV_SLO + settings.COLON + identify(f), description=meta.subtitle, image=meta.image_href, categories=cat)
        _log.debug(rmg.prettyPrint(rtvfeed.writeString(), 'utf-8'))


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestFeedGenerator)

if __name__ == "__main__":
    unittest.main()


