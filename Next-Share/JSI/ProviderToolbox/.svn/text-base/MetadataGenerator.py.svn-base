from cStringIO import StringIO
import os
import re
import urllib
import urlparse
from xml.etree.cElementTree import iterparse

from JSI.ProviderToolbox.external import feedparser
from JSI.ProviderToolbox.utils import log
from JSI.ProviderToolbox.utils.utilities import asciify, command
from JSI.ProviderToolbox.conf import settings
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator

__author__ = 'D. Gabrijelcic (dusan@e5.ijs.si)'
__revision__ = '0.21'
__all__ = ['Feed', 'Item', 'Media', 'RTVSLOLiveFeed', 'BBCLiveFeed',
           '__revision__'] 

_log = log.getLog('MetadataGeneration')

class MetaGen(object):

    def __init__(self):
        self._mapper = None
        # Ignore while compare
        self._ignore = None
        # Look for meta in items
        self._meta_deep = False
        # Look for rich meta in items
        self._rich_meta_deep = False
        self._rehtml = re.compile(r'<[^<]*?/?>')
        self._recdata = re.compile(r'<!\[CDATA\[(?P<text>[^\]]*)\]\]>')
        self._initialized = True

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        if not self._initialized:
            self.__dict__[name]  = value
            return
        elif settings.FEED_REMOVE_CONTENT_HTML:
            if isinstance(value, str) or isinstance(value, unicode):
                value = value.lstrip()
                if value.startswith("<![CDATA["):
                    value = self._recdata.sub('\g<text>', value)
                value = self._rehtml.sub('', value)
        self.__dict__[name]  = value

    def getMetadata(self, data, identifyMedia=True):
        """
        Get metadata from external source. Should be overwritten by
        inheriting class. Data could be link (url) of the
        feed, universal feedparser data or path to multimedia file.

        @param data
        @return metadata instance
        """
        raise NotImpelmentedError()
    getMetadata = staticmethod(getMetadata)

    def getRichMetadata(self, richmeta=None):
        """
        Get rich metadata based on attributes in inherited
        class. RichMetadata gets assigned according to the mapper of
        the inheriting class instance. Mappers of the inheriting
        classes are defined in settings.

        @param richmeta RichMetadata instance
        @return RichMetadata instance
        """
        assert self._mapper != None
        rmm = RichMetadataGenerator.getInstance()
        rmeta = rmm.getRichMetadata()
        if richmeta != None:
            rmeta.copy(richmeta)
        for a, v in self.__dict__.items():
            if not a.startswith("_"):
                if v != None:
                    if self._mapper.has_key(a) and self._mapper.get(a) != None:
                        try:
                            f = getattr(rmeta, self._mapper[a])
                            if f != None:
                                f(v)
                            else:
                                _log.debug("Getting the method %s has failed, None has been returned.", self._mapper[a])
                        except Exception, e:
                            _log.debug("Setting rich metadata attribute %s whith value %s has failed.", self._mapper[a], v)
        if self._rich_meta_deep:
            try:
                items = getattr(self, "_items")
                if len(items) > 0:
                    for i in items:
                        if i != None:
                            rmeta = i.getRichMetadata(rmeta)
            except:
                pass
        return rmeta

    def __cmp__(self, other):
        """
        Compares two instances of metagen class.

        @param other Other instance of same class
        """
        if self.__class__.__name__ != other.__class__.__name__:
            return -1
        for a in self.__dict__:
            if not a.startswith("_"):
                try:
                    if self._ignore != None:
                        if a in self._ignore:
                            continue
                    if getattr(self, a) != getattr(other, a):
                        _log.debug("Instance of %s attribute differs: %s != %s", self.__class__.__name__, getattr(self, a), getattr(other, a))
                        return -1
                except:
                    _log.debug("Failed to get class %s attribute %s", self.__class__.__name__, a)
                    pass
        try:
            items = getattr(self, "_items")
            if len(items) == len(other._items):
                n = 0
                for i in items:
                    if i != other._items[n]:
                        return -1
                    n += 1
            else:
                return -1
        except:
            pass
        return 0

    def toString(self):
        """
        For debugging purposes.
        """
        out = self.__class__.__name__
        for a, v in self.__dict__.items():
            if not a.startswith("_"):
                if v != None:
                    if isinstance(v, str) or isinstance(v, unicode):
                        out += " +" + a + ": " + v
                    else:
                        out += " +" + a + ": " + str(v)
        out += "\n"
        try:
            items = getattr(self, "_items")
            if len(items) > 0:
                for i in items:
                    if i != None:
                        out += i.toString()
        except:
            pass
        return out

class Feed(MetaGen):

    def __init__(self):
        MetaGen.__init__(self)
        self.publisher = None
        self.updated = None
        self.id = None
        self.rights = None
        self.subtitle = None
        self.language = None
        self.author = None
        self.title = None
        self.subtitle = None
        # A reference to an item image, if any
        self.image_href = None
        self.p2pnext_image_src = None
        # Feed link
        self.links_href = None
        self.links_type = None
        self.links_rel = None
        self.title_detail_base = None
        self.title_detail_type = None
        # Items
        self._items = list()
        self._mapper = settings.MMM_FEED
        self._meta_deep = True

    def getMetadata(data, identifyMedia=True):
        """
        Gets metadata from feed url or data like object with a read
        method. Generates {@link Item} instances if present in the
        feed.

        @param data url or file like object with a read method
        @param identifyMedia identify media as described in the feed items
        @return Feed instance
        """
        mfeed = Feed()
        pf = None
        try:
            pf = feedparser.parse(data)
        except Exception, e:
            _log.error("Failed to read the feed at specified url or data '%s', reason: %s", data, str(e))
            return None
        if pf != None:
            for k in mfeed._mapper.keys():
                split = k.split(":")
                try:
                    v = getattr(pf.feed, split[0])
                    if len(split) > 1:
                        name = k.replace(":", "_")
                        if split[1].startswith("-"):
                            name = name.replace("-", "")
                            setattr(mfeed, name, v[split[1].replace("-", "")])
                        else:
                            setattr(mfeed, name, v[0][split[1]])
                    else:
                        setattr(mfeed, k, v)
                except:
                    pass
            if mfeed._meta_deep:
                for i in pf.entries:
                    mfeed._items.append(Item.getMetadata(i, identifyMedia))
            return mfeed
        else:
            return None
    getMetadata = staticmethod(getMetadata)

class Item(MetaGen):
    
    def __init__(self):
        MetaGen.__init__(self)
        self.title = None
        self.subtitle = None
        # Same interface for feeds (Atom, RSS) and program schedule
        self.summary = self.subtitle
        self.synopsis = self.subtitle
        # Should be unique identifier of the content item, often a
        # link
        self.id = None
        self.updated = None
        self.author = None
        # File name
        self.file = None
        # File extension
        self.extension = None
        # Content type as declared in the feed
        self.media_content_type = None
        # Feed link
        self.content_base = None
        # Item link
        self.links_href = None
        self.links_type = None
        self.links_rel = None
        # Itm link to content
        self.link = None
        self.p2pnext_image_src = None
        # Atom categories
        self.tags_term = None
        self.tags_schema = None
        self.tags_label = None
        # Media
        self._items = list()
        self._mapper = settings.MMM_ITEM
        self._meta_deep = True
        self._rich_meta_deep = True

    def getMetadata(data, identifyMedia=True):
        """
        Gets metadata from universal feedparser entry. In general use
        {@link Feed} instance to get this metadata.

        @param universal feedparser entry         
        @param identifyMedia identify media as described by an item
        @return Item instance
        """
        item = Item()
        for k in item._mapper.keys():
            split = k.split(":") 
            try:
                v = getattr(data, split[0])
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
        if item.links_href != None:
            item.link = item.links_href
        elif item.content_base != None:
            item.link = item.content_base
        else:
            item.link = item.id
        if item.link != None:
            url = urlparse.urlparse(item.link)
            item.file = os.path.basename(url.path)
            item.extension = os.path.splitext(url.path)[1] if os.path.splitext(url.path)[1] != '' else None
            if not identifyMedia:
                item._meta_deep = False
            if item._meta_deep:
                item._items.append(Media.getMetadata(item.link))
        return item
    getMetadata = staticmethod(getMetadata)

class Media(MetaGen):

    def __init__(self):
        MetaGen.__init__(self)
        self.path = None
        self.container = None
        self.duration = None
        self.start = None
        self.bitrate = None
        self.size = None
        # Streams
        self._items = list()
        self._ignore = ["path"]
        self._rich_meta_deep = True
        self._mapper = settings.MEDIA_RM_MAP
        self._ident = settings.IDENTIFY_COMMAND
        if self._ident == None:
            com = command("which " + settings.IDENTIFY_PROGRAM)[0]
            if com != "":
                settings.IDENTIFY_COMMAND = com + settings.IDENTIFY_PARAM
                self._ident = settings.IDENTIFY_COMMAND
                version = com + " -version"
                v = command(version)[0].split("\n")
                ffv = "".join((l for l in v if l.startswith("FFmpeg")))
                _log.debug("Good, ffmpeg version '%s' found in path '%s', settings.IDENTIFY_COMMAND set. Please note that identified media parameters output differs between ffmpeg versions, original version used was 'SVN-r25529'", ffv, com)
            else:
                _log.error("Unable to find suitable program '%s' for identification in system path. Either install program as specified in settings.IDENTIFY_PROGRAM or specify settings.IDENTIFY_COMMAND directly.", settings.IDENTIFY_PROGRAM)

    def getMetadata(path):
        """
        """
        media = Media()
        if not os.path.isfile(path):
            url = urlparse.urlparse(path)
            if url.scheme == "http" or url.scheme == "file": 
                if isinstance(path, unicode):
                    path = asciify(path)
                # See if the url can be opened
                f = None
                try:
                    f = urllib.urlopen(path)
                except Exception, e:
                    if f != None:
                        f.close()
                    _log.error("Cannont open specified url '%s', exception raised: '%s'", path, e)
                    return None
                # For VoD items get size, fails for live
                if f != None:
                    try:
                        media.size = f.info().getfirstmatchingheader('Content-Length')[0].split(":")[1].strip()
                        f.close()
                    except Exception, e:
                        f.close()
            else:
                _log.error("Path specified '%s' is neither a file or reference that could be handled. Quit.", path)
                return None
        else:
            media.size = str(os.path.getsize(path))
        media.path = path
        if media._ident != None:
            # ffmpeg fails, look for std error
            ident = command(media._ident + media.path)[1].split("\n")
            inp = "".join(l for l in ident if l.find("Input") != -1) 
            dur = "".join(l for l in ident if l.find("Duration") != -1)
            stream = "\n".join(l for l in ident if l.find("Stream") != -1)
            # ffmpeg always fails, see if an error has occured
            error = "".join(l for l in ident if l.find("error occurred") != -1 or l.find("Input/output error") != -1)
            if error != "":
                _log.error("Getting media metadata has failed with an ffmpeg error: %s", error)
                return None
            if inp.find(",") != -1:
                media.container = inp.split(",")[1].strip()
            else:
                _log.warn("Getting media metadata has failed with since bad Input line was provided: '%s'", inp) 
                return None
            if dur.find(",") != -1:
                ds = dur.split(",")
                media.duration = ds[0].lstrip("  Duration: ")
                media.start = ds[1].lstrip(" start: ")
                if len(ds) < 3:
                    _log.debug("Too few elements to determine file in path '%s' duration parameters - bitrate!", media.path)
                else:
                    media.bitrate = ds[2].lstrip(" bitrate: ")
            else:
                _log.warn("Getting media metadata has failed with since bad Duration line was provided: '%s'", dur) 
                return None
            for l in stream.split("\n"):
                i = l.split(",")
                # Get Stream instance and set type
                stream = Stream(i[0].split(":")[1].strip().lower())
                stream.number = i[0].split(":")[0].strip().lstrip("Stream #")
                stream.coding = i[0].split(":")[2].strip()
                if stream.type == "video":
                    stream.video_coding = stream.coding
                    if len(i) < 3:
                        _log.debug("Too few elements to determine file in path '%s' video parameters - resolution & aspect ratio!", media.path)
                    else:
                        # Should be resolution
                        if i[2].find("x") != -1:
                            if i[2].find("[") != -1:
                                stream.resolution = i[2][0:i[2].find("[")].strip()
                            else:
                                stream.resolution = i[2].strip()
                            ard = stream.resolution.split("x")
                            if len(ard) == 2:
                                ar = float(ard[0])/float(ard[1])
                                if ar in stream._arMap:
                                    stream.aspectRatio = stream._arMap[ar]
                                else:
                                    stream.aspectRatio = str(ar)
                                stream.horizontal = ard[0]
                                stream.vertical = ard[1]
                    if len(i) < 4:
                        _log.debug("Too few elements to determine file in path '%s' video parameters - fps!", media.path)
                    else:
                        # Could be fps
                        if i[3].find("fps") != -1:
                            stream.fps = i[3][0:i[3].find("fps")].strip()
                        # Or could be tbr
                        if i[3].find("tbr") != -1:
                            stream.fps = i[3][0:i[3].find("tbr")].strip()
                elif stream.type == "audio":
                    stream.audio_coding = stream.coding
                    # sample rate
                    if len(i) < 2:
                        _log.debug("Too few elements to determine all file in path '%s' audio parameters - sample rate!", media.path)
                    else: 
                        stream.sampleRate = i[1].strip()
                    if len(i) < 3:
                        _log.debug("Too few elements to determine all file in path '%s' audio parameters - channels!", media.path)
                    else: 
                        ch = i[2].strip()
                        if stream._chMap.has_key(ch):
                            stream.channels = stream._chMap[ch]
                        else:
                            stream.channels = ch
                    if len(i) < 5:
                        _log.debug("Too few elements to determine all file in path '%s' audio parameters -  bitrate!", media.path)
                    else: 
                        stream.bitrate = i[4].strip()
                elif stream.type == "data":
                    pass # teletext?
                elif stream.type == "subtitle":
                    pass # subtitles
                else:
                    _log.error("Unknown media type: '%s'!", stream.type)
                media._items.append(stream)
            return media
        else:
            _log.error("Media identification failed since instance command attribute is None.")
            return None
    getMetadata = staticmethod(getMetadata)

class Stream(MetaGen):

    def __init__(self, streamType):
        MetaGen.__init__(self)
        self.type = streamType
        self.number = None
        self.coding = None
        self.audio_coding = None
        self.video_coding = None
        # Video
        self.resolution = None
        self.horizontal = None
        self.vertical = None
        self.fps = None
        self.aspectRatio = None
        # Audio
        self.sampleRate = None
        self.channels = None
        self.bitrate = None
        self._arMap = { 16/9.: "16:9",
                       4/3.: "4:3",
                       5/4.: "5:4"}
        self._chMap = { "stereo": "2",
                       "mono": "1"}
        self._mapper = settings.STREAM_RM_MAP

class LiveFeed(Feed):

    def __init__(self):
        Feed.__init__(self)
        self._live = True
        self._mapper = settings.LIVE_MMM_FEED
        self._meta_deep = False

    def identifyMedia(self, path):
        """
        Identifies media at specified url and sets feed instance items
        media information, if any media metadata is available and if
        items are already defined. For particular item media metadata
        use {@link LiveItem} identifyMedia method.

        @param path Path to the live media, usually an url
        """
        if len(self._items) > 0:
            media = Media.getMetadata(path)
            for i in self._items:
                # Shoud be set to None anyway if not defined
                media.duration = i.live_duration
                i._items.append(media)

    def setBitrate(self, rate):
        """
        Certain live media streams bitrate ffmpeg identifies as audio
        bitrate. Sets the bitrate as specified if needed.

        @param rate Stream bitrate
        """
        if len(self._items) > 0:
            for i in self._items:
                # Media
                i._items[0].bitrate = rate
        
class LiveItem(Item):

    def __init__(self):
        Item.__init__(self)
        self._live = True
        # Live feeds only?
        self.rights = None
        self.genre = None
        self.parential = None
        self.scheduled = None
        # In ordinary items duration from Media
        self.live_duration = None
        self._mapper = settings.LIVE_MMM_ITEM
        self._meta_deep = False

    def identifyMedia(self, path):
        """
        Identifies media at specified url and sets item instance media
        information, if any. Getting metadata for each particular item
        can be costly.

        @param path Path to the live media, usually an url
        """
        media = Media.getMetadata(path)
        media.duration = self.live_duration
        self._items.append(media)

    def setBitrate(self, rate):
        """
        Certain live media streams bitrate ffmpeg identifies as audio
        bitrate. Sets the bitrate as specified if needed.

        @param rate Stream bitrate
        """
        i._items[0].bitrate = rate

class RTVSLOLiveFeed(LiveFeed):

    def __init__(self):
        LiveFeed.__init__(self)
        # provide fields not in the feed but known
        self.rights = "Copyright RTV (webmaster@rtvslo.si)"
        self.publisher = "MMC RTV (info@rtvslo.si)"
        self.author = "MMC RTV Slo"
        self.language = "sl"
        
    def getMetadata(data):
        # Poor man RTV schedule xml parser
        mfeed = RTVSLOLiveFeed()
        mfeed.title_detail_base = data
        f = urllib.urlopen(data)
        inputSource = StringIO(f.read())
        events = ("start", "end")
        get_tag = settings.PARSE_HELPER[settings.GET_TAG]
        get_text = settings.PARSE_HELPER[settings.GET_TEXT]
        iterator = iterparse(inputSource, events=events)
        item = None
        for event, elem in iterator:
            if event == "end":
                if elem.tag != None:
#                    print ("%s, %s, %s, %s, %s" % ("--On end: ", event, elem.tag, elem.text, elem.attrib))                    
                    tag = get_tag(elem)
                    text = get_text(elem)
                    if tag == "spored":
                        mfeed._items.append(item)
                        item = None
                    if tag == "program":
                        mfeed.title = text
                    if tag == "stamp":
                        mfeed.updated = text
                    if tag == "naslov":
                        if item != None:
                            item.title = text
                    if tag == "napovednik":
                        if item != None:
                            item.summary = text
                    if tag == "legenda_sifre":
                        if item != None:
                            if text == "ZA_MLADOLETNE_S_STARSI":
                                item.parential = "15"
                    if tag == "ura":
                        if item != None:
                            item.scheduled = text
                    if tag == "dolzina_sec":
                        if item != None:
                            item.live_duration = text
                    if tag == "zvrst":
                        if item != None:
                            item.genre = text
            if event == "start":
                if elem.tag != None:
                    tag = get_tag(elem)
                    if tag == "spored":
                        item = RTVSLOLiveItem()
                        item.updated = mfeed.updated
                        item.content_base = mfeed.title_base
        return mfeed
    getMetadata = staticmethod(getMetadata)

class RTVSLOLiveItem(LiveItem):

    def __init__(self):
        LiveItem.__init__(self)
        self.author = "MMC RTV Slo"

class BBCLiveFeed(LiveFeed):

    def __init__(self):
        LiveFeed.__init__(self)
        # provide fields not in the feed but known, adjust to your own
        # needs
        self.publisher = "BBC"
        self.author = "BBC"
        self.language = "en"
        self._meta_deep = False

    def getMetadata(data):
        # Poor man BBC schedule xml parser
        mfeed = BBCLiveFeed()
        mfeed.title_detail_base = data
        f = urllib.urlopen(data)
        inputSource = StringIO(f.read())
        events = ("start", "end")
        get_tag = settings.PARSE_HELPER[settings.GET_TAG]
        get_text = settings.PARSE_HELPER[settings.GET_TEXT]
        split_attr = settings.PARSE_HELPER[settings.SPLIT_ATTRIBS]
        iterator = iterparse(inputSource, events=events)
        item = None
        branch = {}
        level = 0
        feed_lock = False
        for event, elem in iterator:
            # Note on end event logic
            if event == "end":
                if elem.tag != None:
                    level -= 1
#                    print ("%s, %s, %s, %s, %s" % ("--On end: ", event, elem.tag, elem.text, elem.attrib))                    
                    tag = get_tag(elem)
                    text = get_text(elem)
                    if tag == "broadcast":
                        if item != None:
                            item.updated = mfeed.updated
                            mfeed._items.append(item)
                            item = None
                    if tag == "title":
                        if mfeed.__has_parent(branch, level, "service") and not feed_lock:
                            mfeed.title = text
                            feed_lock = True
                        elif mfeed.__has_parent(branch, level, "display_titles"):
                            if item != None:
                                item.title = text
                        elif mfeed.__has_parent(branch, level, "ownership"):
                            if item != None:
                                # Catches the second ownership related to brand/series
                                item.rights = text
                    if tag == "day":
                        mfeed.updated = split_attr(elem).get("date")
                    if tag == "subtitle":
                        if item != None:
                            item.subtitle = text
                    if tag == "short_synopsis":
                        if item != None:
                            item.summary = text
                    if tag == "duration":
                        if item != None:
                            item.live_duration = text
                    if tag == "start":
                        if item != None:
                            item.start = text
                    if tag == "end":
                        if item != None:
                            item.end = text
            # Note on start event logic
            if event == "start":
                if elem.tag != None:
                    tag = get_tag(elem)
                    # On every broadcast tag generate a new item
                    if tag == "broadcast":
                        item = BBCLiveItem()
                        item.content_base = mfeed.title_base
                    branch[level] = tag
                    level += 1
        return mfeed
    getMetadata = staticmethod(getMetadata)

    def __has_parent(self, branch, level, tag):
        for i in range(level, -1, -1):
            if branch[i] == tag:
                return True
        return False

class BBCLiveItem(LiveItem):

    def __init__(self):
        LiveItem.__init__(self)
        self.author = "BBC"
        # Data not available in other live feeds, store for future use
        self.start = None
        self.end = None
