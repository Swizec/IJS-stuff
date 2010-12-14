import os
import shutil
import subprocess
import tempfile
import unittest
import urllib
import urlparse
from cStringIO import StringIO

from JSI.ProviderToolbox.MetadataGenerator import Feed, Item, Media, Stream, RTVSLOLiveFeed, BBCLiveFeed
from JSI.ProviderToolbox.external import feedparser
from JSI.ProviderToolbox.utils import log 
from JSI.ProviderToolbox.utils.utilities import command, asciify, textify
from JSI.ProviderToolbox.conf import settings
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

# Next-Share management of the logging system is always a supprise. If
# imported before the JSI imports the basic logging config sets the
# stream handler to /dev/null. The config is run only once. Sigh.
from BaseLib.Core.TorrentDef import TorrentDef

_log = log.getLog('TestMetaGenerator')
log.setLevel(log.DEBUG)

class TestMetaGenerator(unittest.TestCase):
    """ 
    Test framework for testing generation of metadata from a feed
    """
    data = None
    
    alpha = "ABCDEFGHIJKLMNOPRSTUXYWZ"
    test_counter = 0
    run_test = True
    tests = {"A": True, #testAGetFeedMetadata
             "B": True, #testBGetItemMetadata
             "C": True, #testCFFMpegIdentify
             "D": True, #testDRichMetadata
             # For this test the previous one needs to be set as well
             "E": True, #testECreateRichTorrents
             "F": True, #testFRTVLOLiveFeeds
             "G": True, #testGBBCLiveFeeds
             }

    def setUp(self):
        """ Set up method """
        if not TestMetaGenerator.tests.get(TestMetaGenerator.alpha[TestMetaGenerator.test_counter]):
            TestMetaGenerator.run_test = False
        TestMetaGenerator.test_counter += 1

    def tearDown(self):
        """ Tear down method """
        TestMetaGenerator.run_test = True

    def testAGetFeedMetadata(self):
        _log.info("Get feed metadata ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        metagdn = Feed()
        metaradio4 = Feed()
        feeds = {"http://www.rtvslo.si/podcasts/gori_doli_naokoli.xml": metagdn,
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml": metaradio4}
        for f, m in feeds.items():
            pf = feedparser.parse(f)
            for k in settings.MMM_FEED.keys():
                # Split enables lookup in more complex feedparser
                # structures, like image:href, for example.
                split = k.split(":") # Mark : for settings?
                try:
                    v = getattr(pf.feed, split[0])
                    if len(split) > 1:
                        name = k.replace(":", "_")
                        if split[1].startswith("-"):
                            name = name.replace("-", "")
                            setattr(m, name, v[split[1].replace("-", "")])
                        else:
                            setattr(m, name, v[split[1]])                            
                    else:
                        setattr(m, k, v)
                except:
                    pass
        _log.debug(metagdn.toString())
        _log.debug(metaradio4.toString())

    def testBGetItemMetadata(self):
        _log.info("Get feed items metadata ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        metagdn = Feed()
        metaradio4 = Feed()
        feeds = {"http://www.rtvslo.si/podcasts/gori_doli_naokoli.xml": metagdn,
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml": metaradio4}
        for f, m in feeds.items():
            pf = feedparser.parse(f)
            for i in pf.entries:
                item = Item()
                for k in settings.MMM_ITEM.keys():
                    # Split enables lookup in more complex feedparser
                    # structures, like media_content:type, for
                    # example. Not used at the moment.
                    split = k.split(":") 
                    try:
                        v = getattr(i, split[0])
                        if len(split) > 1:
                            name = k.replace(":", "_")
                            if split[1].startswith("-"):
                                name = name.replace("-", "")
                                setattr(item, name, v[split[1].replace("-", "")])
                            else:
                                setattr(item, name, v[0][split[1]])
                        else:
                            setattr(item, k, v)
                    except:
                        pass
                m._items.append(item)
        _log.debug(metagdn.toString())
        _log.debug(metaradio4.toString())

    def testCFFMpegIdentify(self):
        _log.info("Identify media ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feed = "http://www.rtvslo.si/podcasts/vreme.xml"
        pf = feedparser.parse(feed)
        url = pf.entries[0].id
        if url != None:
            tmpFile = tempfile.NamedTemporaryFile()
            urllib.urlretrieve(url, tmpFile.name)
            m1 = Media.getMetadata(tmpFile.name)
            _log.debug(m1.toString())
            m2 = Media.getMetadata(url)
            _log.debug(m2.toString())
            self.assertTrue(m1 == m2)
            oldsize = m1.size
            m1.size = str(int(m1.size) - 1)
            self.assertTrue(m1 != m2)
            m1.size = oldsize
            self.assertTrue(m1 == m2)
            if len(m2._items) > 0:
                m2._items[0].number = "whoknows"
                self.assertTrue(m1 != m2)

    def testDRichMetadata(self):
        _log.info("Generate RichMetadata ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        rmg = RichMetadataGenerator.getInstance()
        # Only RTV based feed, have problems accessing BBC feeds :(
        feeds = ["http://www.rtvslo.si/podcasts/gori_doli_naokoli.xml",
                 "http://www.rtvslo.si/podcasts/vreme.xml",
                 "http://www.rtvslo.si/podcasts/studio_city.xml",
                 "http://downloads.bbc.co.uk/podcasts/radio4/today/rss.xml"]
        metaFeeds = list()
        for f in feeds:
            metaFeeds.append(Feed.getMetadata(f))
        rmi = {}
        for mf in metaFeeds:
            # Get rich metadata from the feed
            fmeta = mf.getRichMetadata()
            for item in mf._items:
                # Get item rich metadata and add the feed meta
                imeta = item.getRichMetadata(fmeta)
                rmi[imeta] = item
        rm_read = None
        rm_orig = None
        for rm in rmi: 
            rm_orig = rm
            # Build rich metadata instances
            rm_xml = rmg.build(rm)
            _log.debug(rmg.prettyPrint(rm_xml))
            # Can we read what we had encoded?
            rm_read = rmg.getRichMetadata(rm_xml)
            # If this test raises an assertion error elevate the log
            # level in RichMetadata implementation to debug
            self.assertTrue(rm == rm_read)
        rm_read.setFrameRate("12")
        self.assertTrue(rm_read != rm_orig)
        # Build base DIDs
        storeData = {}
        for rm, v in rmi.items(): 
            rm_xml = rmg.build(rm)
            bdid = rmg.getRichMetadata(None, metadata.MPEG_21_BASE)
            bdid.setMetaCore(rm_xml)
            if v.file != None:
                bdid.setContentReference(v.file)
            if v.extension != None:
                if settings.MIME_TYPES_MAP.has_key(v.extension):
                    bdid.setContentType(settings.MIME_TYPES_MAP[v.extension])
                else:
                    if v.media_content_type != None:
                        bdid.setContentType(v.media_content_type)
            if rm.getPublisher() == settings.PUBLISHER_RTV_SLO_MMC:
                if v.id != None:
                    helper = settings.IDENTIFY_HELPER[settings.PUBLISHER_RTV_SLO_MMC]
                    ident = helper(v.id)
                    bdid.setIdentifier(settings.URN_ITEM + settings.RTV_SLO_MMC + "-" + ident)
                    bdid.setRelatedIdentifier(settings.RELATED_RTV_SLO_MMC + ident)
            bdid_xml = rmg.build(bdid)
            _log.debug(rmg.prettyPrint(bdid_xml))
            storeData[bdid_xml] = v
        # Avoid reading the feeds all the time. Data keys: DID base
        # metadata, value: items metadata
        TestMetaGenerator.data = storeData

    def testECreateRichTorrents(self):
        _log.info("Create rich metadata torrents ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        data = None
        self.assertTrue(TestMetaGenerator.data != None, "Test E depends on data gathered in test D, set testD attribute to True")
        if TestMetaGenerator.data != None:
            data = TestMetaGenerator.data
        else:
            return
        rmg = RichMetadataGenerator.getInstance()
        torrents = []
        for k, v in data.items():
            if v.content_base != None:
                # Choose only a small subset of content to download
                if v.content_base == "http://www.rtvslo.si/podcasts/gori_doli_naokoli.xml":
                    mm_file = tempfile.NamedTemporaryFile()
                    try:
                        urllib.urlretrieve(v.id, mm_file.name)
                        torrent_def = TorrentDef()
                        torrent_def.add_content(mm_file.name)
                        torrent_def.set_tracker("http://wanabe.a.tracker.com:8080")
                        torrent_def.set_metadata(k)
                        torrent_def.finalize()
                        torrent_def.save(mm_file.name + ".torrent")
                        torrents.append(mm_file.name + ".torrent")
                    except Exception, e:
                        _log.error("Failed to generate torrent file, reason: " + str(e))
        for t in torrents:
            try:
                tdef = TorrentDef.load(t)
            except Exception, e:
                _log.error("Exception raised while reading the torrent file: " + str(e))
            xml = tdef.get_metadata()
            # Funny, this works 
            self.assertTrue(data.has_key(xml))
            try:
                os.remove(t)
            except:
                _log.error("Cannot remove specified file '%s'", t)

    def testFRTVSLOLiveFeeds(self):
        _log.info("Test RTVSLO programme schedule ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feeds = {"http://www.rtvslo.si/modload.php?&c_mod=rspored-v2&s_content=xml&izbran_program=1": "http://193.138.1.109:19951",
                 "http://www.rtvslo.si/modload.php?&c_mod=rspored-v2&s_content=xml&izbran_program=2": "http://193.138.1.109:19952",
                 "http://www.rtvslo.si/modload.php?&c_mod=rspored-v2&s_content=xml&izbran_program=22": "http://193.138.1.109:19953"}
        metaFeeds = []
        for f, source in feeds.items():
            fm = RTVSLOLiveFeed.getMetadata(f)
            # Get media information as well
            fm.identifyMedia(source)
            metaFeeds.append(fm)
        rmi = {}
        rmg = RichMetadataGenerator.getInstance()
        for lf in metaFeeds:
            # Get rich metadata from the feed
            lmeta = lf.getRichMetadata()
            for item in lf._items:
                # Get item rich metadata and add the live feed meta
                imeta = item.getRichMetadata(lmeta)
                rmi[imeta] = item
        for rm, item in rmi.items():
            _log.debug(rmg.prettyPrint(rmg.build(rm)))

    def testGBBCLiveFeeds(self):
        _log.info("Test BBC programme schedule ------------")
        if not TestMetaGenerator.run_test:
            _log.debug("Test avoided.")
            return
        feeds = {"http://www.bbc.co.uk/bbctwo/programmes/schedules/england/today.xml": None}
        metaFeeds = []
        for f, source in feeds.items():
            fm = BBCLiveFeed.getMetadata(f)
            if source != None:
                fm.identifyMedia(source)
            metaFeeds.append(fm)
        rmi = {}
        rmg = RichMetadataGenerator.getInstance()
        for lf in metaFeeds:
            # Get rich metadata from the feed
            lmeta = lf.getRichMetadata()
            for item in lf._items:
                # Get item rich metadata and add the live feed meta
                imeta = item.getRichMetadata(lmeta)
                rmi[imeta] = item
        for rm, item in rmi.items():
            _log.debug(rmg.prettyPrint(rmg.build(rm)))
            
def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestMetaGenerator)

if __name__ == "__main__":
    unittest.main()


