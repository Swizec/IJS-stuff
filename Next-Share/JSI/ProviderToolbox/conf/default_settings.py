import logging
from hashlib import sha1
from os.path import sep, dirname, abspath, split

########## IMPORTANT GENERAL SETTINGS/ CHANGE or ADAPT

# The root directory where the media/content will be stored, one
# directory per feed
#MEDIA_ROOT = '/media/external'
MEDIA_ROOT = '/Users/Swizec/Documents/freelancing/IJS-stuff/Next-Share/JSI/feeds/'

# The directory where all torrent files will be stored for the time of
# usage. If the torrent files are to be passed to the user through web
# server, the directory and the content should reside in web server
# accessible part of the file system. The directory should be
# writtable by the user, running the toolbox
EXPORT_TORRENT_DIR = MEDIA_ROOT + sep + "torrents"

# Internal tracker listen port. The port that the tracker listens to.
INTERNAL_TRACKER_PORT = 8082
# Internal tracker IP address. If intended for public change to one of
# the public addresses of your host in question (0.0.0.0 should work
# as well, listen on all interfaces?)
INTERNAL_TRACKER_IP = "193.138.1.106"

# Absolute publishing link for the feeds. The link will appear
# prepended to all your publications in feeds if not defined per feed
# via command line. 
CONTENT_PUBLISHING_LINK = "http://stream.e5.ijs.si/publish"

# Absolute export link for the feed links. This link will be prepend
# to all exported feeds xml files, including discovery feed, if the
# link is not defined per feed via command line.
EXPORT_FEED_LINK = "http://stream.e5.ijs.si/feeds"

# Update interval of the torrent server - how often (in seconds) the
# server checks for new content
UPDATE_INTERVAL = 60

########## GENERAL SETTINGS

# Version
VERSION = "0.2"

# Logging level, see ProviderToolbox.util.log for details
LOG_LEVEL = logging.INFO

# Besides logging to consol log to syslog? Watch for unicode character
# going to the syslog, TODO
LOG_SYSLOG = True 

# Shut up other loggers in the system
SHUT_UP_OTHER_LOGGERS = True

# ProviderToolbox directory
PT_DIR = split(abspath(dirname(__file__)))[0]

# ProviderToolbox python import directory
PT_IMPORT_DIR = split(split(PT_DIR)[0])[0]

########## CONTENT SOURCES SETTINGS

# File to store individual content source properties to
CONTENT_SOURCE_PROPERTIES = ".properties"

# Content sources types; channel, whatever eats feedparser
CS_TYPE_CHANNEL = 'channel'

########## CONTENT SETTINGS

IDENTIFY_PROGRAM = "ffmpeg"
IDENTIFY_PARAM = " -i "
IDENTIFY_COMMAND = None

CONTENT_VOD = "vod"
CONTENT_LIVE = "live"

METADATA_EXT = ".xml"

# Primitive locking mechanism that locks the torrent dir while the
# torrents are being created - used in ContentSource/per feed and in
# Publisher
LOCK = ".alock"
TORRENT_DIR_LOCK = EXPORT_TORRENT_DIR + sep + LOCK

# Feed metadata and assumed mappings to core RichMetadata. Mapping is
# done to core RichMetadata instance attributes. Note mapping to
# titles from feeds to particular items in the feed. Feeds vocabulary
# is based on universal feed parser so direct mapping is possible.
MMM_FEED = {"publisher": "setPublisher",
            "updated": None,
            "id": None,
            "rights": "setOriginator",
            "author": "setPublisher",
            "title": "setTitleMain",
            "subtitle": "setTitleSeriesTitle",
            "language": "setLanguage",
            # Lookup for dict value, key -(.*)
            "image:-href": None,
            "title_detail:-base": None,
            "title_detail:-type": None,
            # Lookup for first dict value in list, key
            # :(.*). Currently only the first list element will be
            # examined
            "links:href": None,
            "links:type": None,
            "links:rel": None,
            "p2pnext_image:-src": None}

# Items in a feed and assumed mappings to core RichMetadata. Mapping
# is done to core RichMetadata instance attributes. Note that some
# feeds carry the metadata and the others not. Feeds vocabulary is
# based on universal feed parser so direct mapping is possible.
MMM_ITEM = {"title": "setTitleEpisodeTitle",
            "subtitle" : "setSynopsis",
            # or
            "summary" : "setSynopsis",
            "id": None,
            "links:href": None,
            "content:base": None,
            "links:type": None,
            "links:rel": None,
            "updated": "setReleaseDate",
            "author": "setPublisher",
            # Atom category, only first one
            "tags:term": None,
            "tags:scheme": None,
            "tags:label": None,
            "media_content:type": None,
            "p2pnext_image:-src": None}

# Live program schedules are slightly different then the feeds as
# addressed above. The difference is a number of parameters that can
# be obtained and some titles are shifted from feed to items. (Note:
# feed subtitle -> program synopsis)

# Live feed
LIVE_MMM_FEED = {"publisher": "setPublisher",
                "updated": "setReleaseDate",
                "link": None,
                "author": "setPublisher",
                "title": "setTitleMain",
                "language": "setLanguage",
                "image:href": None,
                "title:base": None}

# Live item
LIVE_MMM_ITEM = {"title": "setTitleEpisodeTitle",
                 "subtitle": "setTitleSeriesTitle",
                 "synopsis" : "setSynopsis",
                 "id": None,
                 "updated": "setReleaseDate",
                 "author": "setPublisher",
                 "rights": "setOriginator",
                 "media_content:type": None,
                 "content:base": None,
                 "genre": "setGenre",
                 "parential": "setMinimumAge",
                 "scheduled": None,
                 "live_duration": "setDuration"}

    
MEDIA_RM_MAP = {"container": "setFileFormat",
                "duration": "setDuration",
                "start": None,
                "bitrate": "setBitRate",
                "size": "setFileSize"}

STREAM_RM_MAP = {"type": None,
                 "number": None,
                 "audio_coding": "setAudioCoding",
                 "video_coding": "setVideoCoding",
                 "vertical": "setVerticalSize",
                 "horizontal": "setHorizontalSize",
                 "resolution": None,
                 "fps": "setFrameRate",
                 "aspectRatio": "setAspectRatio",
                 "sampleRate": None,
                 "channels": "setNumOfChannels",
                 "bitrate": None}

# Will remove any html from the feeds and items
FEED_REMOVE_CONTENT_HTML = True

MIME_TYPES_MAP = {"3gp": "video/3gpp",
                  "axv": "video/annodex",
                  "dl": "video/dl",
                  "dv": "video/dv",
                  "dif": "video/dv",
                  "fli": "video/fli",
                  "gl": "video/gl",
                  "mp2": "video/mpeg",
                  "mpa": "video/mpeg",
                  "mpe": "video/mpeg",
                  "mpg": "video/mpeg",
                  "mpeg": "video/mpeg",
                  "mpv2": "video/mpeg",
                  "mp4": "video/mp4",
                  "m4v": "video/x-m4v",
                  "mov": "video/quicktime",
                  "qt": "video/quicktime",
                  "ogv": "video/ogg",
                  "mxu": "video/vnd.mpegurl",
                  "flv": "video/x-flv",
                  "lsx": "video/x-la-asf",
                  "lsf": "video/x-la-asf",
                  "mng": "video/x-mng",
                  "asx": "video/x-ms-asf",
                  "asf": "video/x-ms-asf",
                  "asr": "video/x-ms-asf",
                  "wm": "video/x-ms-wm",
                  "wmv": "video/x-ms-wmv",
                  "wmx": "video/x-ms-wmx",
                  "wvx": "video/x-ms-wvx",
                  "avi": "video/x-msvideo",
                  "movie": "video/x-sgi-movie",
                  "mkv": "video/x-matroska",
                  "mpv": "video/x-matroska",
                  "webm":"video/webm",
                  "mpegts":"video/mp2t",
                  # audio
                  "m4a":"audio/x-m4a",
                  "mid":"audio/mid",
                  "rmi":"audio/mid",
                  "mp3":"audio/mpeg",
                  "mpga":"audio/mpeg",
                  "mp2":"audio/mpeg",
                  "mp4a":"audio/mpeg",
                  "aif":"audio/x-aiff",
                  "aifc":"audio/x-aiff",
                  "aiff":"audio/x-aiff",
                  "m3u":"audio/x-mpegurl",
                  "ra":"audio/x-pn-realaudio",
                  "ram":"audio/x-pn-realaudio",
                  "wav":"audio/x-wav",
                  "oga":"audio/ogg",
                  "ogg":"audio/ogg",
                  "spx":"audio/ogg",
                  "gsm":"audio/x-gsm",
                  "ra":"audio/x-pn-realaudio",
                  "rm":"audio/x-pn-realaudio",
                  "ram":"audio/x-pn-realaudio",
                  # image
                  "bmp":"image/bmp",
                  "cod":"image/cis-cod",
                  "gif":"image/gif",
                  "ief":"image/ief",
                  "jpe":"image/jpeg",
                  "jpeg":"image/jpeg",
                  "jpg":"image/jpeg",
                  "jfif":"image/pipeg",
                  "png":"image/png",
                  "svg":"image/svg+xml",
                  "tif":"image/tiff",
                  "tiff":"image/tiff",
                  "ras":"image/x-cmu-raster",
                  "cmx":"image/x-cmx",
                  "ico":"image/x-icon",
                  "pnm":"image/x-portable-anymap",
                  "pbm":"image/x-portable-bitmap",
                  "pgm":"image/x-portable-graymap",
                  "ppm":"image/x-portable-pixmap",
                  "rgb":"image/x-rgb",
                  "xbm":"image/x-xbitmap",
                  "xpm":"image/x-xpixmap",
                  "xwd":"image/x-xwindowdump",
                  # torrent, url?
                  "torrent":"application/x-bittorrent",
                  "tstream":"application/x-bittorrent"}

# Live feeds helpers

LIVE_FEED_PARSER = {"www.rtvslo.si":"RTVSLOLiveFeed",
                    "www.bbc.co.uk":"BBCLiveFeed"}

COLON = ":"
URN = "urn:"
P2P_NEXT = "p2p-next"
URN_ITEM = URN + P2P_NEXT + ":item:"
CATEGORY_SCHEME_ST = "urn:service-type"
CATEGORY_TV = "tv"
CATEGORY_RADIO = "radio"
CATEGORY_DISCOVERY = "discovery"
P2P_NEXT_IMAGE = "http://stream.e5.ijs.si/image/p2p-next-logo.jpg"
RTV_SLO = "rtv-slo" 
RTV_SLO_MMC = RTV_SLO + "-mmc"
RELATED_RTV_SLO_MMC = URN + RTV_SLO_MMC + ":"
PUBLISHER_RTV_SLO_MMC = "MMC RTV Slo"

# Pure men methods to identify items
IDENTIFY = "identify"
IDENTIFY_HELPER = {IDENTIFY: lambda x: sha1(unicode(x).encode('utf-8')).hexdigest(),
                   PUBLISHER_RTV_SLO_MMC: lambda x: IDENTIFY_HELPER[IDENTIFY](x)}

GET_TAG = "gettag"
GET_TEXT = "gettext"
STRIP_NS = "stripns"
SPLIT_ATTRIBS = "splitattribs"
PARSE_HELPER = {GET_TAG: lambda x: x.tag[1:].split("}")[1] if x.tag[0] == "{" else x.tag,
                GET_TEXT: lambda x: x.text.replace("\n", " ").strip() if x.text else "",
                STRIP_NS: lambda x: x[1:].split("}")[1] if x[0] == "{" else x,
                SPLIT_ATTRIBS: lambda x: dict((PARSE_HELPER[STRIP_NS](k), v) for k, v in x.attrib.items()) if x.attrib else {},}


########## TORRENT SERVER SETTINGS

# Server default working directory
TORRENT_SERVER_DEFAULT_DIRECTORY = MEDIA_ROOT + sep + 'torrent_server'

# Leave server a number of seconds to finish its tasks befor exit
SERVER_SLEEP_ON_EXIT = 8

# Torrent store directory
TORRENT_DIRECTORY = EXPORT_TORRENT_DIR

# Torrent server settings
MEGACACHE = True
OVERLAY = True
BUDDYCAST = True
START_RECOMMENDER = False
DOWNLOAD_HELP = True
TORRENT_COLLECTING = True
TORRENT_CHECKING = True 
DIALBACK = False
SOCIAL_NETWORKING = False 
REMOTE_QUERY = False
BARTERCAST = False 
INTERNAL_TRACKER = True
DHT = True
SUPERPEER = False
NAT_DETECT = False
CRAWLER = True
# Needs OVERLAY
PEER_DISCOVERY = False
