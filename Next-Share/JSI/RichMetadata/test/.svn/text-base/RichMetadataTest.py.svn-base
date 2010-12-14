from xml.etree.ElementTree import Element, SubElement, iterparse
import unittest
from StringIO import StringIO

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator, __revision__
from JSI.RichMetadata.conf import metadata
from JSI.RichMetadata.utils import log
from JSI.RichMetadata.utils.TimeSeries import StatisticTimeSeries

loglevel = log.INFO
runspeed = True

_log = log.getLog('RichMetadataTest')
log.setLevel(loglevel)

# For development purposes
llA = loglevel
llB = loglevel
llC = loglevel
llD = loglevel
llE = loglevel
llF = loglevel
llG = loglevel
llH = loglevel
llI = loglevel
llJ = loglevel

class RichMetadataTest(unittest.TestCase):
    """ 
    RichMetadata testing framework 
    """

    def setUp(self):
        log.setLevel(loglevel)

    def tearDown(self):
        if loglevel >= log.INFO:
            _log.info("If interested in metadata information and XML representations parsed and generated during tests set log level to log.DEBUG.")

    def crossBuildsCompareXML(self, tva_in, mpeg7_in):
        _log.info("+++ Cross build compare XML +++")
        rmm = RichMetadataGenerator.getInstance()
        # Two instances of the "same" metadata
        tva = rmm.getRichMetadata(tva_in)
        mpeg7 = rmm.getRichMetadata(mpeg7_in)
        # Cross build
        mpeg7_from_tva = rmm.build(tva, metadata.TAG_MPEG7)
        tva_from_mpeg7 = rmm.build(mpeg7, metadata.TAG_TVA_MAIN)
        # Cross instances
        mpeg7_cross = rmm.getRichMetadata(mpeg7_from_tva)
        tva_cross = rmm.getRichMetadata(tva_from_mpeg7)
        for a in rmm.knownAttributes():
            if getattr(tva_cross, a):
                if not getattr(mpeg7_cross, a):
                    _log.error("Attribute '%s' present in TVA but not in MPEG7 rich metadata instance.", a)
                else:
                    if getattr(tva_cross, a) != getattr(mpeg7_cross, a):
                        _log.warn("Attribute '%s' present in both sets but different (TVA) '%s' != '%s' (MPEG7).", a, getattr(tva_cross, a), getattr(mpeg7_cross, a))
            if getattr(mpeg7_cross, a):
                if not getattr(tva_cross, a):
                    _log.error("Attribute '%s' present in MPEG7 but not in TVA rich metadata instance.", a)
        _log.info("Comparing cross builds back for TVA")
        for a in rmm.knownAttributes():
            if getattr(tva, a):
                if not getattr(tva_cross, a):
                    _log.error("Attribute '%s' present in TVA but not in TVA-Cross rich metadata instance.", a)
                else:
                    if getattr(tva, a) != getattr(tva_cross, a):
                        _log.warn("Attribute '%s' present in both sets but different (TVA) '%s' != '%s' (TVA-Cross).", a, getattr(tva, a), getattr(tva_cross, a))
        _log.info("Comparing cross builds back for MPEG7")
        for a in rmm.knownAttributes():
            if getattr(mpeg7, a):
                if not getattr(mpeg7_cross, a):
                    _log.error("Attribute '%s' present in TVA but not in TVA-Cross rich metadata instance.", a)
                else:
                    if getattr(mpeg7, a) != getattr(mpeg7_cross, a):
                        _log.warn("Attribute '%s' present in both sets but different (MPEG7) '%s' != '%s' (MPEG7-Cross).", a, getattr(mpeg7, a), getattr(mpeg7_cross, a))
        self.metadataCrossCompare(tva, mpeg7_cross)
        self.metadataCrossCompare(mpeg7, tva_cross)

    def metadataCrossCompare(self, in_orig, in_out):
        _log.info("+++ Cross compare metadata +++")
        if in_orig.metadataType == in_out.metadataType:
            _log.info("Metadata type: %s", in_orig.metadataType)
        else:
            _log.error("Trying to compare two different metadata types, '%s' != '%s'", in_orig.metadataType, in_out.metadataType)
        for m, a in in_orig.method2attrib.items():
            if m.startswith("get"):
                if m in in_out.method2attrib:
                    if not getattr(in_orig,m)(a) == getattr(in_out,m)(a):
                        _log.warn("Attribute '%s' present in both sets but different '%s' != '%s'.", a, getattr(in_orig,m)(a), getattr(in_out,m)(a))
                else:
                    _log.error("Method '%s' present in original set but not in the out instance - its attribute have been lost in translation.", a)

    def getMetaCore(self, xml=False, formatType=None):
        rmm = RichMetadataGenerator.getInstance()
        meta = rmm.getRichMetadata()
        meta.setProductionLocation("SI").setLanguage("Slovenian")
        meta.setOriginator("JSI")
        meta.setCaptionLanguage("SI").setGenre("Code").setPublisher("p2p-next")
        meta.setProductionDate("2010-8-16").setCaptionLanguage("EN")
        meta.setReleaseDate("2010-8-17").setTitleSeriesTitle("P2P-Next code")
        meta.setTitleMain("Rich Metadata implementation")
        meta.setTitleEpisodeTitle("Rich Metadata v" + __revision__)
        meta.setDuration("1M").setMinimumAge("3")
        meta.setHorizontalSize("640").setVerticalSize("480")
        meta.setFrameRate("27").setAspectRatio("4:3")
        meta.setVideoCoding("Generated").setAudioCoding("Manual")
        meta.setNumOfChannels("2").setFileSize("120k").setBitRate("75")
        meta.setSynopsis("Initial study of RichMetadata API according to the P2P-Next project design")
        meta.setProgramId("crid://p2p-next/example123")
        meta.setAudioCoding("MPEG-1 Audio Layer III")
        meta.setVideoCoding("MPEG-2 Video Main Profile @ Main Level")
        meta.setFileFormat("mp4")
        if xml:
            return rmm.build(meta, formatType)
        return meta

    def getMetaPayment(self, xml=False, formatType=None):
        rmm = RichMetadataGenerator.getInstance()
        meta = rmm.getRichMetadata(None, metadata.METADATA_PAYMENT)
        meta.setAcceptDonations("True")
        meta.setAdvancedInfos("http://www.p2p-next.org/paymentInformation.html")
        meta.setCurrency("EUR").setPaymentId("pay-one").setPaymentRecipient("me")
        meta.setPrice("2000").setProgramId("crid://p2p-next/seeMe")
        meta.setPublisher("p2p-next")
        if xml:
            return rmm.build(meta, formatType)
        return meta

    def getMetaAdvertising(self, xml=False, formatType=None):
        rmm = RichMetadataGenerator.getInstance()
        meta = rmm.getRichMetadata(None, metadata.METADATA_ADVERTISING)
        meta.setAdFormat("All-over").setAdType("P2PAdd").setAge("15")
        meta.setAllowAdvertising("True").setAspectRatio("16:9").setBusinessModel("BM2")
        meta.setCircularContent("Allow Superdistribution").setCountry("EU")
        meta.setFrameRate("30").setGender("W").setHorizontalSize("720")
        meta.setIsLiveContent("True").setProgramId("crid://market/me2")
        meta.setPublisher("p2p-next-2").setStreamingType("In-stream")
        meta.setVerticalSize("405").setVideoCoding("MPEG-4 Video")
        if xml:
            return rmm.build(meta, formatType)
        return meta

    def getMetaScalability(self, xml=False, formatType=None):
        rmg = RichMetadataGenerator.getInstance()
        meta = rmg.getRichMetadata(None, metadata.METADATA_SCALABILITY)
        meta.setAdaptationOperatorDependencyId("0 1 2 3")
        meta.setAdaptationOperatorQualityLevel("0 0 0 0")
        meta.setAdaptationOperatorTemporalLevel("0 0 0 0")
        meta.setConstraintBitrate("400 800 1200 2400")
        meta.setPPS("spsId=1,value=xyz:spsId=2,value=zxy")
        meta.setProgramId("crid://yet/another")
        meta.setPublisher("the one")
        meta.setSPS("spsId=1,width=20,height=16,value=kuku:spsId=2,width=3,height=2,value=lala")
        meta.setUtilityFramerate("25 25 25 25")
        meta.setUtilityHeight("240 240 480 480")
        meta.setUtilityWidth("320 320 640 640")
        if xml:
            return rmg.build(meta, formatType)
        return meta

    def getDIDBase(self, xml = False):
        rmg = RichMetadataGenerator.getInstance()
        meta = rmg.getRichMetadata(None, metadata.MPEG_21_BASE)
        meta.setIdentifier("urn:p2p-next:item:rtv-slo-slo1-xyz") 
        meta.setRelatedIdentifier("urn:rtv-slo:slo1-xyz") 
        # Will build core metadata of type TVA
        meta.setMetaCore(rmg.build(self.getMetaCore())) 
        meta.setPaymentReference("URI to additional MPEG_21 data (payment)") 
        meta.setAdvertisementReference("URI to additional MPEG_21 data (advertising)") 
        meta.setScalabilityReference("URI to additional MPEG_21 data (scalability)")
        meta.setContentReference("URI to video included in the torrent")
        meta.setContentType("video/ts") 
        meta.setLimoReference("URI to additional MPEG_21 data (limo)")
        if xml:
            return rmg.build(meta)
        return meta

    def getDIDAdditional(self, xml=False):
        rmg = RichMetadataGenerator.getInstance()
        meta = rmg.getRichMetadata(None, metadata.MPEG_21_ADDITIONAL)
        meta.setRelatedIdentifier("urn:rtv-slo:slo1-xyz")
        meta.setCSSName("Name of the CSS file in Limo") 
        meta.setCss("Limo CSS content, should be included as XML CDATA") 
        meta.setHtml("Limo HTML content, should be included as XML CDATA") 
        meta.setJavascript("Limo Javascript content, should be included as XML CDATA") 
        meta.setJavascriptName("Name of Javascript file in Limo") 
        meta.setLogo("Logo graphics") 
        meta.setLogoName("Name of the logo file") 
        meta.setLogoReference("URI reference to the logo (Needed indeed?)") 
        # Note that parsing depends on proper definition of mime type
        # start (image/)
        meta.setLogoType("image/Mime type of logo") 
        # Will build advertising metadata of type TVA
        meta.setMetaAdvertisement(rmg.build(self.getMetaAdvertising()))
        # Will build payment metadata of type TVA
        meta.setMetaPayment(rmg.build(self.getMetaPayment())) 
        # Will build scalability metadata of type TVA
        meta.setMetaScalability(rmg.build(self.getMetaScalability()))
        if xml:
            return rmg.build(meta)
        return meta

    def metaMap(self):
        metaMap = {"core": self.getMetaCore(),
                   "payment": self.getMetaPayment(),
                   "advertising": self.getMetaAdvertising(),
                   "scalability": self.getMetaScalability()}
        return metaMap

    def didMap(self):
        didmap = {"base": self.getDIDBase(),
                  "additional": self.getDIDAdditional()}
        return didmap

    def testALearn(self):
        log.setLevel(llA)
        _log.info("------- Learn test --------")
        rmm = RichMetadataGenerator.getInstance()
        for m in rmm.knownMasters():
            master = rmm.getMaster(m)
            _log.debug("Learned from master: %s, %s", master.formatType, master.metadataType)
            _log.debug("\n" + master.root.toString())

    def testBGetMetadata(self):
        log.setLevel(llB)
        _log.info("------- Get metadata --------")
        rmm = RichMetadataGenerator.getInstance()
        tva = rmm.getRichMetadata(metadata.LEARN_BASE_CORE[metadata.TAG_TVA_MAIN])
        _log.debug("\n" + tva.toString())
        mpeg7 = rmm.getRichMetadata(metadata.LEARN_BASE_CORE[metadata.TAG_MPEG7], metadata.TAG_MPEG7)
        _log.debug("\n" + mpeg7.toString())
        for k in tva.core:
            self.assertTrue(mpeg7.core.has_key(k))
        for k in tva.core:
            _tvaExists = False
            _mpeg7Exists = False
            if getattr(tva, k):
                _tvaExists = True
            if getattr(mpeg7, k):
                _mpeg7Exists = True
            if _tvaExists != _mpeg7Exists:
                _log.warn("Offending core key %s, TVA = %s, MPEG7 = %s", k, _tvaExists, _mpeg7Exists)

    def testCHelper(self):
        log.setLevel(llC)
        _log.info("------- Helper test --------")
        a = "{kuku}lala"
        helper = metadata.HELPER[metadata.GET_TAG]
        self.assertEqual(helper(a), "lala")
        helper = metadata.HELPER[metadata.SPLIT_TAG]
        self.assertEqual(helper(a), ["kuku", "lala"])
        e = Element('test', {'{a}b':'c','{d12}d':'{e}[]','{d?"?E#}f':'{}g'})
        helper = metadata.HELPER[metadata.SPLIT_ATTRIBS]
        res = helper(e)
        for k, v in e.attrib.items():
            t = k.split("}")[1]
            self.assertEqual(v,res[t])
        e.text = "    test\nlala    "
        helper = metadata.HELPER[metadata.GET_TEXT]
        self.assertEqual(helper(e), "    test\nlala    ")
        e.text = "    \n    "
        self.assertEqual(helper(e), "")
        e.text = ""
        c = SubElement(e, metadata.TAG_NAME)
        c.text = "This text describes the parent"
        helper = metadata.HELPER[metadata.TAG_SUPPRESS]
        self.assertEqual(helper(c, e), ('test', 'This text describes the parent'))
        inputData = StringIO("<root><Welookfor><Name>data</Name></Welookfor></root>")
        events = ("start", "end")
        iterator = iterparse(inputData, events=events)
        for event, elem in iterator:
            if event == "end":
                if elem.tag == "Name":
                    self.assertEqual(helper(elem, iterator.next()[1]), ('Welookfor', 'data'))

    def testDBuild(self):
        log.setLevel(llD)
        _log.info("------- Build test --------")
        rmm = RichMetadataGenerator.getInstance()
        tva = rmm.getRichMetadata(metadata.LEARN_BASE_CORE[metadata.TAG_TVA_MAIN])
        xml_tva = rmm.build(tva)
        _log.debug(rmm.prettyPrint(xml_tva))
        mpeg7 = rmm.getRichMetadata(metadata.LEARN_BASE_CORE[metadata.TAG_MPEG7])
        xml_mpeg7 = rmm.build(mpeg7, metadata.TAG_MPEG7)
        _log.debug(rmm.prettyPrint(xml_mpeg7))

    def testECrossBuilds(self, tva_in=None, mpeg7_in=None):
        log.setLevel(llE)
        _log.info("------- Cross build --------")
        rmg = RichMetadataGenerator.getInstance()
        tva_xml = rmg.build(self.getMetaCore())
        mpeg7_xml = rmg.build(self.getMetaCore(), metadata.TAG_MPEG7)
        _log.debug(rmg.prettyPrint(tva_xml))
        _log.debug(rmg.prettyPrint(mpeg7_xml))
        self.crossBuildsCompareXML(tva_xml, mpeg7_xml)
 
    def testGDynamicMethods(self):
        log.setLevel(llG)
        _log.info("------- Dynamic methods test --------")
        rmm = RichMetadataGenerator.getInstance()
        meta = rmm.getRichMetadata()
        meta.setProductionLocation("SI").setLanguage("Slovenian").setOriginator("JSI")
        meta.setCaptionLanguage("SI").setGenre("Code").setPublisher("p2p-next")
        meta.setMinimumAge("3").setProductionDate("2010-8-16").setCaptionLanguage("EN")
        meta.setReleaseDate("2010-8-17").setTitleSeriesTitle("P2P-Next code")
        meta.setTitleMain("Rich Metadata implementation")
        meta.setTitleEpisodeTitle("Rich Metadata v" + __revision__)
        meta.setDuration("0.75MM").setHorizontalSize("2").setVerticalSize("cca. 1300")
        meta.setVideoCoding("Generated").setAudioCoding("Manual").setFrameRate("1")
        meta.setNumOfChannels("2").setFileSize("cca. 56k").setBitRate("75")
        meta.setAspectRatio("Substantial")
        meta.setSynopsis("Initial study of RichMetadata API according to the P2P-Next project design")
        xml_tva = rmm.build(meta)
        _log.debug(rmm.prettyPrint(xml_tva))
        xml_mpeg7 = rmm.build(meta, metadata.TAG_MPEG7)
        _log.debug(rmm.prettyPrint(xml_mpeg7))
        self.crossBuildsCompareXML(xml_tva, xml_mpeg7)
        for m in metadata.METADATA_SETS:
            meta = rmm.getRichMetadata(None, m)
            out = ""
            apimethods = meta.getAPIMethods()
            apimethods.sort()
            for method in apimethods:
                out += method + ", "
            out = out.strip().rstrip(",")
            _log.debug(m.capitalize() + " metadata set current API methods: " + out)

    def testHSparseMetadata(self):
        log.setLevel(llH)
        _log.info("------- Sparse metadata test --------")
        rmm = RichMetadataGenerator.getInstance()
        meta = rmm.getRichMetadata()
        meta.setProductionLocation("SI").setLanguage("Slovenian").setOriginator("JSI")
        xml_tva = rmm.build(meta)
        xml_mpeg7 = rmm.build(meta, metadata.TAG_MPEG7)
        _log.debug(rmm.prettyPrint(xml_tva))
        _log.debug(rmm.prettyPrint(xml_mpeg7))
        self.crossBuildsCompareXML(xml_tva, xml_mpeg7)
        meta2 = rmm.getRichMetadata()
        meta2.setTitleMain("Rich Metadata implementation")
        meta2.setNumOfChannels("2").setFileSize("cca. 56k").setBitRate("75")
        meta2.setHorizontalSize("2").setVerticalSize("cca. 1300")
        xml_tva2 = rmm.build(meta2)
        _log.debug(rmm.prettyPrint(xml_tva2))
        xml_mpeg7_2 = rmm.build(meta2, metadata.TAG_MPEG7)
        _log.debug(rmm.prettyPrint(xml_mpeg7_2))
        self.crossBuildsCompareXML(xml_tva2, xml_mpeg7_2)

    def testIOptionalMetadata(self):
        log.setLevel(llI)
        _log.info("------- Optional metadata test --------")
        rmg = RichMetadataGenerator.getInstance()
        rm_tva_xml = dict()
        rm_mpeg7_xml = dict()
        mmap = self.metaMap()
        _log.debug("+ get RichMetadata instance")
        for k, v in mmap.items():
            _log.debug("\n" + v.toString())
        _log.debug("+ RichMetadata instance to XML")
        for k, v in mmap.items():
            xml = rmg.build(v)
            rm_tva_xml["tva_" + k] = xml
            _log.debug(rmg.prettyPrint(xml))
            xml = rmg.build(v, metadata.TAG_MPEG7)
            rm_mpeg7_xml["mpeg7_" + k] = xml
            _log.debug(rmg.prettyPrint(xml))
        _log.debug("+ XML back to RichMetadata instance")
        for k, v in rm_tva_xml.items():
            _log.debug("++ " + k + " to meta")
            m = rmg.getRichMetadata(v)
            orig = k.split("_")[1]
            self.metadataCrossCompare(mmap[orig], m)
        for k, v in rm_mpeg7_xml.items():
            _log.debug("++ " + k + " to meta")
            m = rmg.getRichMetadata(v)
            orig = k.split("_")[1]
            self.metadataCrossCompare(mmap[orig], m)
        _log.debug("+ RichMetadata instance TVA cross to MPEG7 XML")
        for k, v in mmap.items():
            xml_tva = rmg.build(v)
            xml_mpeg7 = rmg.build(v, metadata.TAG_MPEG7)
            self.crossBuildsCompareXML(xml_tva, xml_mpeg7)

    def testJDIDMetadata(self):
        log.setLevel(llJ)
        _log.info("------- DID metadata test --------")
        rmg = RichMetadataGenerator.getInstance()
        _rm = dict()
        _log.debug("+ Get DID RichMetadata instances")
        for k, v in self.didMap().items():
            _rm[k] = v
            _log.debug("\n" + v.toString())
        richm = list()
        richm.append(_rm["base"])
        richm.append(_rm["additional"])
        _log.debug("+ RichMetadata instance DID to XML")
        didxml = list()
        for m in richm:
            xml = rmg.build(m)
            didxml.append(xml)
            _log.debug(rmg.prettyPrint(xml))
        _log.debug("+ DID XML back to RichMetadata instance ")
        i = 0
        for v in didxml:
            m = rmg.getRichMetadata(v)
            self.metadataCrossCompare(richm[i], m)
            i += 1

    def testZSpeed(self):
        if not runspeed:
            _log.warn("Speed test disabled, turn on runspeed variable to run it.")
            return
        _log.info("------- Speed test, please wait --------")
        rmm = RichMetadataGenerator.getInstance()
        sts = StatisticTimeSeries("Test Rich Metadata python implementation")
        test = [("Parsing XML TVA  ", self.getMetaCore(True)), ("Parsing XML MPEG7", self.getMetaCore(True, metadata.TAG_MPEG7))]
        for n, s in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.getRichMetadata(s)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        #########
        meta = self.getMetaCore()
        sparse = rmm.getRichMetadata()
        sparse.setProductionLocation("SI").setLanguage("Slovenian").setOriginator("JSI")
        test = [("Building XML TVA", meta, metadata.TAG_TVA_MAIN), 
                ("Building XML MPEG7", meta, metadata.TAG_MPEG7), 
                ("Sparse build TVA", sparse, metadata.TAG_MPEG7), 
                ("Sparse build MPEG7", sparse, metadata.TAG_MPEG7)]
        for n, s, format in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.build(s, format)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        #########
        xml_tva = self.getMetaCore(True)    
        sts.start("Cross build TVA ")
        for t in range(1,11):
            sts.new()
            for i in range(1,101):
                rm = rmm.getRichMetadata(xml_tva)
                rmm.build(rm, metadata.TAG_MPEG7)
            sts.add(100)
        sts.stop()
        _log.info("Cross build TVA - Done")
        xml_mpeg7 = self.getMetaCore(True, metadata.TAG_MPEG7)    
        sts.start("Cross build MPEG7")
        for t in range(1,11):
            sts.new()
            for i in range(1,101):
                rm = rmm.getRichMetadata(xml_mpeg7)
                rmm.build(rm)
            sts.add(100)
        sts.stop()
        _log.info("Cross build MPEG7 - Done")
        #########
        sts.start("TVA from scratch")
        for t in range(1,11):
            sts.new()
            for i in range(1,101):
                # Default type - core
                meta = rmm.getRichMetadata()
                meta.setProductionLocation("SI").setLanguage("Slovenian").setOriginator("JSI")
                meta.setCaptionLanguage("SI").setGenre("Code").setPublisher("p2p-next")
                meta.setMinimumAge("3").setProductionDate("2010-8-16").setCaptionLanguage("EN")
                meta.setReleaseDate("2010-8-17").setTitleSeriesTitle("P2P-Next code")
                meta.setTitleMain("RichMetadata implementation")
                meta.setTitleEpisodeTitle("Rich Metadata v" + __revision__)
                meta.setDuration("0.75MM").setHorizontalSize("2").setVerticalSize("cca. 1300")
                meta.setVideoCoding("Generated").setAudioCoding("Manual").setFrameRate("1")
                meta.setNumOfChannels("2").setFileSize("cca. 56k").setBitRate("75")
                meta.setAspectRatio("Substantial")
                meta.setSynopsis("Initial study of RichMetadata API according to the P2P-Next project design")
                xml_tva = rmm.build(meta)
            sts.add(100)
        sts.stop()
        _log.info("TVA from scratch - Done")
        sts.start("MPEG7 from scratch")
        for t in range(1,11):
            sts.new()
            for i in range(1,101):
                # Default type - core
                meta = rmm.getRichMetadata()
                meta.setProductionLocation("SI").setLanguage("Slovenian").setOriginator("JSI")
                meta.setCaptionLanguage("SI").setGenre("Code").setPublisher("p2p-next")
                meta.setMinimumAge("3").setProductionDate("2010-8-16").setCaptionLanguage("EN")
                meta.setReleaseDate("2010-8-17").setTitleSeriesTitle("P2P-Next code")
                meta.setTitleMain("Rich Metadata implementation")
                meta.setTitleEpisodeTitle("Rich Metadata v" + __revision__)
                meta.setDuration("0.75MM").setHorizontalSize("2").setVerticalSize("cca. 1300")
                meta.setVideoCoding("Generated").setAudioCoding("Manual").setFrameRate("1")
                meta.setNumOfChannels("2").setFileSize("cca. 56k").setBitRate("75")
                meta.setAspectRatio("Substantial")
                meta.setSynopsis("Initial study of RichMetadata API according to the P2P-Next project design")
                xml_mpeg7 = rmm.build(meta, metadata.TAG_MPEG7)
            sts.add(100)
        _log.info("MPEG7 from scratch - Done")
        sts.stop()
        #########
        test = [("Parsing payments TVA", self.getMetaPayment(True)), 
                ("Parsing advert. TVA", self.getMetaAdvertising(True)), 
                ("Parsing scalab. TVA", self.getMetaScalability(True)), 
                ("Parsing paym. MPEG7", self.getMetaPayment(True, metadata.TAG_MPEG7)), 
                ("Parsing advert. MPEG7", self.getMetaAdvertising(True, metadata.TAG_MPEG7)), 
                ("Parsing scalab. MPEG7", self.getMetaScalability(True, metadata.TAG_MPEG7))]
        for n, s in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.getRichMetadata(s)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        #########
        test = [("Build payments TVA", self.getMetaPayment(), metadata.TAG_TVA_MAIN), 
                ("Build advert. TVA", self.getMetaAdvertising(), metadata.TAG_TVA_MAIN), 
                ("Build scalab. TVA", self.getMetaScalability(), metadata.TAG_TVA_MAIN), 
                ("Build paym. MPEG7", self.getMetaPayment(), metadata.TAG_MPEG7), 
                ("Build advert. MPEG7", self.getMetaAdvertising(), metadata.TAG_MPEG7), 
                ("Build scalab. MPEG7", self.getMetaScalability(), metadata.TAG_MPEG7)]
        for n, s, format in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.build(s, format)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        #########
        test = [("Parse DID base    ", self.getDIDBase(True)),
                ("Parse DID addit.  ", self.getDIDAdditional(True))]
        for n, s, in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.getRichMetadata(s)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        test = [("Build DID base    ", self.getDIDBase()),
                ("Build DID addit.  ", self.getDIDAdditional())]
        for n, s, in test:
            sts.start(n)
            for t in range(1,11):
                sts.new()
                for i in range(1,101):
                    rmm.build(s)
                sts.add(100)
            sts.stop()
            _log.info(n + " - Done")
        #########
        _log.info(sts.toString())

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(RichMetadataTest)

if __name__ == "__main__":
    unittest.main()
