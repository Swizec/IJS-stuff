import os
import shutil
import tempfile
import unittest
import urlparse
import logging
import random
import time
from cStringIO import StringIO

from JSI.ProviderToolbox.FeedGenerator import P2PNextAtomFeed, P2PNextLiveAtomFeed
from JSI.ProviderToolbox.MetadataGenerator import Feed
from JSI.ProviderToolbox.external import feedparser
from JSI.ProviderToolbox.ContentSource import Channel, ContentUnit, RTVVoDContent, ContentSource
from JSI.ProviderToolbox.utils import log 
from JSI.ProviderToolbox.utils.exceptions import FeedGeneratorError
from JSI.ProviderToolbox.utils.utilities import textify
from JSI.ProviderToolbox.conf import settings
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

_log = log.getLog('TestContentSource')
log.setLevel(log.INFO)

class TestContentSource(unittest.TestCase):
    """ 
    Test framework for testing content sources
    """
    
    alpha = "ABCDEFGHIJKLMNOPRSTUXYWZ"
    test_counter = 0
    run_test = True
    tests = {"A": True, #testAGetChannel
             "B": True, #testBExportTorrents
             "C": True, #testCSyncCheck
             "D": True, #testDCheckUpdate
             "E": True, #testEDefaultsExportFeed
             "F": True, #testFCustomizedExportFeed
             "G": True, #testGExportFeedLink
             "H": True, #testHRestoreStoredProperties
             "I": True, #testIWindow
             "J": True, #testJLoadFromDir
             }

    def setUp(self):
        """ Set up method """
        if not TestContentSource.tests.get(TestContentSource.alpha[TestContentSource.test_counter]):
            TestContentSource.run_test = False
        TestContentSource.test_counter += 1

    def tearDown(self):
        """ Tear down method """
        TestContentSource.run_test = True

    def testAGetChannel(self):
        _log.info("Get channel metadata and content ------------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]
        for f in feeds:
            channel = Channel.getContentSource(f)
            feed = feedparser.parse(f)
            self.assertTrue(channel.metadata != None)
            self.assertTrue(channel.cstype == settings.CS_TYPE_CHANNEL)
            self.assertTrue(channel.sourceMeta == None)
            self.assertTrue(channel.name != None)
            self.assertTrue(channel.identifier != None)
            self.assertTrue(channel.location == f)
            self.assertTrue(os.path.isdir(channel.storage))
            self.assertTrue(os.path.exists(os.path.join(channel.storage, channel.metaFile)))
            self.assertTrue(os.path.exists(os.path.join(channel.storage, settings.CONTENT_SOURCE_PROPERTIES)))
            # The reason for failure can be that the channel was
            # already there before running the test - more items were
            # stored then there are feed items
            self.assertTrue(len(channel.items) == len(feed.entries))
            for i, v in channel.items.items():
                self.assertTrue(v.name != None)
                self.assertTrue(v.cutype == settings.CONTENT_VOD)
                self.assertTrue(v.identifier != None and v.identifier == i)
                self.assertTrue(v.metadata != None)
                self.assertTrue(channel.storage == v.feedStore)
                self.assertTrue(v.stored)
                self.assertTrue(v.acquire == channel.acquire)
                self.assertTrue(os.path.exists(os.path.join(channel.storage, v.contentFile)))
                self.assertTrue(os.path.exists(os.path.join(channel.storage, v.metaFile)))
            restored = channel.restore(channel.storage)
            _log.debug(restored.toString())
            _log.debug(channel.toString())
            self.assertTrue(restored == channel)
            new = Channel.getContentSource(f)
            self.assertTrue(new == channel)
            channel.remove()
        
    def testBExportTorrents(self):
        _log.info("Export torrents ------------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        channel = Channel.getContentSource("http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml")
        channel.exportTorrent()
        for i, v in channel.items.items():
            (b, e) = os.path.splitext(v.contentFile)
            tp = os.path.join(settings.EXPORT_TORRENT_DIR, b + '.tstream')
            self.assertTrue(os.path.exists(tp))
        channel.update()
        for i, v in channel.items.items():
            self.assertTrue(not v.fresh)
        channel.remove()
        shutil.rmtree(settings.EXPORT_TORRENT_DIR)

    def testCSyncCheck(self):
        _log.info("Sync check for torrents ------------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        channel = Channel.getContentSource("http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml")
        channel.exportTorrent()
        tp = ""
        for i, v in channel.items.items():
            (b, e) = os.path.splitext(v.contentFile)
            tp = os.path.join(settings.EXPORT_TORRENT_DIR, b + '.tstream')
            if os.path.exists(tp):
                os.remove(tp)
                break
        self.assertTrue(not os.path.exists(tp))
        channel.syncCheck()
        for i, v in channel.items.items():
            (b, e) = os.path.splitext(v.contentFile)
            tp = os.path.join(settings.EXPORT_TORRENT_DIR, b + '.tstream')
            self.assertTrue(os.path.exists(tp))
        channel.remove()
        shutil.rmtree(settings.EXPORT_TORRENT_DIR)

    def testDCheckUpdate(self):
        _log.info("Check update from source ------------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]
        for f in feeds:
            channel = Channel.getContentSource(f)
            for i, v in channel.items.items():
                self.assertTrue(os.path.exists(os.path.join(channel.storage, v.contentFile)))
                self.assertTrue(os.path.exists(os.path.join(channel.storage, v.metaFile)))
            random.random()
            r = random.randint(1, len(channel.items))
            n = 0
            meta = None 
            cont = None
            for i, v in channel.items.items():
                n += 1
                if n == r:
                    meta = os.path.join(channel.storage, v.contentFile)
                    cont = os.path.join(channel.storage, v.metaFile)
                    os.remove(meta)
                    os.remove(cont)
            self.assertTrue(not os.path.exists(meta))
            self.assertTrue(not os.path.exists(cont))
            # update
            channel = Channel.getContentSource(f)
            self.assertTrue(os.path.exists(meta))
            self.assertTrue(os.path.exists(cont))

    def testEDefaultsExportFeed(self):
        _log.info("Defaults export feed ------------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]
        rmg = RichMetadataGenerator.getInstance()
        publish = "http://web.server.of.your.choice/relative"
        for f in feeds:
            channel = Channel.getContentSource(f, publish)
            # Get meta, don't identify media, since we can't (yet?)
            meta = Feed.getMetadata(StringIO(channel.exportFeed()), False)
            self.assertTrue(meta.title == channel.name)
            self.assertTrue(meta.links_href == channel.getExportFeedLink())
            self.assertTrue(meta.language == channel.metadata.getLanguage())
            self.assertTrue(meta.author == channel.metadata.getPublisher())
            self.assertTrue(meta.id == channel.guid)
            self.assertTrue(meta.p2pnext_image_src == channel.image)
            for i, v in channel.items.items():
                # Find according to link
                rmi = None
                for m in meta._items:
                    if m.links_href == publish + "/" + v.getPublish():
                        rmi = m
                self.assertTrue(rmi != None)
                self.assertTrue(rmi.title == v.name)
                if v.getPublish().endswith("/"):
                    self.assertTrue(rmi.links_type == "text/html")
                else:
                    self.assertTrue(rmi.links_type == "application/x-bittorrent")
                # Id not tested
                if v.getImage():
                    self.assertTrue(rmi.p2pnext_image_src == v.getImage())
                else:
                    self.assertTrue(rmi.p2pnext_image_src == channel.image)
                self.assertTrue(rmi.title == v.metadata.getTitleEpisodeTitle())


    def testFCostumizedExportFeed(self):
        _log.info("Customized export feed -----------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]  
        rmg = RichMetadataGenerator.getInstance()
        publish = "http://stream.e5.ijs.si/vod"
        for f in feeds:
            url = urlparse.urlparse(f)
            if url.netloc == "www.rtvslo.si":
                channel = Channel.getContentSource(f, publish, RTVVoDContent())
                for i, v in channel.items.items():
                    self.assertTrue(type(v) == type(RTVVoDContent()))
            else:
                channel = Channel.getContentSource(f, publish)
                for i, v in channel.items.items():
                    self.assertTrue(type(v) == type(ContentUnit()))
            _log.debug(rmg.prettyPrint(channel.exportFeed(), 'utf-8'))

    def testGExportFeedLink(self):
        _log.info("Export feed link -----------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml"]
        rmg = RichMetadataGenerator.getInstance()
        publish = "http://stream.e5.ijs.si/vod"
        feedLink = "http://stream.e5.ijs.si/feeds/zapisi_iz_mocvirja.xml"
        for f in feeds:
            channel = Channel.getContentSource(f, publish, RTVVoDContent(), feedLink)
            meta = Feed.getMetadata(StringIO(channel.exportFeed()), False)
            self.assertTrue(meta.links_href == feedLink)

    def testHRestoreStoredProperties(self):
        _log.info("Restore stored properties -----------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feed = "http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml"
        publish = "http://stream.e5.ijs.si/vod"
        feedLink = "http://stream.e5.ijs.si/feeds/zapisi_iz_mocvirja.xml"
        cuci = "RTVVoDContent"
        exportLink = "http://web.server.of.your.choice/relative"
        guid = "xyz"
        image = "http://stream.e5.ijs.si/image/kuku.jpg"
        didfile = "did-base-test.xml"
        rmg = RichMetadataGenerator.getInstance()
        meta = rmg.getRichMetadata(None, metadata.MPEG_21_BASE)
        meta.setRelatedIdentifier("urn:rtv-slo:slo1-xyz") 
        meta.setPaymentReference("URI to additional MPEG_21 data (payment)") 
        meta.setAdvertisementReference("URI to additional MPEG_21 data (advertising)") 
        meta.setScalabilityReference("URI to additional MPEG_21 data (scalability)")
        meta.setLimoReference("URI to additional MPEG_21 data (limo)")
        f = open(didfile, 'w')
        f.write(rmg.build(meta))
        f.close()
        channel = Channel.getContentSource(feed, publish, RTVVoDContent(), feedLink, didfile)
        feed1_xml = channel.exportFeed(guid, image)
        test = ContentSource.getContentSource(feed)
        test.storage = channel.storage
        test.restoreAttributes()
        self.assertTrue(channel.storage == test.storage)
        self.assertTrue(channel.cstype == test.cstype)
        self.assertTrue(channel.location == test.location)
        self.assertTrue(channel.publish == test.publish)
        self.assertTrue(channel.image == test.image)
        self.assertTrue(channel.contentUnitClassInstance == test.contentUnitClassInstance)
        self.assertTrue(channel.exportFeedLink == test.exportFeedLink)
        self.assertTrue(channel.didbaseFile == test.didbaseFile)
        self.assertTrue(channel.guid == test.guid)
        channel = Channel.getContentSource(feed)
        feed2_xml = channel.exportFeed()
        # Cannot compare directly xmls since the updated can change
        feed1_meta = Feed.getMetadata(StringIO(feed1_xml), False)
        feed2_meta = Feed.getMetadata(StringIO(feed2_xml), False)
        self.assertTrue(feed1_meta.id == feed2_meta.id)
        self.assertTrue(feed1_meta.p2pnext_img_src == feed2_meta.p2pnext_img_src)
        self.assertTrue(feed1_meta.links_href == feed2_meta.links_href)
        count = 0
        for i in feed1_meta._items:
            self.assertTrue(i.links_href == feed2_meta._items[count].links_href)
            self.assertTrue(i.id == feed2_meta._items[count].id)
            self.assertTrue(i.p2pnext_image_src == feed2_meta._items[count].p2pnext_image_src)
            count += 1

    def testIWindow(self):
        _log.info("Window test -----------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feed = "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"
        channel = Channel.getContentSource(feed)
        fp = feedparser.parse(feed)
        osw = len(fp.entries)
        channel = Channel.getContentSource(feed, None, None, None, None, osw)
        self.assertTrue(len(channel.items) == osw)
        channel = Channel.getContentSource(feed, None, None, None, None, osw-1)
        self.assertTrue(len(channel.items) == osw-1)
        channel.window = 10
        channel.checkWindow()
        self.assertTrue(len(channel.items) == 10)
        channel.store(True)
        channel = Channel.getContentSource(feed)
        self.assertTrue(len(channel.items) == 10)
        # Negative value for window restores default - None
        channel = Channel.getContentSource(feed, None, None, None, None, -1)
        self.assertTrue(len(channel.items) == osw)

    def testJLoadFromDir(self):
        _log.info("Loading from directory -----------")
        if not TestContentSource.run_test:
            _log.debug("Test avoided.")
            return
        feeds = ["http://www.rtvslo.si/podcasts/zapisi_iz_mocvirja.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]  
        netch = []
        for f in feeds:
            netch.append(Channel.getContentSource(f))
        dirch = []
        for c in netch:
            dirch.append(Channel.getContentSource(c.storage))
        i = 0
        for c in netch:
            self.assertTrue(c == dirch[i])
            i += 1
                                
def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestContentSource)

if __name__ == "__main__":
    unittest.main()


