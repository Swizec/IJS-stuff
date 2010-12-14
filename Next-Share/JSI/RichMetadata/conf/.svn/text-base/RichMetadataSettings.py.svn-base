from re import findall
from os.path import sep

# Base P2P-Next metadata definitions

VERSION = "0.61"

# Root tags
TAG_MPEG7 = "Mpeg7"
TAG_TVA_MAIN = "TVAMain"
TAG_PO_EPISODE = "Episode"

# Supported root tags
SUPPORTED_ROOT_TAGS = [TAG_TVA_MAIN,
                       TAG_MPEG7]

# Common tags/attributes
TAG_TITLE = "Title"
TAG_GENRE = "Genre"
TAG_PARENTAL_GUIDANCE = "ParentalGuidance"
TAG_MINIMUM_AGE = "MinimumAge"
TAG_LANGUAGE = "Language"
TAG_CAPTION_LANGUAGE = "CaptionLanguage"
TAG_SIGN_LANGUAGE = "SignLanguage"
TAG_IS_INTERACTIVE_CONTENT = "IsInteractiveContent"
TAG_IS_COMMERCIAL_CONTENT = "IsCommercialContent"
TAG_CONTAINS_COMMERCIAL_CONTENT = "ContainsCommercialContent"
TAG_P2P_DATA = "P2PData"
TAG_TORRENT = "Torrent"
TAG_P2P_FRAGMENT = "P2PFragment"
TAG_FILE_FORMAT = "FileFormat"
TAG_FILE_SIZE = "FileSize"
TAG_BIT_RATE = "BitRate"
ATTR_PROGRAM_ID = "programId"
ATTR_PUBLISHER = "publisher"

# TVA tags
TAG_PROGRAM_INFORMATION = "ProgramInformation"
TAG_SYNOPSIS = "Synopsis"
TAG_RELATED_MATERIAL = "RelatedMaterial"
TAG_HOW_RELATED = "HowRelated"
TAG_PRODUCTION_DATE = "ProductionDate"
TAG_PRODUCTION_LOCATION = "ProductionLocation"
TAG_RELEASE_INFORMATION = "ReleaseInformation"
TAG_RELEASE_DATE = "ReleaseDate"
TAG_DURATION = "Duration"
TAG_ORIGINATOR = "Originator"
TAG_IS_LIVE = "IsLive"
TAG_CODING = "Coding"
TAG_HORIZONTAL_SIZE = "HorizontalSize"
TAG_VERTICAL_SIZE = "VerticalSize"
TAG_ASPECT_RATIO = "AspectRatio"
TAG_FRAME_RATE = "FrameRate"
TAG_NUM_OF_CHANNELS = "NumOfChannels"
TAG_RELEASE_DATE = "ReleaseDate"

# Optional TVA tags
TAG_ADVERTISING = "AdvertisingData"
TAG_TVA_PAYMENT = "PurchaseItem"
TAG_SCALABILITY = "ScalabilityData"

# P2P-Next extended tags

# Payments
TAG_PRICE = "Price"
TAG_PAYMENT_ID = "PaymentId"
TAG_ACCEPT_DONATIONS = "AcceptDonations"
TAG_ADVANCED_INFOS = "AdvancedInfos"
TAG_PAYMENT_RECIPIENT = "PaymentRecipient"
ATTR_CURRENCY = "currency"

# Advertising
TAG_BUSINESS_MODEL = "BusinessModel"
TAG_LIVE_CONTENT = "IsLiveContent"
TAG_ALLOW_ADVERTISING = "AllowAdvertising"
TAG_CIRCULAR_CONTENT = "CircularContent"
TAG_AD_TYPE = "AdType"
TAG_STREAMING_TYPE = "StreamingType"
TAG_AD_FORMAT = "AdFormat"
TAG_AGE = "Age"
TAG_GENDER = "Gender"
TAG_COUNTRY = "Country"

# Scalability
TAG_CONSTRAINT = "Constraint"
TAG_ADAPTATION_OPERATOR = "AdaptationOperator"
TAG_UTILITY = "Utility"
TAG_SPS = "SPS"
TAG_PPS = "PPS"
TAG_WIDTH = "width"
TAG_HEIGHT = "height"
TAG_VALUE = "value"
TAG_SPS_ID = "spsId"

# Mpeg7
TAG_ABSTRACT = "Abstract"
TAG_LOCATION = "Location"
TAG_DATE = "Date"
TAG_ENTITY_IDENTIFIER = "EntityIdentifier"
TAG_FRAME = "Frame"
TAG_MEDIA_DURATION = "MediaDuration"
TAG_AUDIO_CHANNELS = "AudioChannels"
TAG_MPEG7_PAYMENT = "PaymentData"
TAG_MEDIA_INFORMATION = "MediaInformation"
TAG_ENTITY_INFORMATION = "EntityInformation"

# Uriplay
TAG_PO_EPISODE = "Episode"
TAG_DC_TITLE = "title"
TAG_DC_DESCRIPTION = "description"
TAG_PO_POSITION = "position"
TAG_PLAY_SEASON_POSITION = "seasonPosition"
TAG_DCTERMS_RIGHTS_HOLDER = "rightsHolder"
TAG_PLAY_IMAGE = "image"
TAG_PO_GENRE = "genre"
TAG_DCTERMS_SPATIAL = "spatial"
TAG_PLAY_AUDIO_LANGUAGE = "audioLanguage"
TAG_PLAY_CAPTION_LANGUAGE = "captionLanguage"
TAG_PO_SUBTITLE_LANGUAGE = "subtitle_language"
TAG_PLAY_CONTAINS_ADVERTISING = "containsAdvertising"
TAG_PLAY_GUIDANCE = "guidance"
TAG_PO_DURATION = "duration"
TAG_PLAY_ENCODING = "Encoding"
TAG_PLAY_RESTRICTED_BY = "restrictedBy"
TAG_PLAY_URI = "uri"
TAG_PLAY_PROVIDER = "provider"
TAG_PLAY_ORIGINATOR = "originator"
TAG_PLAY_TRANSPORT_IS_LIVE = "transportIsLive"
TAG_DCTERMS_DATE_SUBMITTED = "dateSubmitted"
TAG_DCTERMS_CREATED = "created"
TAG_PLAY_SEASON_TITLE = "seasonTitle"

# MPEG-21
MPEG_21 = "DIDL"
MPEG_21_BASE = "did_base"
MPEG_21_ADDITIONAL = "did_additional"
MPEG_21_TYPES = [MPEG_21_BASE,
                 MPEG_21_ADDITIONAL]
TAG_IDENTIFIER = "Identifier"
TAG_RELATED_IDENTIFIER = "RelatedIdentifier"
TAG_RESOURCE = "Resource"
TAG_COMPONENT = "Component"
TAG_INCLUDE = "include"
TAG_TYPE = "Type"
TAG_STATEMENT = "Statement"
TAG_DESCRIPTOR = "Descriptor"
TAG_ITEM = "Item"
TAG_MPEG_21_BASE = "urn:p2p-next:type:item:2009"
TAG_MPEG_21_ADDITIONAL = "urn:p2p-next:type:item:additional:2009"

BASE_FORMAT_TYPES = [TAG_MPEG7,
                     TAG_TVA_MAIN, 
                     TAG_PO_EPISODE,
                     MPEG_21]

OPTIONAL_TAGS = [TAG_ADVERTISING,
                 TAG_TVA_PAYMENT,
                 TAG_SCALABILITY,
                 TAG_MPEG7_PAYMENT,
                 TAG_MPEG_21_BASE,
                 TAG_MPEG_21_ADDITIONAL]

# Commented tags are not present in the samples but can be present in
# the specification
TAGS_COMMON = [TAG_TITLE,
               TAG_GENRE,
               TAG_MINIMUM_AGE,
               TAG_LANGUAGE,
               TAG_CAPTION_LANGUAGE,
               TAG_SIGN_LANGUAGE,
#               TAG_IS_INTERACTIVE_CONTENT,
#               TAG_IS_COMMERCIAL_CONTENT,
#               TAG_CONTAINS_COMMERCIAL_CONTENT,
#               TAG_P2P_DATA,
#               TAG_TORRENT,
#               TAG_P2P_FRAGMENT,
               TAG_FILE_FORMAT,
               TAG_FILE_SIZE,
               TAG_BIT_RATE,
               ATTR_PUBLISHER,
               TAG_PROGRAM_INFORMATION]

TAGS_TVA = [TAG_SYNOPSIS,
            TAG_RELATED_MATERIAL,
            TAG_HOW_RELATED,
            TAG_PRODUCTION_DATE,
            TAG_PRODUCTION_LOCATION,
            TAG_RELEASE_INFORMATION,
            TAG_RELEASE_DATE,
            TAG_DURATION,
            TAG_ORIGINATOR,
 #           TAG_IS_LIVE,
            TAG_CODING,
            TAG_HORIZONTAL_SIZE,
            TAG_VERTICAL_SIZE,
            TAG_ASPECT_RATIO,
            TAG_FRAME_RATE,
            TAG_NUM_OF_CHANNELS,
            TAG_RELEASE_DATE]

################# P2P-Next extensions

ADVERTISING_TAGS = [TAG_BUSINESS_MODEL,
                    TAG_LIVE_CONTENT,
                    TAG_ALLOW_ADVERTISING,
                    TAG_CIRCULAR_CONTENT,
                    TAG_AD_TYPE,
                    TAG_STREAMING_TYPE,
                    TAG_AD_FORMAT,
                    TAG_AGE,
                    TAG_GENDER,
                    TAG_COUNTRY,
                    TAG_ASPECT_RATIO,
                    TAG_FRAME_RATE,
                    TAG_HORIZONTAL_SIZE,
                    TAG_VERTICAL_SIZE]

PAYMENT_TAGS =  [TAG_PRICE,
                 TAG_PAYMENT_ID,
                 TAG_ACCEPT_DONATIONS,
                 TAG_ADVANCED_INFOS,
                 TAG_PAYMENT_RECIPIENT,
                 ATTR_CURRENCY]

SCALABILITY_TAGS = [TAG_CONSTRAINT,
                    TAG_ADAPTATION_OPERATOR,
                    TAG_UTILITY,
                    TAG_SPS,
                    TAG_PPS]


P2P_NEXT_TAGS_CORE = TAGS_COMMON + TAGS_TVA
P2P_NEXT_TAGS_EXTENDED = ADVERTISING_TAGS + PAYMENT_TAGS 
#+ SCALABILITY_TAGS
P2P_NEXT_ALL_TAGS = P2P_NEXT_TAGS_CORE + P2P_NEXT_TAGS_EXTENDED

TAGS_URIPLAY = [TAG_DC_TITLE,
                TAG_DC_DESCRIPTION,
                TAG_PLAY_SEASON_TITLE,
                TAG_PLAY_SEASON_POSITION,
                TAG_DCTERMS_RIGHTS_HOLDER,
                TAG_PLAY_IMAGE,
                TAG_PO_GENRE,
                TAG_DCTERMS_SPATIAL,
                TAG_PLAY_AUDIO_LANGUAGE,
                TAG_PLAY_CAPTION_LANGUAGE,
                TAG_PO_SUBTITLE_LANGUAGE,
                TAG_PLAY_CONTAINS_ADVERTISING,
                TAG_PO_DURATION,
                TAG_PLAY_ENCODING,
                TAG_PLAY_RESTRICTED_BY,
                TAG_PLAY_URI,
                TAG_PLAY_PROVIDER,
                TAG_PLAY_ORIGINATOR,
                TAG_PLAY_TRANSPORT_IS_LIVE,
                TAG_DCTERMS_DATE_SUBMITTED,
                TAG_DCTERMS_CREATED]

TAGS_MPEG_21 = []

############################ Learning, parsing and building definitions

DEFAULT_FORMAT_TYPE = TAG_TVA_MAIN
DEFAULT_PUBLISHER = "P2P-Next"

# Define the naming and values for the following sets
METADATA_CORE = "core"
METADATA_PAYMENT = "payment"
METADATA_ADVERTISING = "advertising"
METADATA_SCALABILITY = "scalability"
METADATA_DID_BASE = "did_base"
METADATA_DID_ADDITIONAL = "did_additional"
METADATA_ALL = "all"
METADATA_SETS = {METADATA_CORE: P2P_NEXT_TAGS_CORE,
                 METADATA_PAYMENT: PAYMENT_TAGS,
                 METADATA_ADVERTISING: ADVERTISING_TAGS,
                 METADATA_SCALABILITY: SCALABILITY_TAGS,
                 METADATA_DID_BASE: TAGS_MPEG_21,
                 METADATA_DID_ADDITIONAL: TAGS_MPEG_21}

############################ Learning

# Learn the structure from the following samples
ME_DIR = "JSI/RichMetadata/conf"
SEP = sep
LEARN_BASE_CORE = {TAG_MPEG7: ME_DIR + SEP + "p2p-next_mpeg7_v" + VERSION + ".xml",
                   TAG_TVA_MAIN: ME_DIR + SEP + "p2p-next_tva_v" + VERSION + ".xml"}
#                   TAG_PO_EPISODE: ME_DIR + SEP + "p2p-next_uriplay_v" + VERSION + ".xml"}

P2P_NEXT_OPTIONAL_METADATA_TYPE = "p2pnext:P2POptionalDescriptionType"
OPTIONAL_METADATA_TYPES = [TAG_TVA_MAIN,
                           TAG_MPEG7]
SEPARATOR = "_"
TVA_EXT_TAG_ADVERTISING = TAG_TVA_MAIN + SEPARATOR + TAG_ADVERTISING
MPEG7_EXT_TAG_ADVERTISING = TAG_MPEG7 + SEPARATOR + TAG_ADVERTISING
TVA_EXT_TAG_PAYMENT = TAG_TVA_MAIN + SEPARATOR + TAG_TVA_PAYMENT
MPEG7_EXT_TAG_PAYMENT = TAG_MPEG7 + SEPARATOR + TAG_TVA_PAYMENT 
TVA_EXT_TAG_SCALABILITY = TAG_TVA_MAIN + SEPARATOR + TAG_SCALABILITY
MPEG7_EXT_TAG_SCALABILITY = TAG_MPEG7 + SEPARATOR + TAG_SCALABILITY
MPEG_21_EXT_BASE = MPEG_21_BASE + SEPARATOR + MPEG_21_BASE
MPEG_21_EXT_ADDITIONAL = MPEG_21_ADDITIONAL + SEPARATOR + MPEG_21_ADDITIONAL

# Optional learn base
LEARN_BASE_OPTIONAL = {TVA_EXT_TAG_ADVERTISING: ME_DIR + SEP + "p2p-next_tva_advertising_v" + VERSION + ".xml",
                       TVA_EXT_TAG_PAYMENT: ME_DIR + SEP + "p2p-next_tva_payment_v" + VERSION + ".xml",
                       TVA_EXT_TAG_SCALABILITY: ME_DIR + SEP + "p2p-next_tva_scalability_v" + VERSION + ".xml",
                       MPEG7_EXT_TAG_ADVERTISING: ME_DIR + SEP + "p2p-next_mpeg7_advertising_v" + VERSION + ".xml",
                       MPEG7_EXT_TAG_PAYMENT: ME_DIR + SEP + "p2p-next_mpeg7_payment_v" + VERSION + ".xml",
                       MPEG7_EXT_TAG_SCALABILITY: ME_DIR + SEP + "p2p-next_mpeg7_scalability_v" + VERSION + ".xml",
                       MPEG_21_EXT_BASE: ME_DIR + SEP + "p2p-next_mpeg-21-base_v" + VERSION + ".xml",
                       MPEG_21_EXT_ADDITIONAL: ME_DIR + SEP + "p2p-next_mpeg-21-additional_v" + VERSION + ".xml"}

MPEG_21_EXT_FORMATS = [MPEG_21_EXT_BASE,
                       MPEG_21_EXT_ADDITIONAL]

############################ Parsing

# General metadata attributes related information
ATTRIB_SEP = SEPARATOR

# Optional tags mapper
OPTIONAL_TAGS_MAPPER = {TAG_ADVERTISING: METADATA_ADVERTISING,
                        TAG_TVA_PAYMENT: METADATA_PAYMENT,
                        TAG_MPEG7_PAYMENT: METADATA_PAYMENT,
                        TAG_SCALABILITY: METADATA_SCALABILITY,
                        TAG_MPEG_21_BASE: METADATA_DID_BASE,
                        TAG_MPEG_21_ADDITIONAL: METADATA_DID_ADDITIONAL}

# Can help resolve the type of metadata
RESOLVE_TYPE_TAG = [TAG_TYPE]

# This could be done smarter but there is no guarantee that the
# payment tag will map to TVA as used in LEARN_BASE_OPTIONAL and thus
# in known models
OPTIONAL_META_MAPPER = {METADATA_ADVERTISING: TAG_ADVERTISING,
                        METADATA_PAYMENT: TAG_TVA_PAYMENT,
                        METADATA_SCALABILITY: TAG_SCALABILITY,
                        METADATA_DID_BASE: MPEG_21_BASE,
                        METADATA_DID_ADDITIONAL: MPEG_21_ADDITIONAL}

# Suppressed tags
TAG_NAME = "Name"
TAG_TIME_POINT = "TimePoint"
TAG_DAY_AND_YEAR = "DayAndYear"
TAG_AGENT = "Agent"
TAG_ROLE = "Role"
TAG_FREE_TEXT_ANNOTATION = "FreeTextAnnotation"
TAG_VECTOR = "Vector"
TAG_VALUES = "Values"

# While parsing the following tags will be suppressed with the parent
# and their attributes 
TAGS_SUPPRESS = [TAG_NAME,
                 TAG_TIME_POINT,
                 TAG_DAY_AND_YEAR,
                 TAG_FREE_TEXT_ANNOTATION,
                 TAG_VECTOR,
                 TAG_VALUES,
                 TAG_RESOURCE,
                 TAG_COMPONENT]

# Some of nasty tags information needs to be preserved while parsing
# so it can be reused later. Preservation model relates to next tag
# and model ([tag, text, attrib])
TAGS_COPY_PRESERVED = {TAG_AGENT: [False, False, True]}

# Model helper: x - previous, y - current, z - model 
MH = {"tag": lambda x,y,z: x.tag if z[0] else y.tag,
      "text": lambda x,y,z: x.text if z[1] else y.text,
      "attrib": lambda x,y,z: dict(y.attrib.items() + x.attrib.items()) if z[2] else y.attrib}

# Model restore helper: x - original
MH_RESTORE = {"tag": lambda x: x.tag,
              "attrib": lambda x: x.attrib}

# Ignore if attrib and text, sigh
IGNORE_ATTRIB_AND_TEXT = [TAG_ENTITY_IDENTIFIER]

# Disambiguate the Coding tag (TVA and Mpeg7)
AUDIO_CODING_FORMAT = "urn:mpeg:mpeg7:cs:AudioCodingFormatCS:2001"
TAG_AUDIO_CODING = "Audio" + ATTRIB_SEP + TAG_CODING
TAG_VIDEO_CODING = "Video" + ATTRIB_SEP + TAG_CODING

# Disambiguate the Role/Agent tag (Mpeg7)
ROLE_PRODUCER = "urn:mpeg:mpeg7:cs:RoleCS:2001:PRODUCER"
TAG_PRODUCER = "Producer"
TAG_DISSEMINATOR = "Disseminator"

# Disambiguate the Format tag (Mpeg7)
TAG_FORMAT = "Format"

# Collects the tags that can be ambiguous, like Coding, resoved
# through HELPER (TVA, Mpeg7). If tag is listed here and is in
# P2P-Next set, an extended RichMetadata class attributes will be
# defined during learning.
AMBIGUOUS_TAGS_HELPERS = [TAG_CODING,
                          TAG_FORMAT,
                          TAG_AGENT]

# Attributes (RM class) from attributes (element) (TVA and Mpeg7). The
# elements with the tags specified in the dict below should not carry
# other information in the element text. 
ATTR_HEIGHT = "height"
ATTR_WIDTH = "width"
ATTR_ASPECT_RATIO = "aspectRatio"
ATTR_RATE = "rate"
ATTR_XPOINTER = "xpointer"
ATTR_MIME_TYPE = "mimeType"
ATTR_HREF = "href"
ATTR_REF = "ref"
ATTR_ID = "id"
ATTR_TYPE = "type"
ATTR_SCHEMA_LOCATION = "schemaLocation"
ATTR_OPREF = "iOPinRef"
ATTR_RELATION_TYPE = "relationshipType"
ATTR_ORGANIZATION = "organization"
ATTRIBUTES_FROM_ATTRIB = {}

# The attributes will be copied from master to every metadata item
# created
KEEP_ATTRIBUTES = [ATTR_TYPE,
                   ATTR_HREF,
                   ATTR_SCHEMA_LOCATION,
                   ATTR_OPREF,
                   ATTR_XPOINTER,
                   ATTR_MIME_TYPE,
                   ATTR_RELATION_TYPE]

################# Lists and items. 
#List can contain multiple items or other tags as well

TAG_MODULE = "Module"
LIST_TAGS = [TAG_SCALABILITY,
             TAG_MODULE]
ITEM_TAGS_RESOLVABLE = [TAG_CONSTRAINT,
                        TAG_ADAPTATION_OPERATOR,
                        TAG_UTILITY]
ITEM_TAGS_MULTIPLE = [TAG_SPS,
                      TAG_PPS]
ITEM_TAGS = ITEM_TAGS_RESOLVABLE + ITEM_TAGS_MULTIPLE

ITEMS_SEP = ":"
PAIRS_SEP = ","
EQUAL = "="
SPLIT = "split"
DICT = "dictsplit"
SPLIT_ITEMS = "itemssplit"
SPLIT_PAIRS = "pairssplit"
PAIRS = "tuplepairs"
ASSIGN = "assign"
ITEM_SET_METHODS = {SPLIT: lambda x,y: [s for s in x.split(y)] if x.__contains__(y) else [x],
                    ASSIGN: lambda x,y=EQUAL: x.split(EQUAL) if x.__contains__(y) else (x, None),
                    PAIRS: lambda x,y: [ITEM_SET_METHODS[ASSIGN](k) for k in x.split(y)] if x.__contains__(y) else [(x, None)],
                    DICT: lambda x,y: dict(ITEM_SET_METHODS[PAIRS](x,y)),
                    SPLIT_ITEMS: lambda x,y=ITEMS_SEP: ITEM_SET_METHODS[SPLIT](x,y), 
                    SPLIT_PAIRS: lambda x,y=PAIRS_SEP: ITEM_SET_METHODS[PAIRS](x,y)}

################ MPEG-21 

# Statement text
MPEG_21_METADATA_CORE = "urn:p2p-next:type:rm:core:2009"
MPEG_21_METADATA_ITEM = "urn:p2p-next:type:item:2009"
MPEG_21_METADATA_ADDITIONAL = "urn:p2p-next:type:item:additional:2009"
MPEG_21_METADATA_PAYMENT = "urn:p2p-next:type:rm:payment:2009"
MPEG_21_METADATA_ADVERTISEMENT = "urn:p2p-next:type:rm:advertisement:2009"
MPEG_21_METADATA_SCALABILITY = "urn:p2p-next:type:rm:scalability:2009"
MPEG_21_METADATA_LIMO = "urn:p2p-next:type:limo:2009"
MPEG_21_METADATA_CONTENT = "urn:p2p-next:type:content:2009"

# Variables in samples
VAR_CORE = "MetaCore"
VAR_PAYMENT = "MetaPayment"
VAR_ADVERTISEMENT = "MetaAdvertisement"
VAR_SCALABILITY = "MetaScalability"
VAR_LIMO = "MetaLimo"
VAR_CONTENT = "MetaContent"
VAR_PAYMENT_REFERENCE = "PaymentReference"
VAR_ADVERTISEMENT_REFERENCE = "AdvertisementReference"
VAR_SCALABILITY_REFERENCE = "ScalabilityReference"
VAR_LIMO_REFERENCE = "LimoReference"
VAR_CONTENT_REFERENCE = "ContentReference"
VAR_CONTENT_TYPE = "ContentType"
VAR_JAVASCRIPT = "javascript"
VAR_CSS = "css"
VAR_HTML = "html"
VAR_LOGO = "logo"
VAR_JAVASCRIPT_NAME = "JavascriptName"
VAR_CSS_NAME = "CSSName"
VAR_LOGO_NAME = "LogoName"
VAR_LOGO_TYPE = "LogoType"
VAR_LOGO_REF = "LogoReference"
# Needed?
VAR_CURRENCY = "Currency"
VAR_PROGRAM_ID = "ProgramId"
VAR_PUBLISHER = "Publisher"
VAR_HEIGHT = "HorizontalSize"
VAR_WIDTH = "VerticalSize"
VAR_ASPECT_RATIO = "AspectRatio"
VAR_RATE = "FrameRate"
VAR_MEDIA_INFORMATION = "MediaInformation"

# Keep certain text in MPEG-21, according to condition as specified -
# used only in build - x - RichMetadata instance. Conditions are build
# from vars which lower value should match directly to instance
# attributes
MPEG_21_KEEP_TEXT = {MPEG_21_METADATA_CORE: lambda x: True,
                     MPEG_21_METADATA_ITEM: lambda x: True,
                     MPEG_21_METADATA_ADDITIONAL: lambda x: True,
                     MPEG_21_METADATA_PAYMENT: lambda x: True if getattr(x, VAR_PAYMENT.lower()) else False,
                     MPEG_21_METADATA_ADVERTISEMENT: lambda x: True if getattr(x, VAR_ADVERTISEMENT.lower()) else False,
                     MPEG_21_METADATA_SCALABILITY: lambda x: True if getattr(x, VAR_SCALABILITY.lower()) else False,
                     MPEG_21_METADATA_LIMO: lambda x: True if getattr(x, VAR_LIMO.lower()) else False,
                     MPEG_21_METADATA_CONTENT: lambda x: True if getattr(x, VAR_CONTENT.lower()) or getattr(x, "resource_ref") or getattr(x, "resource_mimetype") else False}

# Include xpointer to var mapper
INCLUDE_MAP = {"rm.payment": VAR_PAYMENT_REFERENCE,
               "rm.advertisement": VAR_ADVERTISEMENT_REFERENCE,
               "rm.scalability": VAR_SCALABILITY_REFERENCE,
               "limo": VAR_LIMO_REFERENCE}

# Map mime types to various items in suppressed descriptor tag
ID_MAP = {"text/javascript": [VAR_JAVASCRIPT, VAR_JAVASCRIPT_NAME, None, None],
          "text/css": [VAR_CSS, VAR_CSS_NAME, None, None],
          "image": [VAR_LOGO, VAR_LOGO_NAME, VAR_LOGO_TYPE, VAR_LOGO_REF]}

# Resource mime type to var mapper
RESOURCE_MAP = {"text/javascript": VAR_JAVASCRIPT,
                "text/css": VAR_CSS,
                "image": VAR_LOGO}

# Map statements according to type in previous descriptor
STATEMENT_MAP = {MPEG_21_METADATA_CORE: VAR_CORE,
                 MPEG_21_METADATA_PAYMENT: VAR_PAYMENT,
                 MPEG_21_METADATA_ADVERTISEMENT: VAR_ADVERTISEMENT,
                 MPEG_21_METADATA_SCALABILITY: VAR_SCALABILITY}

# Vars mapper, filled during learning. Holds extended names and maps
# directly to RM instance attributes. Used in HELPER while parsing.
VAR_MAPPER = {}

# Helper related definitions
SPLIT_ATTRIBS = "splitattribs"
GET_TAG = "gettag"
SPLIT_TAG = "splittag"
GET_TEXT = "gettext"
TAG_SUPPRESS = "suppress"
TAG_FULL_SUPPRESS = "fullsuppress"
TAG_TO_RMA = "tagtormatrib"
CAPITAL_SPLIT = "splitoncapitals"
RM_TO_API = "rmtoapi"
TAG_AMBIGUOUS = "ambiguous"
TARGET_NAME = "targetname"
TAG_FROM_ATTRIB = "tagfromattrib"
TAG_FROM_VAR = "tagfromvar"
ATTRIB_TYPE_INTEGER_VECTOR = "IntegerVectorType"
EXT_VAR_NAME = "extvarname"
EXT_VAR_NAME_TAG = "2extvarname"
MPROV = "mimeprovide"
DVN = "descriptorvarname"

# Mighty helper. A nice example how the Python code and lambdas can
# easily become obfuscated. But on the other hand this dict helps keep
# a number of lines of code used to implement the parser in
# RichMetadata.py low and thus understandable. Helper is used in build
# method as well for generation of consistent names of the RichMetadata
# instance attributes. All tag related lambdas in the helper should
# return a tuple of ([extended]tag, result). If the tag provides more
# attributes, the result in the tuple is a list of tuples with same
# structure as original. Often the lambdas are written as follows:
# lambda x: (,[(,),(,),...]) if condition else (,). Some lambdas of
# this type return None for a value of the tag - in this case we don't
# want to register original type as RichMetadata instance attribute.
HELPER = {
    ################ General ################
    GET_TAG: lambda x: x[1:].split("}")[1] if x[0] == "{" else x,
    SPLIT_TAG: lambda x: x[1:].split("}") if x[0] == "{" else x,
    SPLIT_ATTRIBS: lambda x: dict((HELPER[GET_TAG](k), v) for k, v in x.attrib.items()) if x.attrib else {},
    GET_TEXT: lambda x: x.text if x != None and x.text != None and not x.text.isspace() else "",
    # x-child, y-parent 
    TAG_SUPPRESS: lambda x,y: (y.tag,HELPER[GET_TEXT](x)),
    TAG_TO_RMA: lambda x: x.lower(),
    # target name for attributes from attribs
    TAG_FROM_ATTRIB: lambda x,y: HELPER[GET_TAG](x.tag).__add__(ATTRIB_SEP).__add__(x.attrib[y]) if x.attrib.get(y) else HELPER[GET_TAG](x.tag),
    TARGET_NAME: lambda x,y: HELPER[GET_TAG](x.tag).lower().__add__(ATTRIB_SEP).__add__(y.lower()) if y else HELPER[GET_TAG](x.tag).lower(),
    # Humanize tags
    CAPITAL_SPLIT: lambda x: " ".join(findall('[A-Z][^A-Z]*', x)).replace("_"," ") if not x.islower() else x.capitalize(),
    # Ambiguous - elem, return either tag 1 or 2, condition attrib href 
    TAG_AMBIGUOUS: lambda x,y,z,w: (y, None) if x.attrib.get(ATTR_HREF) == w else (z, None),
    # Text and attrib variables - map directly to RM instance attribs
    # x - element, y - var as specified in samples (without $)
    EXT_VAR_NAME: lambda x,y: VAR_MAPPER.get(HELPER[GET_TAG](x.tag).__add__(SEPARATOR).__add__(y)) if y else None,
    # Can specify tag directly, use for suppressed (tag descriptor)
    EXT_VAR_NAME_TAG: lambda x,y: VAR_MAPPER.get(x.__add__(SEPARATOR).__add__(y)) if y else None,
    ################ TVA ################
    TAG_PROGRAM_INFORMATION: lambda x: (HELPER[EXT_VAR_NAME](x, VAR_PROGRAM_ID), x.attrib[ATTR_PROGRAM_ID]) if x.attrib.get(ATTR_PROGRAM_ID) else (None, "ojoj"),
    # Get the producer from the tag attributes, thus list
    TAG_TVA_MAIN: lambda x: (ATTR_PUBLISHER, x.attrib[ATTR_PUBLISHER]) if x.attrib.get(ATTR_PUBLISHER) else (None, None),
    TAG_CODING: lambda x: HELPER[TAG_AMBIGUOUS](x, TAG_AUDIO_CODING, TAG_VIDEO_CODING, AUDIO_CODING_FORMAT),
    # Order in tuple matters when deleting old tag in learning
    TAG_PRICE: lambda x: (x.tag, [(ATTR_CURRENCY, x.attrib[ATTR_CURRENCY]), (TAG_PRICE, HELPER[GET_TEXT](x))]) if x.attrib.get(ATTR_CURRENCY) else (TAG_PRICE, HELPER[GET_TEXT](x)),
    TAG_TITLE: lambda x: (HELPER[TAG_FROM_ATTRIB](x, ATTR_TYPE), HELPER[GET_TEXT](x)),
    ################ MPEG7 ################
    TAG_ABSTRACT: lambda x: (MAPPER_MPEG7_P2P_NEXT[TAG_ABSTRACT], None),#suppress
    TAG_LOCATION: lambda x: (MAPPER_MPEG7_P2P_NEXT[TAG_LOCATION], None),#suppress
    TAG_DATE: lambda x: (MAPPER_MPEG7_P2P_NEXT[TAG_DATE], None),#suppress
    TAG_ENTITY_IDENTIFIER: lambda x: (x.tag, [(HELPER[EXT_VAR_NAME](x,VAR_PROGRAM_ID), HELPER[GET_TEXT](x)), (HELPER[EXT_VAR_NAME](x, VAR_PUBLISHER), x.attrib[ATTR_ORGANIZATION])]) if x.attrib.get(ATTR_ORGANIZATION) else (VAR_PROGRAM_ID, HELPER[GET_TEXT](x)),
    TAG_AGENT: lambda x: HELPER[TAG_AMBIGUOUS](x, MAPPER_MPEG7_P2P_NEXT[TAG_PRODUCER], MAPPER_MPEG7_P2P_NEXT[TAG_DISSEMINATOR], ROLE_PRODUCER),
    TAG_FORMAT: lambda x: HELPER[TAG_CODING](x),
    TAG_MEDIA_DURATION: lambda x: (MAPPER_MPEG7_P2P_NEXT[TAG_MEDIA_DURATION], x.text),
    TAG_AUDIO_CHANNELS: lambda x:(MAPPER_MPEG7_P2P_NEXT[TAG_AUDIO_CHANNELS], x.text),
    # Keys are Mpeg7 height, with, ... needs to be mapped to get the name
    TAG_FRAME: lambda x: (None, [(MAPPER_MPEG7_P2P_NEXT.get(k), v) for k, v in x.attrib.items()]) if x.attrib else (None, None),
    TAG_MEDIA_INFORMATION: lambda x: (TAG_MEDIA_INFORMATION, x.attrib[ATTR_ID]) if x.attrib.get(ATTR_ID) else (None, None),
    ################ Scalability ################
    TAG_CONSTRAINT: lambda x: (HELPER[TAG_FROM_ATTRIB](x, ATTR_OPREF), x.text),
    TAG_ADAPTATION_OPERATOR: lambda x: (HELPER[TAG_FROM_ATTRIB](x, ATTR_OPREF), x.text),
    TAG_UTILITY: lambda x: (HELPER[TAG_FROM_ATTRIB](x, ATTR_OPREF), x.text),
    # Note: childLead is always the first key in the template
    TAG_SPS: lambda x: (TAG_SPS, [(TAG_SPS_ID, None), (TAG_WIDTH, None), (TAG_HEIGHT, None), (TAG_VALUE, None)]),
    TAG_PPS: lambda x: (TAG_PPS, [(TAG_SPS_ID, None), (TAG_VALUE, None)]),
    ################ DID BASE ################
    TAG_IDENTIFIER: lambda x: (TAG_IDENTIFIER, HELPER[GET_TEXT](x)),
    TAG_RELATED_IDENTIFIER: lambda x: (TAG_RELATED_IDENTIFIER, HELPER[GET_TEXT](x)),
    # Map according to last descriptor type - parser is responsible to
    # call the method with last type seen
    TAG_STATEMENT: lambda x,y=None: (HELPER[EXT_VAR_NAME](x, STATEMENT_MAP[y]), HELPER[GET_TEXT](x)) if HELPER[GET_TEXT](x) != "" and STATEMENT_MAP.get(y) else (None, None),
    TAG_INCLUDE: lambda x: (HELPER[EXT_VAR_NAME](x, INCLUDE_MAP.get(x.attrib.get(ATTR_XPOINTER))) , x.attrib.get(ATTR_HREF)) if x.attrib.get(ATTR_XPOINTER) and x.attrib.get(ATTR_HREF) else (None, None),
    ###### Tag descriptor suppressed with resource and component
    #+ MPROV - provides key in ID_MAP, in case of image/... only image
    MPROV: lambda x: x.attrib.get(ATTR_MIME_TYPE).split("/")[0] if  x.attrib.get(ATTR_MIME_TYPE) and x.attrib.get(ATTR_MIME_TYPE).startswith("image") else x.attrib.get(ATTR_MIME_TYPE),
    #+ DVN - maps to the element of the list in ID_MAP
    DVN: lambda x,y: ID_MAP.get(HELPER[MPROV](x))[y] if HELPER[MPROV](x) and ID_MAP.get(HELPER[MPROV](x)) else None,
    # Descriptor is extended, TAG_RESOURCE AND TAG_COMPONENT info are
    # available when helper is invoked (suppressed). 
    TAG_DESCRIPTOR: lambda x: (None, [(HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,HELPER[DVN](x,0)), HELPER[GET_TEXT](x)), (HELPER[EXT_VAR_NAME_TAG](TAG_DESCRIPTOR,HELPER[DVN](x,1)),x.attrib.get(ATTR_ID)), (HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,HELPER[DVN](x,2)),x.attrib.get(ATTR_MIME_TYPE)), (HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,HELPER[DVN](x,3)),x.attrib.get(ATTR_REF))]) if HELPER[GET_TEXT](x) != "" else (None, None),
    # Since suppress $html and TAG_RESOURCE wo content is stuck in last item
    TAG_ITEM: lambda x: (HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,VAR_HTML),HELPER[GET_TEXT](x)) if x.attrib.get(ATTR_MIME_TYPE) and x.attrib.get(ATTR_MIME_TYPE) == "text/html" else (None,[(HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,VAR_CONTENT_REFERENCE),x.attrib.get(ATTR_REF)),(HELPER[EXT_VAR_NAME_TAG](TAG_RESOURCE,VAR_CONTENT_TYPE),x.attrib.get(ATTR_MIME_TYPE))]) if x.attrib.get(ATTR_REF) else (None,None),
    # Learn type of DID, return None since we don't need type
    TAG_TYPE: lambda x: (None, HELPER[GET_TEXT](x))
}

# List of RM class attributes from ITEM_TAGS_MULTIPLE and suitable
# method in RM class
ITM_ATTRIBUTES = [ HELPER[TAG_TO_RMA](x) for x in ITEM_TAGS_MULTIPLE]
ITEM_SET = "setItem"
ITEM_SET_HELP = { TAG_PPS: "Sets PPS value as a string: spsId=1,value=xyz:...",
                  TAG_SPS: "Sets SPS value as a string: spsId=1,width=a,height=b,value=cde:..."}


# Mapper between name space MPEG7 to P2P-Next (assumed)
MAPPER_MPEG7_P2P_NEXT = {TAG_ABSTRACT: TAG_SYNOPSIS,
                         TAG_LOCATION: TAG_PRODUCTION_LOCATION,
                         TAG_DATE: TAG_PRODUCTION_DATE,
                         TAG_ENTITY_IDENTIFIER: ATTR_PROGRAM_ID,
                         TAG_PRODUCER: TAG_ORIGINATOR,
                         TAG_DISSEMINATOR: ATTR_PUBLISHER,
                         TAG_MEDIA_DURATION: TAG_DURATION,
                         ATTR_HEIGHT: TAG_VERTICAL_SIZE,
                         ATTR_WIDTH: TAG_HORIZONTAL_SIZE,
                         ATTR_ASPECT_RATIO: TAG_ASPECT_RATIO,
                         ATTR_RATE: TAG_FRAME_RATE,
                         TAG_AUDIO_CHANNELS: TAG_NUM_OF_CHANNELS}

# Mapper between format types and name spaces mappers
MAPPER_FT_NS = {TAG_TVA_MAIN: {},
                TAG_MPEG7: MAPPER_MPEG7_P2P_NEXT,
                TVA_EXT_TAG_ADVERTISING: {},
                TVA_EXT_TAG_PAYMENT: {},
                TVA_EXT_TAG_SCALABILITY: {},
                MPEG7_EXT_TAG_ADVERTISING: MAPPER_MPEG7_P2P_NEXT,
                MPEG7_EXT_TAG_PAYMENT: MAPPER_MPEG7_P2P_NEXT,
                MPEG7_EXT_TAG_SCALABILITY: MAPPER_MPEG7_P2P_NEXT,
                MPEG_21_EXT_BASE: {}}

# Defines human description of the RichMetadata class attributes.
# Filled while learning. Here are defined only the ones that simple re
# (CAPITAL_SPLIT) in helper doesn't convert properly.
HUMAN_DESCRIPTION = {HELPER[TAG_TO_RMA](TAG_P2P_FRAGMENT): "P2P Fragment",
                     HELPER[TAG_TO_RMA](TAG_P2P_DATA): "P2P Data",
                     HELPER[TAG_TO_RMA](TAG_PPS): "PPS",
                     HELPER[TAG_TO_RMA](TAG_SPS): "SPS",
                     HELPER[TAG_TO_RMA](TAG_TVA_MAIN): "TVA Main",
                     HELPER[TAG_TO_RMA](VAR_CSS_NAME): "CSS Name"}
