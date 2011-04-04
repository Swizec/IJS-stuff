from base64 import encodestring
from datetime import datetime
import os 
import shutil
from time import mktime
import urllib
from urlparse import urlparse

from JSI.ProviderToolbox.MetadataGenerator import Feed
from JSI.ProviderToolbox.FeedGenerator import P2PNextAtomFeed, P2PNextLiveAtomFeed
from JSI.ProviderToolbox.utils import log
from JSI.ProviderToolbox.utils.utilities import textify, asciify, classImport, Fetch, TimeSorter, time2duration
from JSI.ProviderToolbox.conf import settings
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

from BaseLib.Core.TorrentDef import TorrentDef
from BaseLib.Core.ClosedSwarm import ClosedSwarm

__author__ = 'D. Gabrijelcic (dusan@e5.ijs.si)'
__revision__ = '0.24'
__all__ = ['ContenSource', 'Channel', 'ContentUnit', 
           'RTVVoDContent', 'classpath', '__revision__']


_log = log.getLog('ContentSource')
log.setLevel(log.DEBUG)
# Used to import content unit classes 
classpath = "JSI.ProviderToolbox.ContentSource"

class Identify(object):

    def __init__(self, select=None):
        """
        Initialize identification and specify the method.

        @param select A string that specifies a method for
                      identification. If None, a default method is
                      provided. The string should be a key in a config
                      dict variable settings.IDENTIFY_HELPER.
        """ 
        self.imethod = settings.IDENTIFY_HELPER.get(settings.IDENTIFY)
        if select != None:
            if settings.IDENTIFY_HELPER.get(select):
                self.imethod = settings.IDENTIFY_HELPER.get(select)
            else:
                _log.warn("Specfied identification method with the method parameter select '%s' is not available, the default identification method will be used.", select)
        # List of attributes for identification
        self.identifyAttr = None

    def identify(self, string=None):
        """
        Produces identifier based on selected identification method
        and object attributes specified as a list in class attribute
        identifyAttr or supplied parameter string. A list of
        attributes can contain either rich methadata methods or object
        attributes.

        The method returns either an identification string or
        None. None is returned if a string on which is identification
        based is less then 8 characters. Identification attributes
        should be selected in a way to uniquely identify an instance.

        @param string A string on which the identification is made if
                      an iheriting instance does not specifiy an
                      identifyAttr
        @return Identification string or None
        """
        if string != None:
            return self.imethod(string)
        i = ""
        for s in self.identifyAttr:
            try:
                f = getattr(self.metadata, s)
                _i = f()
                if _i != None:
                    i += _i
            except:
                try:
                    i += getattr(self, s)
                except:
                    _log.debug("Attribute '%s' specified for identification is not present in the class '%s' instance.", s, self.__class__.__name__)
        if len(i) < 8:
            _log.warn("String '%s' used for class '%s' instance identification is very short - '%s' characters. Consider providing longer unique string!", i, self.__class__.__name__, len(i))
            return None
        return self.imethod(i)

class ContentUnit(Identify):
    """
    An unit of content.
    """
    def __init__(self, cutype=settings.CONTENT_VOD):
        Identify.__init__(self)
        # Type of content unit, not used
        self.cutype = cutype
        # Name of the unit
        self.name = None
        # Identifier of the unit
        self.identifier = None
        # Rich metadata
        self.metadata = None
        # Torrent file
        self.torrent = None
        # Image
        self.image = None
        # Location of per cu DID base file (template)
        self.didbaseFile = None
        # DID base
        self.didbase = {}
        # Feed store
        self.feedStore = None
        # Content or the essence of the unit - name of the file
        self.contentFile = None
        # Metadata file of the unit - name of the file
        self.metaFile = None
        # Shadow file
        self.shadow = None
        # Time of fetch - creation time - or time of metadata file
        # creation - restore
        self.timestamp = None
        # Stored on the node?
        self.stored = False
        # Fresh ?
        self.fresh = False
        # ClosedSwarm ? 
        self.cskeyfile = None
        # Acquire content? Alwayse defined per CS settings 
        self.acquire = False
        # Identify attributes are based on rich metadata specification
        # plus content file name
        self.identifyAttr = ["getTitleMain",
                             "getTitleEpisodeTitle",
                             "getPublisher",
                             "getOriginator",
                             "getFileSize",
                             "getDuration",
                             # Content unit attribute
                             "contentFile"]

    def __cmp__(self, other):
        """
        Compare two cuntent unit instances. Not all instance
        attributes are compared.

        @param other Other instance to compare
        @return int O if equal, -1 if otherwise
        """
        if self.__class__.__name__ != other.__class__.__name__:
            _log.debug("Class instances differ, %s != %s", self.__class__.__name__, other.__class__.__name__)
            return -1
        # Attributes to ignore
        ignore = ["identifyAttr", "metadata", "imethod", "timestamp"]
        for a in self.__dict__:
            if a not in ignore:
                try:
                    if getattr(self, a) != getattr(other, a):
                        _log.debug("Instance of %s attribute differs: %s != %s", self.__class__.__name__, getattr(self, a), getattr(other, a))
                        return -1
                except:
                    _log.debug("Failed to get class %s attribute %s", self.__class__.__name__, a)
                    pass
        if self.metadata != other.metadata:
            return -1
        return 0

    def store(self, url):
        """
        Acquire the content form url specified and store the content
        unit in a feed as specified with instance attribute feedStore
        together with rich metadata.

        @param url Url of the link to content
        """
        if self.feedStore != None:
            filehandle = None
            cpath = None
            if url != None:
                if self.acquire:
                    f = Fetch(self.feedStore)
                    try:
                        filehandle = f.acquire(url)
                    except Exception, e:
                        _log.error("Failed to acquire content named %s at specified reference %s with an exception: %s", self.name, url, str(e))
                        return
                    cpath = os.path.realpath(filehandle.name)
                    self.contentFile = os.path.basename(cpath)
                    filehandle.close()
                else:
                    _log.debug("Acquire is %s content named '%s', at url %s wont be acquired.", self.acquire, self.name, url)
                    u = urlparse(url)
                    if u.scheme == 'http':
                        cn = os.path.basename(u.path)
                        cpath = self.feedStore + os.path.sep + cn
            else:
                _log.warn("Storing of content named '%s', has failed, url specified is None.", self.name)
            if cpath != None:
                (base, e) = os.path.splitext(cpath)
                self.storeMeta(base)
        if self.isStored():
            self.stored = True


    def storeMeta(self, fileName):
        """
        Store content related rich metadata.

        @param fileName Basename of the content file (full path) 
                        without an extension
        """
        if fileName != None:
            if self.metadata != None:
                rmg = RichMetadataGenerator.getInstance()
                rm = rmg.getRichMetadata()
                if isinstance(self.metadata, rm.__class__):
                    if self.metadata.metadataType == metadata.METADATA_CORE:
                        xmlpath = fileName + settings.METADATA_EXT
                        if not os.path.exists(xmlpath):
                            _log.debug("Creating core metadata file %s for the content named '%s'", xmlpath, self.name)
                        else:
                            _log.debug("Overwriting core metadata file %s for the content named '%s'", xmlpath, self.name)
                        xmlfile = open(xmlpath, 'w')
                        xmlfile.write(rmg.build(self.metadata))
                        xmlfile.close()
                        self.metaFile = os.path.basename(xmlpath)
                    else:
                        _log.warn("Failed to write content unit named '%s' metadata, metadata is not of a type %s but %s", self.name, settings.METADATA_CORE, self.metadata.metadataType)
                else:
                    _log.warn("Failed to write content unit named '%s' metadata, metadata is not an instance of RichMetadata but %s", self.name, self.metadata.__class__.__name__)
            else:
                _log.warn("Failed to write content unit named '%s' metadata, metadata is None", self.name)

    def isStored(self):
        """
        Decides, if the content unit is stored on the node. 

        @returns Boolean True if stored else False
        """
        content = False
        meta = False
        if self.feedStore != None:
            if self.contentFile != None:
                cf = os.path.join(self.feedStore, self.contentFile)
                if os.path.exists(cf):
                    content = True
            if self.metaFile != None:
                mf = os.path.join(self.feedStore, self.metaFile)
                if os.path.exists(mf):
                    meta = True
        if self.acquire:
            if content and meta:
                return True
        else:
            if meta:
                return True
        return False

    def createTime(self, path=None):
        """
        Provides create time of the content unit. If path is specified
        the time is based on last modification time of the file else
        on the current time

        @param path Path of the file (metadata)
        @return float Unix time
        """
        if path and os.path.exists(path):
            return os.path.getmtime(path)
        else:
            time = datetime.now()
        return mktime(time.timetuple())+1e-6*time.microsecond

    def setDIDBase(identifier=None, limor=None, advertisingr=None, 
                   paymentr=None, scalabilityr=None, related=None):
        """
        Sets DID base data that is used in export per item

        @param identifier Identifier
        @param limor Limo reference
        @param advertisingr Advertising reference
        @param paymentr Payment reference
        @param scalabilitr Scalability reference
        @param related Related identifier
        """
        self.didbase= {"identifier": identifier,
                       "limo": limor,
                       "advertising": advertisingr,
                       "payment": paymentr,
                       "scalability": scalabilityr,
                       "related": relatedr}

    def setDIDBaseFile(self, didbasefile):
        """
        Sets DID base file that is used in export per item. Non core
        metadata gets stored in didbase dictionary

        @param didbasefile Path to DID base file
        @return RichMetadata DID base RichMetadata instance 
        """
        if os.path.exists(didbasefile):
            if os.path.isfile(didbasefile):
                rmg = RichMetadataGenerator.getInstance()
                didrm = rmg.getRichMetadata(didbasefile)
                if didrm != None:
                    if didrm.metadataType == metadata.METADATA_DID_BASE:
                        didbase = {}
                        didbase['identifier'] = didrm.getIdentifier()
                        didbase['related'] = didrm.getRelatedIdentifier()
                        didbase['limo'] = didrm.getLimoReference()
                        didbase['payment'] = didrm.getPaymentReference()
                        didbase['advertising'] = didrm.getAdvertisementReference()
                        didbase['scalability'] = didrm.getScalabilityReference()
                        self.didbase = didbase
                    else:
                        _log.debug("Failed to get DID base metadata from specified file '%s', metadata type %s is not DID base", didbasefile, didrm.formatType)
                        return None
                    return didrm
                else:
                    _log.debug("Failed to get DID base metadata from specified file '%s'", didbasefile)
            else:
                _log.debug("Specified DID base argument '%s' is not a file, failed to set didbase attribute", didbasefile)
        else:
            _log.debug("Specified DID base file '%s' does not exists, failed to set didbase attribute", didbasefile)
        return None

    def loadDIDBaseData(self, path):
        """
        Loads DID base metadata from a path

        @param string Path to DID base file
        """
        didrm = self.setDIDBaseFile(path)
        if didrm != None:
            self.metadata = didrm.getMetaCore()
            
    def buildDIDBaseXMLData(self):
        rmg = RichMetadataGenerator.getInstance()
        bdid = rmg.getRichMetadata(None, metadata.MPEG_21_BASE)
        if self.metadata:
            cm_xml = rmg.build(self.metadata)
            bdid.setMetaCore(cm_xml)
        if self.contentFile != None:
            bdid.setContentReference(self.contentFile)
            (b, e) = os.path.splitext(self.contentFile)
            ext = e.lstrip(".")
            if settings.MIME_TYPES_MAP.has_key(ext):
                bdid.setContentType(settings.MIME_TYPES_MAP[ext])
        if self.getId() != None: 
            bdid.setIdentifier(self.getId())
        elif self.didbase.get('identifier'):
            bdid.setIdentifier(didbase['identifier'])
        if self.didbase.get('related'):
            bdid.setRelatedIdentifier(didbase['related'])
        if self.didbase.get('limo'):
            bdid.setLimoReference(didbase['limo'])
        if self.didbase.get('advertising'):
            bdid.setAdvertisementReference(didbase['advertising'])
        if self.didbase.get('payment'):
            bdid.setPaymentReference(didbase['payment'])
        if self.didbase.get('scalability'):
            bdid.setSclabilityReference(didbase['scalability'])
        return rmg.build(bdid)

    def storeDIDBaseData(self, path):
        """
        Stores DID base metadata in a file specified in the path

        @param string A full path to DID base file without an extension
        """
        if path != None:
            xmlpath = path + settings.METADATA_EXT
            if os.path.isdir(os.path.dirname(xmlpath)):
                if not os.path.exists(xmlpath):
                    _log.debug("Creating DID base metadata file %s for the content named '%s'", xmlpath, self.name)
                else:
                    _log.debug("Overwriting DID base metadata file %s for the content named '%s'", xmlpath, self.name)
                    xmlfile = open(xmlpath, 'w')
                    xmlfile.write(self.buildBIDBaseXMLData())
                    xmlfile.close()
                    self.metaFile = os.path.basename(xmlpath)
            else:
                _log.warn("Trying to write content unit named '%s' DID base metadata to non exsistent directory %s", self.name, path)
        else:
            _log.warn("Failed to write content unit named '%s' DID base metadata, path is None", self.name)

    def findTorrentFile(self):
        """
        Finds content unit torrent file
        
        @return string Name of the torrent file or None if not present
        """
        if self.contentFile:
            (b, e) = os.path.splitext(self.contentFile)
            u = os.path.join(settings.TORRENT_DIR, b + '.url')
            t = os.path.join(settings.TORRENT_DIR, b + '.tstream')
            if os.path.exists(u):
                return b + '.url'
            if os.path.exists(t):
                return b + '.tstream'
        return None

    def findCSFile(self):
        tdef = TorrentDef.load(os.path.join(settings.TORRENT_DIR, self.torrent))
        kfile =  encodestring(tdef.infohash).replace("\n","").replace("/","").replace("\\","")
        cs_key_file = os.path.join(settings.CS_PUBLISH_DIR, kfile + ".tkey")
        if os.path.exists(cs_key_file):
            return kfile + ".tkey"
        return None

    def getImage(self):
        """
        Per content unit settable image. Define any mapping on content
        unit attributes ta return the image location as a string. If
        the method is not overloaded in inheriting class the image
        will equal to feed image.

        @return string String or None.
        """
        return self.image

    def getId(self):
        """
        Per content unit settable id. Define any mapping on content
        unit attributes ta return the content id as a string. If the
        method returns None content unit id will be equal to its link.

        @return string String or None.
        """
        return None

    def getPublish(self):
        """
        Per content unit settable relative publishing link. Define any
        mapping on content unit attributes ta return the content
        relative publishing link as a string. If the method is not
        overloaded by inheriting class the content unit relative
        publishing link will be equal to its torrent publication.

        @return string String or None.
        """
        if settings.XML_EXPORT:
            return self.shadow
        return self.torrent

    def exportShadow(self, path, relative_name=None):
        """
        Exports core rich metadata XML representation as a content,
        store in the path.
        """
        assert os.path.isdir(path)
        if relative_name != None:
            self.shadow = relative_name
        else:
            self.shadow = self.getShadow()
        if not os.path.isfile(os.path.join(path, self.shadow)):
            xmlpath = os.path.join(path, self.shadow)
            xmlfile = open(xmlpath, 'w')
            rmg = RichMetadataGenerator.getInstance()
            # Backward compatible
            if self.metadata.getDuration():
                d = self.metadata.getDuration()
                if not d.startswith("P"):
                    self.metadata.setDuration(time2duration(d))
            if self.metadata.getBitRate():
                try:
                    br = int(self.metadata.getBitRate())
                except Exception, e:
                    br = self.metadata.getBitRate()
                    br = br.rstrip(" kb/s").strip()
                    try:
                        br = int(br)
                        self.metadata.setBitRate(str(br*1024))
                    except Exception, e:
                        pass
            xmlfile.write(rmg.build(self.metadata, metadata.TAG_MPEG7))
            xmlfile.close()

    def getShadow(self):
        if self.shadow:
            return self.shadow
        else:
            assert self.metaFile != None
            return os.path.splitext(self.metaFile)[0]

    def toString(self):
        """
        For debuging purposes
        """
        ignore = ["identifyAttr", "metadata", "imethod"]
        out = "Content unit: "
        for a in self.__dict__:
            if a not in ignore:
                if getattr(self, a):
                    out += a + ": " + unicode(getattr(self, a)) + ", "
        out += "\n   + metadata: "
        for a in self.identifyAttr:
            try:
                f = getattr(self.metadata, a)
                if f():
                    out += a + ": " + f() + ", "
            except:
                pass
        out = out.rstrip(",")
        return out + "\n"

class RTVVoDContent(ContentUnit):

    def __init__(self, cutype=settings.CONTENT_VOD):
        ContentUnit.__init__(self)

    def getId(self):
        return settings.URN + settings.P2P_NEXT + settings.COLON + settings.RTV_SLO + settings.COLON + self.identifier

    def exportShadow(self, path, relative_name=None):
        # Changes the name from unit name to identifier.
        super(RTVVoDContent, self).exportShadow(path, self.identifier)        

    def getShadow(self):
        return self.identifier

    # Sets the image per content unit. But some needs to generate the
    # images on the end. Assumed that the images are in the same
    # exported dir as the shadows. If the complete link is provided it
    # won't get overwritten - otherwise the return valu will be
    # relative to feed publishing link
    def getImage(self):
        return self.getPublish() + ".png"

class ContentSource(Identify):
    """
    A content source defines where the content can be obtained
    from. Content source is a list holding related content units
    identifiers.
    """
    def __init__(self):
        Identify.__init__(self)
        self.cstype = None
        self.name = None
        self.identifier = None
        self.location = None
        self.image = None
        # Unique content source identifier (export feed)
        self.guid = None
        # Rich metadata
        self.metadata = None
        # CS storage
        self.storage = None
        self.metaFile = None
        # CS shadow (XML exports)
        self.shadow = None
        # The items
        self.items = {}
        # Holds the list of last fresh content units identifiers
        self.lastFreshList = []
        # Acquire content?
        self.acquire = True
        # Exist already?
        self.present = False
        # Location of DID base file
        self.didbaseFile = None
        # DID base data
        self.didbase = None
        # Root for publishing (used with content unit publish)
        self.publish = None
        # Exported feed link
        self.exportFeedLink = None
        # Content unit class instance name serving as template for
        # items
        self.contentUnitClassInstance = None
        # Content unit class instance
        self.cuci = None
        # Time sorter
        self.timesort = TimeSorter()
        # Window
        self.window = None
        # The source metadata
        self.sourceMeta = None
        # Preserved attributes 
        self.storeAttr = ["location", 
                          "name",
                          "cstype", 
                          "publish",
                          "image", 
                          "contentUnitClassInstance", 
                          "exportFeedLink", 
                          "didbaseFile",
                          "guid",
                          "window"]

    def __cmp__(self, other):
        """
        Compare two content source instances. Not all instance
        attributes are compared.

        @param other Other instance to compare
        @return int O if equal, -1 if otherwise
        """
        if self.__class__.__name__ != other.__class__.__name__:
            _log.debug("Class instances differ, %s != %s", self.__class__.__name__, other.__class__.__name__)
            return -1
        # Attributes to ignore
        ignore = ["storeAttr", "sourceMeta", "items", 
                  "imethod", "timesort", "cuci"]
        for a in self.__dict__:
            if a not in ignore:
                try:

                    if getattr(self, a) != getattr(other, a):
                        _log.debug("Instance of %s attribute  %s differs: %s != %s", self.__class__.__name__, a, getattr(self, a), getattr(other, a))
                        return -1
                except:
                    _log.debug("Failed to get class %s attribute %s", self.__class__.__name__, a)
                    pass
        if len(self.items) == len(other.items):
            for i, v in self.items.items():
                if other.items.get(i):
                    if v != other.items[i]:
                        return -1
                else:
                    _log.debug("Mismatch in identifiers, %s not present in other.", i)
                    return -1
        else:
            _log.debug("Number of content source items differ, %s != %s", len(self.items), len(other.items))
            return -1
        return 0

    def getContentSource(location, 
                         publish=None, 
                         contentUnitClassInstance = None,
                         exportFeedLink=None,
                         didbasefile=None,
                         window=None):
        """
        Creates or gets a content source based on location. If the
        source is already present on the node it gets restored first,
        otherwise a storage for the source is created. The content of
        the source is acquired through the update method. During every
        update for not yet published content units torrent files are
        generated based on metadata obtained in the original feed and
        data provided by ContentUnit class methods.

        In an exported feed the supplied parameter publish defines the
        absolute web path for published content units. Content units
        define relative path to the content which is concatenated
        with absolute path while building exported feed.

        Export feed link parameter defines a link at which the
        exported feed can be obtained from. If not present the feed
        link is defined as absolute path concatenated with textified
        (as defined in utilities) name of the feed.
        
        Window parameter defines a number of content units to keep in
        content source. If None (default) the content source is in a
        collection mode. No units gets removed. If set to 0 the length
        of the content source is the same as original source. Otherwise 
        the lengt is according to the parameter value. The content units 
        are removed according to their timestamp value, older first.

        @param location Location of the source
        @param publish Absolute path for publishing (web server)
        @param contentUnitClassName Name of the ContentUnit class
                                    customized per content provider
        @param exportFeedLink Link of exported feed
        @param didbasefile A location of DID base file
        @param window An integer number of content units to keep
        @return ContentSource instance
        """
        cs = ContentSource()
        cs.location = location
        cs.identifier = cs.identify(cs.location)
        if publish != None:
            cs.publish = publish
        if contentUnitClassInstance != None:
            cs.cuci = contentUnitClassInstance
            cs.contentUnitClassInstance = cs.cuci.__class__.__name__
        else:
            cs.cuci = ContentUnit()
        if exportFeedLink != None:
            cs.exportFeedLink = exportFeedLink
        if didbasefile != None:
            cs.didbaseFile = os.path.abspath(didbasefile)
            cs.setDIDBaseFile(cs.didbaseFile)
        if window != None:
            cs.window = window
        _log.debug("Create/get a content source for location: " + cs.location)
        return cs
    getContentSource = staticmethod(getContentSource)

    def store(self, force=False):
        """
        Stores a content source
        """
        if self.name != None:
            fdir = textify(self.name)
            fpath = os.path.join(settings.MEDIA_ROOT, fdir)
            if not os.path.exists(fpath):
                try:
                    os.mkdir(fpath)
                    force = True
                    _log.debug("Content source with name '%s' storage created in path '%s'", self.name, fpath)
                except Exception, e:
                    _log.error("Failed to make directory for content source named %s storage in path %s, exception was raised: %s", self.name, fpath, str(e))
                    return
            self.storage = fpath
            if force:
                self.storeAttributes()
                self.storeMeta()
            else:
                self.storage = fpath
                xmlf = fdir + settings.METADATA_EXT
                xmlpath = os.path.join(self.storage, xmlf)
                if os.path.exists(xmlpath):
                    self.metaFile = xmlf
                    self.present = True
                    _log.debug("Storage for content source named %s in path %s exists and metadata is already defined", self.name, self.storage)
                else:
                    _log.debug("Storage for content source named %s in path %s exists but metadata is not present", self.name, self.storage)

    def storeMeta(self):
        if self.name != None:
            meta = textify(self.name)
            if self.metadata != None:
                xmlf = meta + settings.METADATA_EXT
                xmlpath = os.path.join(self.storage, xmlf)
                xmlfile = open(xmlpath, 'w')
                rmg = RichMetadataGenerator.getInstance()
                xmlfile.write(rmg.build(self.metadata))
                xmlfile.close()
                self.metaFile = xmlf
                _log.debug("Content source named %s in path %s metadata stored in file %s", self.name, self.storage, xmlf)
            else:
                _log.debug("Storage for content source named %s in path %s exists but metadata wasn't stored since is None", self.name, self.storage)

    def isStored(self):
        """
        Decides if the content source is stored on the node. The source
        is stored if the source directory exists and the metadata of
        the source is stored.

        @returns Boolean True if present, else False 
        """
        store = False
        meta = False
        if self.storage != None:
            if os.path.isdir(self.storage):
                store = True
        if self.metaFile != None:
            mf = os.path.join(self.storage, self.metaFile)
            if os.path.exists(mf):
                meta = True
        if store and meta:
            return True
        return False

    def restore(self, path, csbase=None):
        """
        Restores the content source from a path

        @param path Directory holding the content source
        @param csbase Caller or template content source instance
        @return contentSource Content source instance
        """
        if os.path.isdir(path):
            cs = self.__new__(type(self))
            cs.__init__()
            cs.storage = os.path.realpath(path)
            cs.restoreAttributes()
            # Need to be known before restoring cu
            if csbase != None and csbase.cuci != None: 
                cs.contentUnitClassInstance = csbase.contentUnitClassInstance
                cs.cuci = csbase.cuci
            if cs.location != None:
                cs.identifier = cs.identify(cs.location)
            rmg = RichMetadataGenerator.getInstance()
            base = os.path.basename(path)
            csxml = base + settings.METADATA_EXT
            csxmlpath = os.path.join(path, csxml)
            if os.path.exists(csxmlpath):
                cs.metadata = rmg.getRichMetadata(csxmlpath)
                cs.name = cs.metadata.getTitleMain()
                cs.metaFile = csxml
            lf = os.listdir(cs.storage)
            for f in lf:
                if f.endswith(settings.METADATA_EXT) and f != cs.metaFile:
                    cu = cs.getContentUnitInstance()
                    xmlp = os.path.join(cs.storage, f)
                    cu.metadata = rmg.getRichMetadata(xmlp)
                    cu.name = cu.metadata.getTitleEpisodeTitle()
                    cu.timestamp = cu.createTime(xmlp)
                    # Find corresponding content, if any
                    (base, e) = os.path.splitext(f)
                    tmp = list()
                    for c in lf:
                        (n, ne) = os.path.splitext(c)
                        if n == base:
                            tmp.append(c)
                    tmp.remove(f)
                    if len(tmp) == 1: # content exists
                        cu.contentFile = tmp[0]
                        (base, e) = os.path.splitext(cu.contentFile)
                        u = os.path.join(settings.TORRENT_DIR, base + '.url')
                        t = os.path.join(settings.TORRENT_DIR, base + '.tstream')
                        if os.path.exists(u):
                            cu.torrent = base + '.url'
                        elif os.path.exists(t):
                            cu.torrent = base + '.tstream'
                        if cu.torrent:
                            cu.cskeyfile = cu.findCSFile()
                    cu.identifier = cu.identify()
                    cs.timesort.fill((cu.timestamp, cu.identifier))
                    cu.feedStore = cs.storage
                    cu.metaFile = f
                    cu.stored = True
                    cu.acquire = cs.acquire
                    if settings.XML_EXPORT:
                        # Backward compatibility
                        cs.exportShadow()
                        cu.shadow = cu.getShadow()
                    if cu.identifier != None:
                        cs.items[cu.identifier] = cu
            return cs
        return None

    def storeAttributes(self):
        if self.storage != None:
            if os.path.isdir(self.storage):
                if self.storeAttr:
                    out = ""
                    for a in self.storeAttr:
                        try:
                            if getattr(self, a):
                                v = getattr(self, a)
                                if isinstance(v, basestring):
                                    out += a + " = " + getattr(self, a) + "\n"
                                elif isinstance(v, int):
                                    if a == 'window' and v < 0:
                                        continue
                                    out += a + " = " + str(getattr(self, a)) + "\n"
                                else:
                                    _log.debug("Unsuitable attribute named '%s' for storring in a properties file for content source named '%s'", a, self.name)
                        except Exception, e:
                            _log.debug("Failed to get content source instance attribute '%s' with an error '%s'", a, e)
                    pfpath = os.path.join(self.storage, settings.CONTENT_SOURCE_PROPERTIES)
                    pf = open(pfpath, 'w')
                    out = out.encode('utf-8')
                    pf.write(out)
                    pf.close()
                    _log.debug("Properties for content source with name '%s' stored", self.name)
            else:
                _log.debug("Content source with name '%s' properties cannot be stored since storage in path %s is no a directory", self.name, self.storage)
        else:
            _log.debug("Content source with name '%s' properties cannot be stored since storage is None", self.name)

    def restoreAttributes(self):
        if self.storage != None:
            if os.path.isdir(self.storage):
                pfpath = os.path.join(self.storage, settings.CONTENT_SOURCE_PROPERTIES)
                if os.path.exists(pfpath):
                    pf = open(pfpath, 'r')
                    for line in pf:
                        a = None
                        v = None
                        t = line.split(" = ")
                        if len(t) == 2:
                            (a, v) = line.split(" = ")
                            a = a.strip()
                            v = v.strip()
                        elif len(t) > 2: 
                                a = t[0].strip()
                                v = ""
                                for i in range(1,len(t)-1):
                                    v += t[i]
                                v = v.strip()
                        else:
                            _log.debug("Malformed line '%s' in feed named '%s' properties file", line, self.name)
                        if a in self.storeAttr:
                            if a == "contentUnitClassInstance":
                                c = classImport(classpath, v)
                                if c != None:
                                    setattr(self, a, c.__class__.__name__)
                                    setattr(self, "cuci", c)
                            else:
                                if a and v:
                                    setattr(self, a, v)
                else:
                    _log.debug("No content source with name '%s' properties file in path %s", self.name, pfpath)
            else:
                _log.debug("Content source with name '%s' properties cannot be restored since storage in path %s is no a directory", self.name, self.storage)
        else:
            _log.debug("Content source with name '%s' properties cannot be restored since storage is None", self.name)
                    
    def getContentUnitInstance(self):
        """
        Returns a content unit instance of the same type as specified
        while creating a content source

        @return object Returns a content unit instance as specified
                       while creating the content source
        """
        content = None
        try:
            if issubclass(self.cuci.__class__, ContentUnit().__class__):
                content = object.__new__(type(self.cuci))
                content.__init__()
            else:
                raise Exception("ContentUnit instance of class " + self.cuci.__class__.__name__ + " supplied is not a subclass of ContentUnit, reverting to defaults")
        except Exception, e:
            content = ContentUnit()
            self.cuci = content
            self.contentUnitClassInstance = content.__class__.__name__
            _log.debug("Exception thrown while getting content unit class instance: %s", e)
        return content
        

    def update(self):
        """
        Update the content source
        """
        raise NotImplementedError()

    def setDIDBase(identifier=None, limor=None, advertisingr=None, 
                   paymentr=None, scalabilityr=None, related=None):
        """
        Sets DID base data that is used in export, common for a feed

        @param identifier Identifier
        @param limor Limo reference
        @param advertisingr Advertising reference
        @param paymentr Payment reference
        @param scalabilitr Scalability reference
        @param related Related identifier
        """
        self.didbase= {"identifier": identifier,
                       "limo": limor,
                       "advertising": advertisingr,
                       "payment": paymentr,
                       "scalability": scalabilityr,
                       "related": relatedr}

    def setDIDBaseFile(self, didbasefile):
        if os.path.exists(didbasefile):
            if os.path.isfile(didbasefile):
                rmg = RichMetadataGenerator.getInstance()
                didrm = rmg.getRichMetadata(didbasefile)
                if didrm != None:
                    if didrm.metadataType == metadata.METADATA_DID_BASE:
                        didbase = {}
                        didbase['identifier'] = didrm.getIdentifier()
                        didbase['related'] = didrm.getRelatedIdentifier()
                        didbase['limo'] = didrm.getLimoReference()
                        didbase['payment'] = didrm.getPaymentReference()
                        didbase['advertising'] = didrm.getAdvertisementReference()
                        didbase['scalability'] = didrm.getScalabilityReference()
                        self.didbase = didbase
                    else:
                        _log.debug("Failed to get DID base metadata from specified file '%s', metadata type %s is not DID base", didbasefile, didrm.formatType)
                else:
                    _log.debug("Failed to get DID base metadata from specified file '%s'", didbasefile)
            else:
                _log.debug("Specified DID base argument '%s' is not a file, failed to set didbase attribute", didbasefile)
        else:
            _log.debug("Specified DID base file '%s' does not exists, failed to set didbase attribute", didbasefile)

    def exportTorrent(self, tracker, common=False, 
                      path=settings.TORRENT_DIR, **kwargs):
        """
        Exports content sorce content and metadata as torrents

        @param tracker Sets the torrents tracker 
        @param common Common reference to content (live stream)
        @param path Path to directory where to store the torrent files
        """
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
                _log.debug("Torrent directory created in path '%s'", path)
            except Exception, e:
                _log.error("Failed to make directory for torrent storage in path %s, exception was raised: %s", path, str(e))
                return

    def exportShadow(self, path=settings.SHADOW_DIR):
        """
        Exports content source items in a shadow dir as xml files
        containing a link to a torrent as MediaUri. The shadow is
        placed in the path. The content source directory under the
        source name will hold the XML represenations of the content.

        @param path Sets the shadow dir
        """
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
                _log.debug("Shadow directory created in path '%s'", path)
            except Exception, e:
                _log.error("Failed to make directory for shadow storage in path %s, exception was raised: %s", path, str(e))
        self.shadow = os.path.join(path, textify(self.name))
        if not os.path.isdir(self.shadow):
            try:
                os.mkdir(self.shadow)
                _log.debug("Shadow directory for the content source '%s' created in path '%s'", self.name, self.shadow)
            except Exception, e:
                _log.error("Failed to make directory for content source shadow storage in path %s, exception was raised: %s", self.shadow, str(e))

    def syncCheck(self):
        """
        Checks if all content units in the feed have torrents
        exported. If not, unexported gets exported.
        """
        raise NotImplementedError()

    def exportFeed(self):
        """
        Exports original feed as P2P-Next feed
        """
        raise NotImplementedError()

    def getExportedFeedLink(self):
        """
        Returns a link as a string where the exported feed can be
        obtained from
        """
        raise NotImplementedError()

    def remove(self):
        for k, v in self.items.items():
            t = v.findTorrentFile()
            if t:
                try:
                    os.remove(os.path.join(settings.TORRENT_DIR, t))
                except Exception, e:
                    _log.error("Exception raised while removing a torrent file %s: %s", t, e)
            else:
                _log.error("Programmable error, content unit with name '%s' has no torrent file", v.name)
        if settings.XML_EXPORT and os.path.isdir(self.shadow):
            try:
                shutil.rmtree(self.shadow)
            except Exception, e:
                _log.error("Exception raised wile removing content source named '%s' shadow '%s': %s", self.name, self.shadow, e )
        if os.path.isdir(self.storage):
            try:
                shutil.rmtree(self.storage)
                _log.debug("Removed content source named '%s' storage in path '%s'", self.name, self.storage)
            except Exception, e:
                _log.error("Exception raised wile removing content source named '%s' storage: %s", self.name, e )
        self.items = {}

    def removeContentUnit(self, identifier):
        """
        Removes content unit in content source by identifier. Removes
        related torrent file, if any.

        @param identifier String identifier of the content unit
        """
        if self.items.get(identifier):
            item = self.items[identifier]
            name = item.name
            ident = item.identifier
            ct = item.timestamp
            if self.storage:
                if item.contentFile:
                    os.remove(os.path.join(self.storage, item.contentFile))
                if item.torrent:
                    os.remove(os.path.join(settings.TORRENT_DIR, item.torrent))
                else:
                    (b, e) = os.path.splitext(item.contentFile)
                    u = os.path.join(settings.TORRENT_DIR, b + '.url')
                    t = os.path.join(settings.TORRENT_DIR, b + '.tstream')
                    if os.path.exists(t):
                        os.remove(t)
                    elif os.path.exists(u):
                        os.remove(u)
                if item.metaFile:
                    os.remove(os.path.join(self.storage, item.metaFile))
                if item.cskeyfile:
                    os.remove(os.path.join(settings.CS_PUBLISH_DIR, item.cskeyfile))
                if settings.XML_EXPORT and item.shadow:
                    os.remove(os.path.join(self.shadow, item.shadow))
                del self.items[identifier]
                self.timesort.remove((ct, identifier))
                _log.debug("Content unit with name '%s' and identifier %s removed from source '%s'", name, ident, self.name)

    def checkWindow(self):
        if self.window: # If None collect
            # recover if restored as string
            if isinstance(self.window, basestring): 
                try:
                    self.window = int(self.window)
                except ValueError:
                    self.window = 0
            l = None
            if self.window == 0: # If 0 keep len(source)
                l = len(self.sourceMeta._items)
            elif self.window > 0: 
                l = self.window
            else: # If negative set to default
                self.window = None
            if l:
                sorteditems = self.timesort.sort() # Descending, identifiers
                for i in sorteditems:
                    _log.debug(self.items[i].name)
                if len(sorteditems) > l:
                    tbr = list()
                    c = 0
                    for i in sorteditems:
                        c += 1
                        if c > l:
                            tbr.append(i)
                    for r in tbr:
                        self.removeContentUnit(r)
        return

    def getItemIdentifier(self, fileName):
        """
        Gets item identifier by a content or torrent file name

        @param string Name of the content or torrent file 
        @return list A list of identifiers of the content units, if
                     there is no match an empty list is returned.
        """
        ret = []
        for k, v in self.items.items():
            if fileName == v.contentFile or fileName == v.torrent or fileName == v.metaFile:
                ret.append(v.identifier)
        return ret

    def getFresh(self, content=False, meta=False):
        """
        Return a list of fresh content file names or identifiers

        @param boolean Controls if the content names are returned or
                       identifiers, default False (return identifiers)
        @return list A list of identifiers of the fresh content units
                     or a list of content names
        """
        if content:
            ret = []
            for i in self.lastFreshList:
                ret.append(self.items[i].contentFile)
            return ret
        elif meta:
            ret = []
            for i in self.lastFreshList:
                ret.append(self.items[i].metaFile)
            return ret
        return self.lastFreshList

    def listJson(self):
        """
        Provides a short list as a dict, suitable to be exported in
        json format.

        @return dict A dictionary holding the feed list in short format
        """
        l = {}
        for k, v in self.items.items():
            d = {}
            d["content"] = v.contentFile
            d["meta"] = v.metaFile
            d["torrent"] = v.torrent
            if v.cskeyfile:
                d["cskeys"] = v.cskeyfile
            l[k] = d
        return l

    def getJsonExports(self):
        """
        Provides a dict for exporting feed data in json format. To be
        sure that the data is as in exported feed run before
        exportFeed with all the parameters as were originally
        provided.

        @return dict A dictionary holding the feed data
        """
        e = {}
        e["fresh"] = self.getFresh(False, True)
        rmg = RichMetadataGenerator.getInstance()
        # Get raw feed
        feed = self.exportFeed(None, None, False)
        e["feed"] = rmg.prettyPrint(feed.writeString(), 'utf-8')
        e["maps"] = {}
        for k, v in self.items.items():
            cudata = {}
            cudata["content"] = v.contentFile 
            cudata["identifier"] = v.identifier
            cudata["torrent"] = v.torrent
            if v.cskeyfile:
                cudata["cskeys"] = v.cskeyfile
            if v.getId():
                cudata["id"] = v.getId()
            else:
                for i in feed.items:
                    if i["identifier"] == v.identifier:
                        feed._generate_item_id(i)
                        cudata["id"] = i["unique_id"]
                        break
            e["maps"][v.metaFile] = cudata
        return e

    def toString(self):
        """
        For debuging purposes
        """
        ignore = ["storeAttr", "metadata", "imethod", 
                  "items", "cuci", "timesort"]
        out = "Content source: content units: " + str(len(self.items)) + ", "
        for a in self.__dict__:
            if a not in ignore:
                if getattr(self, a):
                    out += a + ": " + unicode(getattr(self, a)) + ", "
        out += "\n   + metadata: "
        if self.metadata != None:
            for a in self.metadata.getAPIMethods():
                if a.startswith("get"):
                    try:
                        f = getattr(self.metadata, a)
                        if f():
                            out += a + ": " + f() + ", "
                    except:
                        pass
        out = out.rstrip(",")
        out += "\n"
        for i, v in self.items.items():
            out += " - " + v.toString()
        return out

class Channel(ContentSource):
    """
    A content source of type channel offering multiple content
    units based on feeds (RSS, ATOM)
    """
    def __init__(self):
        ContentSource.__init__(self)
        self.cstype = settings.CS_TYPE_CHANNEL

    def getContentSource(location, 
                         publish=None, 
                         contentUnitClassInstance=None,
                         exportFeedLink=None,
                         didbasefile=None,
                         window=None):
        cs = Channel()
        # Load from directory
        if os.path.isdir(location):
            return cs.getCSFromDir(location, publish, contentUnitClassInstance, exportFeedLink, didbasefile, window)
        if publish != None:
            cs.publish = publish
        if contentUnitClassInstance != None:
            cs.cuci = contentUnitClassInstance
            cs.contentUnitClassInstance = cs.cuci.__class__.__name__
        if exportFeedLink != None:
            cs.exportFeedLink = exportFeedLink
        if didbasefile != None:
            cs.didbaseFile = os.path.abspath(didbasefile)
            cs.setDIDBaseFile(cs.didbaseFile)
        if window != None:
            cs.window = window
        cs.location = location
        cs.identifier = cs.identify(cs.location)
        cs.sourceMeta = Feed.getMetadata(location)
        cs.name = cs.sourceMeta.title
        cs.metadata = cs.sourceMeta.getRichMetadata()
        cs.image = cs.sourceMeta.image_href
        cs.store()
        if cs.present: # Restore/update source and properties
            storedcs = cs.restore(cs.storage, cs)
            if not storedcs:
                _log.warn("Failed to restore the content source for location '%s' from storage, returning None", location)
                return None
            storedcs.name = cs.name
            storedcs.location = location
            storedcs.metadata = cs.metadata
            storedcs.sourceMeta = cs.sourceMeta
            storedcs.acquire = cs.acquire
            # Allow stored image to prevail
            if storedcs.image == None:
                storedcs.image = cs.sourceMeta.image_href
            # Update only if new publish is defined, otherwise
            # restored
            if publish != None:
                storedcs.publish = cs.publish
            # Update if new cuci is defined, otherwise restore
            if contentUnitClassInstance != None:
                storedcs.cuci = cs.cuci
                storedcs.contentUnitClassInstance = cs.contentUnitClassInstance
            # Update if new exportFeedLink is defined otherwise
            # restore
            if exportFeedLink != None:
                storedcs.exportFeedLink = cs.exportFeedLink
            # Update if new didbasefile is defined, otherwise restore
            if didbasefile != None:
                storedcs.didbaseFile = cs.didbaseFile
                storedcs.didbase = cs.didbase
            # Update if new window is defined, otherwise restore
            if window != None:
                storedcs.window = cs.window
            # Store channel attributes if they differ
            storedcs.store(True)
            cs = storedcs
            _log.debug("Got a content source for location '%s' from storage", cs.location)
        else:
            _log.debug("Create a content source for location: " + cs.location)
        cs.update()
        return cs
    getContentSource = staticmethod(getContentSource)

    def getCSFromDir(self,
                     location, 
                     publish=None, 
                     contentUnitClassInstance=None,
                     exportFeedLink=None,
                     didbasefile=None,
                     window=None):
        cs = Channel()
        if os.path.exists(location) and os.path.isdir(location):
            if os.path.exists(os.path.join(location, settings.CONTENT_SOURCE_PROPERTIES)):
                if location.endswith("/"):
                    location = location.rstrip("/")
                cs.storage = location
            else:
                _log.warn("Directory %s exists but there is no properties file, returning None", location)
                return None
        else:
            _log.warn("Specified location '%s' is not a directory or does not exists, returning None", location)
            return None
        if contentUnitClassInstance != None:
            cs.cuci = contentUnitClassInstance
            cs.contentUnitClassInstance = cs.cuci.__class__.__name__
        if didbasefile != None:
            cs.didbaseFile = os.path.abspath(didbasefile)
            cs.setDIDBaseFile(cs.didbaseFile)
        cs.metaFile = os.path.basename(location) + settings.METADATA_EXT
        if not cs.isStored():
            _log.warn("Trying to load a content source from path %s that does not store a content source", location)
            return None
        storedcs = cs.restore(cs.storage, cs)
        if not storedcs:
            _log.warn("Failed to restore the content source for location '%s' from storage, returning None", location)
            return None
        # Update only if new publish is defined, otherwise
        # restored
        if publish != None:
            storedcs.publish = publish
        # Update if new cuci is defined, otherwise restore
        if contentUnitClassInstance != None:
            storedcs.cuci = cs.cuci
            storedcs.contentUnitClassInstance = cs.contentUnitClassInstance
        # Update if new exportFeedLink is defined otherwise
        # restore
        if exportFeedLink != None:
            storedcs.exportFeedLink = exportFeedLink
        # Update if new didbasefile is defined, otherwise restore
        if didbasefile != None:
            storedcs.didbaseFile = cs.didbaseFile
            storedcs.didbase = cs.didbase
        # Update if new window is defined, otherwise restore
        if window != None:
            storedcs.window = window
        # Store channel attributes if they differ
        storedcs.store(True)
        cs = storedcs
        _log.debug("Got a content source for location '%s' from storage", cs.location)
        cs.checkWindow()
        cs.syncCheck()
        return cs

    def update(self):
        """
        Update the channel. Acquire new content
        """
        if self.sourceMeta == None:
            if self.location != None:
                self.sourceMeta = Feed.getMetadata(self.location)
            else:
                return 
        self.lastFreshList = []
        # start from teh back of the list so the oldest items get
        # oldest timestamp
        self.sourceMeta._items.reverse()
        for i in self.sourceMeta._items:
            content = self.getContentUnitInstance()
            content.acquire = self.acquire
            content.metadata = i.getRichMetadata(self.metadata)
            content.name = content.metadata.getTitleEpisodeTitle()
            content.image = i.p2p2next_img_src
            # Should be overwritten later
            content.contentFile = i.file
            content.identifier = content.identify()
            if content.identifier in self.items:
                continue
            content.feedStore = self.storage
            content.store(i.link)
            if content.stored:
                content.fresh = True
                self.lastFreshList.append(content.identifier)
                content.timestamp = content.createTime()
                self.timesort.fill((content.timestamp, content.identifier))
                self.items[content.identifier] = content
            else:
                _log.warn("Content unit and metadata related to the item '%s' haven't been stored on the node, content not registred.", content.name)
        self.checkWindow()
        self.syncCheck()
        self.exportShadow()
        self.sourceMeta = None

    def exportTorrent(self, tracker=None, common=False, 
                      path=settings.TORRENT_DIR, **kwargs):
        """
        Creates torrents for all fresh content units. All other
        parameters for the torrent file creation can be specified via
        **kwargs.

        @param tracker The tracker to use to track the torrent
        @param common Common reference to content (live stream)
        @param path A path for torrents export dir
        """
        # Part of the code has been mercilessly taken from createtorrent.py
        # Closed Swarm not supported yet
        super(Channel, self).exportTorrent(common, path)
        config = self.getTorrentConfig(tracker, path, **kwargs)
        # Locks the torrent dir while the torents are created. Looked
        # for by Publisher, but only by common prefix
        lock = settings.TORRENT_DIR_LOCK + "-" + asciify(self.name)
        open(lock, 'a').close()
        if not common:
            for i, v in self.items.items():
                if not v.fresh:
                    continue
                self.createTorrent(v, config)
                v.fresh = False
        os.remove(lock)

    def getTorrentConfig(self, tracker=None, path=settings.TORRENT_DIR, 
                         **kwargs):
        if not tracker:
            tracker = "http://"
            if settings.INTERNAL_TRACKER_IP:
                tracker += settings.INTERNAL_TRACKER_IP
            else:
                tracker += "127.0.0.1" 
            if settings.INTERNAL_TRACKER_PORT:
                tracker += ":" + str(settings.INTERNAL_TRACKER_PORT) + "/" + "announce"
            else:
                tracker += ":7760" + "/" + "announce"
        config = { "destdir": path,
                   "tracker": tracker,
                   "path" : path,
                   "piecesize": 32768,
                   "duration": "1:00:00",
                   "url": False,
                   "url-list": [],
                   "generate_cs": "no"}
        config.update(kwargs)
        return config

    def createTorrent(self, cu, config=None, tracker=None, 
                      path=settings.TORRENT_DIR, **kwargs):
        """
        Creates a torrent file for specified content unit. Allows
        specifying a config dict as an argument or a default is
        provided. The tracker, path and kwargs arguments will be used
        only if the config is not specified.
        """
        if config == None:
            super(Channel, self).exportTorrent(False, path)
            config = self.getTorrentConfig(tracker, path, **kwargs)
        source = os.path.join(self.storage, cu.contentFile)
        if os.path.exists(source) and not os.path.isdir(source):
            tdef = TorrentDef()
            if cu.metadata and cu.metadata.getDuration():
                config['duration'] = cu.metadata.getDuration()
            config['source'] = source
            tdef.add_content(source, playtime=config['duration'])
            tdef.set_tracker(config['tracker'])
            tdef.set_piece_length(config['piecesize'])
            if len(config['url-list']) > 0:
                urllist = [config['url-list']]
                tdef.set_urllist(urllist)
            if config['url']:
                tdef.set_create_merkle_torrent(1)
                tdef.set_url_compat(1)
            else:
                if config.get('thumb'):
                    tdef.set_thumbnail(config['thumb'])
            tdef.set_metadata(cu.buildDIDBaseXMLData())
            # Closed Swarm
            cs_keypair = self.closed_swarm(config, tdef)
            tdef.finalize()            
            (b, e) = os.path.splitext(cu.contentFile)
            publish = None
            if config['url']:
                urlbasename = b + '.url'
                torrent = urlbasename
                urlfilename = os.path.join(config['destdir'],urlbasename)
                f = open(urlfilename,"wb")
                f.write(tdef.get_url())
                f.close()
            else:
                torrentbasename = b + '.tstream'
                torrent = torrentbasename
                torrentfilename = os.path.join(config['destdir'],torrentbasename)
                tdef.save(torrentfilename)                       
            cu.torrent = torrent
            if cs_keypair:
                self.publish_key(torrentfilename, cs_keypair)

    def closed_swarm(self, config, tdef):
        cs_keypair = None
        if config.get('generate_cs').lower() == "yes":
            if config.get('cs_keys'):
                _log.error("Refusing to generate keys when key is given for content unit '%s'", config['source'])
            cs_keypair, cs_pubkey = self.generate_key(config)
            tdef.set_cs_keys([cs_pubkey])
        elif config.get('cs_keys'):
            config['cs_keys'] = config['cs_keys'].split(";")
        return cs_keypair

    def generate_key(self, config):
        """
        Generate and a closed swarm key matching the config.  Source is the 
        source of the torrent
        """
        if 'target' in config and config['target']:
            target = os.path.join(params['target'], split(normpath(file))[1])
        else:
            a, b = os.path.split(config['source'])
            if b == '':
                target = a
            else:
                target = os.path.join(a, b)
        target += ".torrent"
        _log.debug("Generating key to '%s.tkey' and '%s.pub'", target, target)
        keypair, pubkey = ClosedSwarm.generate_cs_keypair(target + ".tkey",
                                                          target + ".pub")
    
        return keypair,pubkey

    def publish_key(self, torrent, keypair, target_directory = settings.CS_PUBLISH_DIR):
        if not os.path.isdir(target_directory):
            try:
                os.mkdir(target_directory)
                _log.debug("ClosedSwarm directory created in path '%s'", target_directory)
            except Exception, e:
                _log.error("Failed to make ClosedSwarm directory in path %s, exception was raised: %s", target_directory, str(e))
                return
        t = TorrentDef.load(torrent)
        filename = encodestring(t.infohash).replace("\n","")
        filename = filename.replace("/","")
        filename = filename.replace("\\","")
        key_file = os.path.join(target_directory, filename + ".tkey")
        ClosedSwarm.save_cs_keypair(keypair, key_file)
        _log.debug("Key saved to: '%s'", key_file)

    def syncCheck(self):
        """
        Checks if all content units in the feed have torrents
        exported. If not, unexported gets exported.
        """
        for i, v in self.items.items():
            if v.contentFile:
                (b, e) = os.path.splitext(v.contentFile)
                u = os.path.join(settings.TORRENT_DIR, b + '.url')
                t = os.path.join(settings.TORRENT_DIR, b + '.tstream')
                if not os.path.exists(u) and not os.path.exists(t):
                    v.fresh = True
        self.exportTorrent()

    def exportFeed(self, guid=None, image=None, export=True):
        if guid != None:
            self.guid = guid
        if self.guid == None:
            self.guid = self.getExportFeedLink()
        if image != None:
            self.image = image
        feed = P2PNextAtomFeed(title=self.name,
                               feed_url=self.getExportFeedLink(),
                               language=self.metadata.getLanguage(),
                               author_name=self.metadata.getPublisher(),
                               feed_guid=self.guid, 
                               image=self.image)
        sitems = self.timesort.sort()
        sitems.reverse()
        for i in sitems:
            v = None
            if self.items.get(i):
                v = self.items[i]
            else:
                _log.debug("Programming error: identifier in sorter that does not exists in source")
                continue
            publish = None
            if v.getPublish(): # Item getPublish has been defined
                if settings.XML_EXPORT:
                    mime_type = "application/xml"
                else:
                    (bd, ed) = os.path.splitext(v.getPublish())
                    ed = ed.lstrip(".")
                    if ed == '': # but has no extension
                        mime_type = 'text/html'
                    elif settings.MIME_TYPES_MAP.get(ed) != None: # mapped
                        mime_type = settings.MIME_TYPES_MAP[ed]
                    else: # not yet defined in map
                        mime_type = "text/plain"
                publish = self.getPublish() + "/" 
                if settings.EXPORT_SHADOW_FEED_NAME:
                    publish += textify(self.name) + "/"
                publish += v.getPublish()
            else: # No getPublish is defined
                publish = self.getPublish()
                mime_type = "text/plain"
            image = None
            if v.getImage() != None:
                image = v.getImage()
                if urlparse(image)[0] == '':
                    image = self.getPublish() + "/" + image
            else:
                image = self.image
            iid = None
            if v.getId() != None:
                iid = v.getId()
            media_uri = self.getPublish() + "/" + settings.EXPORT_TORRENT_LINK + "/" + v.torrent
            media_duration = None
            if v.metadata and v.metadata.getDuration():
                media_duration = v.metadata.getDuration()
                # Backward compatible
                if not media_duration.startswith("P"):
                    media_duration = time2duration(media_duration)
            kwargs = {"identifier": v.identifier}
            feed.add_item(title=v.name, 
                          link=publish, 
                          link_type=mime_type, 
                          unique_id=iid, 
                          description=v.metadata.getSynopsis(), 
                          image=image,
                          broadcast_type='vod',
                          media_uri=media_uri,
                          media_duration=media_duration, 
                          **kwargs)
        # Store if the guid or image has been specified for future use
        if guid != None or image != None:
            self.store(True)
        if export:
            return feed.writeString()
        return feed

    def exportShadow(self, path=settings.SHADOW_DIR):
        if settings.XML_EXPORT:
            super(Channel, self).exportShadow(path)            
            for i, c in self.items.items():
                c.exportShadow(self.shadow)

    def getExportFeedLink(self):
        """
        Returns a link as a string where the exported feed can be
        obtained from
        """
        link = ""
        if self.name != None:
            link = textify(self.name) + settings.METADATA_EXT
        if self.exportFeedLink != None:
            if self.exportFeedLink == settings.EXPORT_FEED_LINK:
                self.exportFeedLink = self.exportFeedLink + "/" + link
            return self.exportFeedLink
        if settings.EXPORT_FEED_LINK != None:
            link = settings.EXPORT_FEED_LINK + "/" + link
        return link


    def getPublish(self):
        if self.publish != None:
            return self.publish
        return settings.CONTENT_PUBLISHING_LINK

