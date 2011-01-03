from xml.etree.cElementTree import Element, SubElement, iterparse, tostring
#from xml.etree.ElementTree import Element, SubElement, iterparse, tostring
from os import path
from threading import RLock
from cStringIO import StringIO

from JSI.RichMetadata.conf import metadata
from JSI.RichMetadata.utils import log

__author__ = 'D. Gabrijelcic (dusan@e5.ijs.si)'
__revision__ = '0.35'
__all__ = ['RichMetadataGenerator', '__revision__']

_log = log.getLog('RichMetadata')
log.setLevel(log.INFO, "RichMetadata")

class RichMetadataGenerator(object):

    __single = None
    __lock = RLock()

    def __init__(self):
        if RichMetadataGenerator.__single:
            raise RuntimeError, "RichMetadataGenerator is Singleton"
        RichMetadataGenerator.__single = self
        self.knownTypes = metadata.BASE_FORMAT_TYPES
        # Learn bases
        self.learnBase = metadata.LEARN_BASE_CORE
        self.learnBaseOptional = metadata.LEARN_BASE_OPTIONAL
        self.master = dict()
        # Tag sets
        self.core = dict()
        self.payment = dict()
        self.advertising = dict()
        self.scalability = dict()
        self.did_base = dict()
        self.did_additional = dict()
        # Mappers
        self.rmTagsMapper = dict()
        self.tagsRmMapper = dict()
        self.__defineAttributes()
        self.learn()

    def getInstance(*args, **kw):
        """
        Get an singelton instance of the {@link RichMetadataGenerator}
        class.
        """
        if RichMetadataGenerator.__single is None:
            RichMetadataGenerator.__lock.acquire()
            try:
                RichMetadataGenerator(*args, **kw)
            finally:
                RichMetadataGenerator.__lock.release()
        return RichMetadataGenerator.__single
    getInstance = staticmethod(getInstance)

    def __defineAttributes(self):
        """
        Defines basic {@link RichMetadata} class attributes according
        to the rich metadata settings. Please note that additional
        attributes are defined through learnig process via {@link
        RichMetadataGenerator.learn} method
        """
        for k, v in metadata.METADATA_SETS.items():
            self.__makeAttributes(v, k)

    def __makeAttributes(self, tagSet, setName):
        ttrma = metadata.HELPER[metadata.TAG_TO_RMA]
        soc = metadata.HELPER[metadata.CAPITAL_SPLIT]
        for t in tagSet:
            _t = ttrma(t)
            d = getattr(self, setName)
            d[_t] = t
            # All
            self.rmTagsMapper[_t] = t
            self.tagsRmMapper[t] = _t
            if _t not in metadata.HUMAN_DESCRIPTION:
                metadata.HUMAN_DESCRIPTION[_t] = soc(t)

    def knownAttributes(self, aType=metadata.METADATA_CORE):
        """
        Return a list of know {@link RichMetadata} attributes as
        defined through learning process.

        @param aType Type of attribute, either core, payment,
        advertising, scalability or all
        @return list 
        """
        if aType in metadata.METADATA_SETS:
            for m in metadata.METADATA_SETS:
                if aType == m:
                    return getattr(self, m).keys()
        elif aType == metadata.METADATA_ALL:
            out = list()
            for m in metadata.METADATA_SETS:
                out = out + self.knownAttributes(m)
            return out
        else:
            _log.warn("Unknown set of attributes %s!", aType)
            return None
        return out

    def getMaster(self, masterType):
        if masterType in self.master:
            return self.master[masterType]
        _log.warn("Unknown master of type: %s", masterType)
        _log.debug("Known masters %s", self.knownMasters())

    def knownMasters(self):
        """
        Returns a list of known masters as created through {@link
        RichMetadadaManager.learn} method.

        @return list
        """
        return self.master.keys()

    def getRichMetadata(self, inputSource=None, metadataType=None):
        """
        RichMetadata factory. 

        @param inputSource The source of the rich metadata. Source can
        be a file or string. If None, empty RichMetadata instance is
        returned of type metadataType
        @param metadataType Defines metadata type if inputSource is
        None. If its value is None an instance of type core metadata is
        returned.
        @return RichMetadata
        """
        rm = RichMetadata()
        rm.core = self.core.copy()
        rm.payment = self.payment.copy()
        rm.advertising = self.advertising.copy()
        rm.scalability = self.scalability.copy()
        rm.did_base = self.did_base.copy()
        rm.did_additional = self.did_additional.copy()
        # Allow updating till the metadata type is known
        rm.update = True
        if inputSource == None:
            if not metadataType:
                metadataType = metadata.METADATA_CORE
            rm.metadataType = metadataType
            rm.api()
            return rm
        else:
            events = ("start", "end")
            get_tag = metadata.HELPER[metadata.GET_TAG]
            get_text = metadata.HELPER[metadata.GET_TEXT]
            formatType = None
            try:
                if not hasattr(inputSource, "read"):
                    if path.isfile(inputSource):
                        inputSource = StringIO(open(inputSource, "r").read())
                    else:
                        inputSource = StringIO(inputSource)
                iterator = iterparse(inputSource, events=events)
            except Exception, e:
                _log.error("Exception thrown while opening the input source, reason: '%s'", str(e))
            try:
                previousElem = None
                eatChildren = False
                toBeEaten = None
                eatStore = None
                lastType = None
                suppressed = False
                supElem = None
                # Needs further simplification. Suppress is subset of
                # collect, multiple items could go into collect as
                # well? VAR_MAPPER needed?
                for event, elem in iterator:
                    tag = "" # Will be overwritten many times during parse
                    if elem.tag != None: # sanitize
                        tag = get_tag(elem.tag)
                        elem.tag = tag
                        elem.text = get_text(elem).strip()
                    if event == "end": # Note logic on end event
#                        print ("%s, %s, %s, %s, %s" % ("--On start: ", event, elem.tag, elem.text, elem.attrib))
                        if suppressed: # Full suppress
                            elem.text = supElem.text
                            elem.attrib.update(supElem.attrib)
                            suppressed = False
#                        print ("%s, %s, %s, %s, %s" % ("++After sup: ",event, elem.tag, elem.text, elem.attrib))
                        # Sigh. Multiple items
                        if eatChildren and toBeEaten != None:
                            if tag != None and tag in toBeEaten:
                                if elem.text != "":
                                    eatStore[tag] = elem.text
                            else:
                                # on closing tag of the parent
                                lead = eatStore.get(toBeEaten[0])
                                if lead != None:
                                    if tag in self.tagsRmMapper:
                                        if isinstance(getattr(rm, self.tagsRmMapper[tag]), dict):
                                            getattr(rm, self.tagsRmMapper[tag]).update({lead: eatStore})
                                        else:
                                            setattr(rm, self.tagsRmMapper[tag], {lead: eatStore})
                                eatChildren = False
                                previousElem = elem
                                continue
                        if tag in metadata.BASE_FORMAT_TYPES:
                            formatType = tag
                        # Rewind forward if suppressed
                        if tag in metadata.TAGS_SUPPRESS:
                            suppressed = True
                            supElem = elem
                            continue
                        # Rewind back if needed
                        if tag in metadata.TAGS_COPY_PRESERVED:
                            tag, elem = self.__restorePreserved(previousElem, elem)
                        # Invoke metadata.HELPER
                        if tag in metadata.HELPER:
                            res = ""
                            helper = metadata.HELPER[tag]
                            if tag == metadata.TAG_STATEMENT: # Ugly but true
                                tag, res = helper(elem, lastType)
                            else:
                                tag, res = helper(elem)
#                            print "Get helper: ", get_tag(elem.tag), tag, res
                            if isinstance(res, str): 
                                elem.text = res
                            elif isinstance(res, list):
                                for k, v in res:
                                    if k != None and k in self.tagsRmMapper:
                                        setattr(rm, self.tagsRmMapper[k], v)
                                tag = "" # Avoid further processing
                        if tag in self.tagsRmMapper:
                            if elem.text != "":
                                setattr(rm, self.tagsRmMapper[tag], elem.text)
                        previousElem = elem
                    if event == "start": # On start event
                        if tag in metadata.RESOLVE_TYPE_TAG: # MPEG_21
                            oldtag, tag = metadata.HELPER[tag](elem)
                            lastType = tag
                        # Learn this as soon as possible
                        if tag in metadata.OPTIONAL_TAGS:
                            setattr(rm, "metadataType", metadata.OPTIONAL_TAGS_MAPPER[tag])
                            rm.update = False
                        if tag in metadata.ITEM_TAGS_MULTIPLE:
                            eatChildren = True
                            _tmp, tupl = metadata.HELPER[tag](tag)
                            toBeEaten = list()
                            for k, v in tupl:
                                toBeEaten.append(k)
                            eatStore = dict()
                if not formatType:
                    raise Exception("Unsupported metadata format type!")
                rm.api()
                return rm
            except Exception, e:
                _log.warn("Failed to create rich metadata, exception thrown, reason: '%s'", str(e))

    def __restorePreserved(self, previous, current):
        """
        Copy/overwrite element/node attributes according to the model
        as defined in the metadata settings
        """
        tag = metadata.HELPER[metadata.GET_TAG](current.tag)
        model = metadata.TAGS_COPY_PRESERVED[tag]
        for k, v in metadata.MH.items():
            setattr(current, k, v(previous, current, model))
        return (tag, current)

    def learn(self):
        """
        Learn basic structure of the XML metadata from the master
        samples provided. Master samples are defined in the metadata
        settings. During the process some {@link RichMetadata} class
        attributes are additionaly defined and added to the attribute
        lists and mappers between XML tags and attributes. Learnig
        provides means to build proper XML document through {@link
        RichMetadaManager.build} method. If something goes wrong
        during the learning proces a warning is passed through the log
        system.

        @return A master of type {@link Master}
        """
        for k, v in self.learnBase.items():
            try:
                _log.debug("Learning for base %s from file %s.", k, v)
                self.master[k] = self.__learn(v, k)
            except Exception, e:
                _log.warn("Exception thrown while base '%s' learning: '%s'", k, str(e))
        for k, v in self.learnBaseOptional.items():
            try:
                _log.debug("Learning for optional base %s from file %s.", k, v)
                self.master[k] = self.__learn(v, k)
            except Exception, e:
                _log.warn("Exception thrown while optional base '%s' learning: '%s'", k, str(e))

    def __learn(self, learnBase, formatType):
        master = Master()
        master.formatType = formatType
        master.metadataType = None
        if formatType in metadata.LEARN_BASE_CORE:
            master.metadataType = metadata.METADATA_CORE
        elif formatType == metadata.TVA_EXT_TAG_PAYMENT or formatType == metadata.MPEG7_EXT_TAG_PAYMENT:
            master.metadataType = metadata.METADATA_PAYMENT
        elif formatType == metadata.TVA_EXT_TAG_ADVERTISING or formatType == metadata.MPEG7_EXT_TAG_ADVERTISING:
            master.metadataType = metadata.METADATA_ADVERTISING
        elif formatType == metadata.TVA_EXT_TAG_SCALABILITY or formatType == metadata.MPEG7_EXT_TAG_SCALABILITY:
            master.metadataType = metadata.METADATA_SCALABILITY
        elif formatType in metadata.MPEG_21_EXT_BASE:
            master.metadataType = metadata.METADATA_DID_BASE
        elif formatType in metadata.MPEG_21_EXT_ADDITIONAL:
            master.metadataType = metadata.METADATA_DID_ADDITIONAL
        else:
            _log.error("Learn: unknown format type '%s', quit!", formatType)
            raise Exception()
        get_tag = metadata.HELPER[metadata.GET_TAG]
        split_tag = metadata.HELPER[metadata.SPLIT_TAG]
        get_text = metadata.HELPER[metadata.GET_TEXT]
        split_attribs  = metadata.HELPER[metadata.SPLIT_ATTRIBS]
        events = ("start", "end", "start-ns")
        ns_map = []
        previousNode = None
        previousItem = None
        skipChildren = False
        getparent = dict()
        level = 0
        for event, elem in iterparse(learnBase, events=events):
            if event == "start":
                node = Node()
                node.level = level 
                node.formatType = master.formatType
                node.namespace, node.tag = split_tag(elem.tag)
                if skipChildren:
                    level += 1
                    if node.level > previousNode.level:
                        continue
                    skipChildren = False
                    level -= 1
                # Sanitize text and check
                if elem.text:
                    text = get_text(elem)
                    if text != "":
                        node.hasText = True
                # Preserve and split attribs
                if len(elem.attrib) > 0:
                    for k, v in split_attribs(elem).items():
                        node.attrib[k] = v
                if node.tag in metadata.TAGS_SUPPRESS:
                    node.suppressed = True
                if node.tag in metadata.AMBIGUOUS_TAGS_HELPERS:
                    node.ambiguous = True
                # Keep text
                if node.formatType in metadata.MPEG_21_EXT_FORMATS:
                    if node.tag == metadata.TAG_TYPE:
                        if get_text(elem) in metadata.MPEG_21_KEEP_TEXT:
                            node.keepText = True
                            node.text = get_text(elem)
                # Vars in text - tagName (in samples, vars) -
                # attribute (RM instance). Get sure that no newlines
                # and spaces are in text
                if get_text(elem).replace("\n", " ").strip().startswith("$"):
                    tagName = get_text(elem).replace("\n", " ").strip().lstrip("$")
                    attribute = tagName.lower() 
                    node.var[attribute] = "text"
                    self.__updateAttributesList(master.metadataType, attribute, tagName, node.tag, True)
                # Vars in attribs
                if len(node.attrib) > 0:
                    for k, v in node.attrib.items():
                        if v.startswith("$"):
                            tagName = v.lstrip("$") 
                            attribute = tagName.lower() 
                            node.var[attribute] = k
                            self.__updateAttributesList(master.metadataType, attribute, tagName, node.tag, True)
                # Invoke HELPER to extend
                if node.tag in metadata.HELPER:
                    helper = metadata.HELPER[node.tag]
                    extendedName, _tmp = helper(node)
                    if extendedName != None:
                        self.__updateAttributesList(master.metadataType, extendedName.lower(), extendedName, node.tag)
                # Lists and items
                if node.tag in metadata.LIST_TAGS :
                    node.isList = True
                if node.tag in metadata.ITEM_TAGS_MULTIPLE:
                    node.multiple = True
                if node.tag in metadata.ITEM_TAGS:
                    if node.itemEqual(previousItem):
                        skipChildren = True
                        level += 1
                        previousNode = node
                        continue
                    node.isItem = True
                    previousItem = node
                # Set current node in the parent list for the level
                getparent[level] = node
                if level == 0:
                    node.empty = False
                    node.parent = Node()
                    node.parent.tag = "root"
                    node.rootNamespace = dict(ns_map)
                    for k,v in node.rootNamespace.items():
                        node.nsMapper[v] = k
                else:
                    node.rootNamespace = getparent[0].namespace
                    node.nsMapper = getparent[0].nsMapper
                    node.parent = getparent[level-1]
                    node.parent.children.append(node)
                level += 1
                previousNode = node
            elif event == "end":
                level = level - 1
            elif event == "start-ns":
                ns_map.append(elem)
        master.root = getparent[0]
        return master

    def __updateAttributesList(self, metadataType, attr, tag, oldtag=None, var=None):
        """
        Update RichMetadata class attributes from elements attribs or
        due to disambiguation. If the oldTag is not None the oldTag
        gets deleted from the dict of RichMetadata attributes.
        """
        soc = metadata.HELPER[metadata.CAPITAL_SPLIT]
        d = getattr(self, metadataType)
        if attr != None:
            d[attr] = tag
            if tag != None:
                self.tagsRmMapper[tag] = attr
                self.rmTagsMapper[attr] = tag
                human = soc(tag[0].capitalize() + tag[1:]).title()
                if not metadata.HUMAN_DESCRIPTION.get(attr):
                    metadata.HUMAN_DESCRIPTION[attr] = human
        # Remove from RichMetadata metadata set dict
        if oldtag != None and oldtag.lower() != attr:
            if d.has_key(oldtag.lower()):
                del d[oldtag.lower()]
        if var:
            # Extend naming space for HELPER - parsing
            metadata.VAR_MAPPER[oldtag + metadata.SEPARATOR + tag] = tag

    def build(self, richMetadata, formatType=metadata.DEFAULT_FORMAT_TYPE):
        """
        Provides XML representation of the {@link RichMetadata}
        instance.

        @param richMetadata {@link RichMetadata} instance 
        @param formatType Target format type. If None the {@link
        RichMetadata} instance default type will be used as defined
        while generating the instance through {@link
        RichMetadataGenerator.getRichMetadata} method.
        @return string
        """
        builder = None
        if formatType == None:
            formatType = metadata.DEFAULT_FORMAT_TYPE
        if richMetadata.metadataType == None:
            richMetadata.metadata.Type = metadata.METADATA_CORE
        if richMetadata.metadataType not in metadata.METADATA_SETS:
            _log.error("Build: unknown metadata type '%s', quit!", richMetadata.metadataType)
            return ""
        if richMetadata.metadataType in metadata.OPTIONAL_META_MAPPER:
            if richMetadata.metadataType in metadata.MPEG_21_TYPES:
                formatType = richMetadata.metadataType
            formatType = formatType + metadata.SEPARATOR + metadata.OPTIONAL_META_MAPPER[richMetadata.metadataType]
        if formatType in self.knownMasters():
            master = self.getMaster(formatType)
            builder = master.root.clone()
            levelMap = None
            levelMap = self.__findMatchingNodes(master.root, richMetadata, builder, levelMap)
            self.__removeDeadBranches(levelMap, builder)
            return builder.build()
        else:
            _log.error("Build: unknown format type: '%s'", formatType)
            return ""

    def __findMatchingNodes(self, nodeFromMaster, richMetadata, builder, levelMap, getparent=None):
        if not levelMap: # Init recurse
            levelMap = {}
            levelMap[0] = [nodeFromMaster]
            levelMap["maxlevel"] = 0
            getparent = {}
            getparent[0] = nodeFromMaster
            #TVA publisher :(on builder since clone)
            if len(builder.var) > 0:
                for k, v in builder.var.items():
                    if getattr(richMetadata, k):
                        builder.attrib[v] = getattr(richMetadata, k)
        previousNode = None
        for child in nodeFromMaster.children:
            skip = False
            clone = child.clone()
            # Provide needed preserved information from previous node
            clone_old = clone.clone()
            if previousNode and child.tag in metadata.TAGS_COPY_PRESERVED:
                _t, clone = self.__restorePreserved(previousNode, clone)
                # We need the previous node
                previousNode.deadBranch = False
            # Remap tags to P2P-Next/TVA understanding
            tag = self.__remap(clone.tag, clone.formatType)
            # Remap to attributes according to tag or
            # learned/specified knowledge
            attribute = None
            if tag in metadata.HELPER: # Map through HELPER
                extendedName, _tmp = metadata.HELPER[tag](clone)
                attribute = self.tagsRmMapper.get(extendedName)
            else: # Maps directly and suppressed tags
                attribute = self.tagsRmMapper.get(tag)
            # Assign attributes to proper nodes
            if attribute and getattr(richMetadata, attribute): # text or dict
                # For both, since skip
                clone.empty = False
                if getattr(richMetadata, attribute):
                    value = getattr(richMetadata, attribute)
                    if isinstance(value, str) or isinstance(value, unicode):
                        # Handles suppressed nodes
                        # Note child, not clone, clone has no children yet
                        for c in child.children: # Normally only one, caution
                            cloneChild = None
                            if c.suppressed:
                                cloneChild = c.clone()
                                cloneChild.deadBranch = False
                                if len(c.children) > 0:
                                    for twice in c.children:
                                        if twice.suppressed:
                                            twiceClone = twice.clone()
                                            twiceClone.deadBranch = False
                                            twiceClone.text = value
                                            cloneChild.children.append(twiceClone)
                                else:
                                    cloneChild.text = value
                                clone.children.append(cloneChild)
                                skip = True
                        if not skip: # No suppressed children
                            clone.text = value
                    elif isinstance(value, dict): # items, only simple, caution
                        for k, v in value.items():
                            newClone = clone.clone()
                            for c in child.children:
                                if c.tag in v: #dict
                                    newChild = c.clone()
                                    newChild.deadBranch = False
                                    newChild.text = v[c.tag]
                                    newClone.children.append(newChild)
                            newClone.parent = getparent[clone.level - 1]
                            builder.children.append(newClone)
                        clone.deadBranch = True # template should be deleted
            # Restore to old attributes and tags
            if child.tag in metadata.TAGS_COPY_PRESERVED:
                for k, v in metadata.MH_RESTORE.items():
                    setattr(clone, k, v(clone_old))
            # Keep text (MPEG21)
            if clone.keepText and metadata.MPEG_21_KEEP_TEXT.get(child.text):
                if metadata.MPEG_21_KEEP_TEXT[child.text](richMetadata):
                    clone.text = child.text
                    clone.empty = False
            # Variables on the end - all attribs plus some text
            if len(clone.var) > 0:
                for k, v in clone.var.items():
                    if getattr(richMetadata, k):
                        clone.empty = False
                        if v == "text":
                            clone.text = getattr(richMetadata, k)
                        else:
                            clone.attrib[v] = getattr(richMetadata, k)
            if clone.empty and len(child.children) == 0:
                clone.deadBranch = True
            clone.parent = getparent[clone.level - 1]
            builder.children.append(clone)
            getparent[clone.level] = clone
            if not levelMap.get(clone.level):
                levelMap[clone.level] = list()
            if clone.level > levelMap["maxlevel"]:
                levelMap["maxlevel"] = clone.level
            levelMap[clone.level].append(clone)
            previousNode = clone
            if not skip: # Problem if not only suppressed
                self.__findMatchingNodes(child, richMetadata, clone, levelMap, getparent)
        return levelMap

    def __remap(self, name, formatType):
        """
        Remap type or attribute name between other name spaces and
        P2P-Next understanding
        """
        if metadata.MAPPER_FT_NS.get(formatType):
            mapper = metadata.MAPPER_FT_NS.get(formatType)
            if name in mapper:
                return mapper[name]
        return name

    def __removeDeadBranches(self, levelMap, builder):
        """
        Removes dead branches in the builder structure.
        """
        # find dead
        dead = {}
        l = levelMap["maxlevel"]
        while l > 0:
            dead[l] = [(child, None) for child in levelMap[l] if self.__dead(child)]
            l -= 1
        for k, v in dead.items():
            dead[k] = dict(v)
        # find empty and remove
        l = levelMap["maxlevel"]
        while l > 0:
            for d in dead[l].keys():
                d.parent.children[:] = [child for child in d.parent.children if not self.__empty(child)]
                if len(d.parent.children) == 0:
                    dead[l-1][d.parent] = None
            l -= 1
        # on the end clean the root
        builder.children[:] = [child for child in builder.children if not self.__empty(child)]

    def __dead(self, child):
        """
        Decides when the child is dead
        """
        if len(child.children) == 0:
            return child.deadBranch
        dead = True
        for c in child.children:
            dead = dead & c.deadBranch
        return dead
            
    def __empty(self, child):
        """
        Decides when the child is empty
        """
        if len(child.children) > 0:
            return False
        return child.empty

    def prettyPrint(self, xml, encoding=None, indent="   ", newl="\n"):
        """
        For debugging purposes
        
        @param xml XML metadata as stirng
        @param encoding XML encoding
        @param indent XML elements indent
        @param newl New line as string
        @return string
        """
        from xml.dom.minidom import parseString
        return parseString(xml).toprettyxml(indent, newl, encoding)

class Master(object):
    """
    Helper class
    """

    def __init__(self):
        self.formatType = None
        self.metadataType = None
        # Holds root node
        self.root = None
        # Stores unsupported tags not recognized through learning
        self.unsupported = {}
        
class Node(object):
    """
    Helper class
    """

    def __init__(self):
        self.level = None
        self.formatType = None
        self.rootNamespace = None
        self.nsMapper = dict()
        self.namespace = None
        self.empty = True
        self.hasText = False
        self.text = None
        self.keepText = False
        self.tag = None
        self.attrib = dict()
        self.ambiguous = False
        self.attribType = None
        self.isList = False
        self.isItem = False
        self.suppressed = False
        self.multiple = False
        self.var = dict()
        self.parent = None
        self.deadBranch = False
        self.children = list()

    def update(self, text=None, attrib = None):
        if text != None:
            self.text = text
        self.attrib.update(attrib)

    def itemEqual(self, itemNode):
        if itemNode == None:
            return False
        if self.tag == itemNode.tag and self.attrib == itemNode.attrib:
            return True
        return False

    def clone(self):
        """
        Clone the node. Children are not copied. Parent should be
        overwritten.
        
        @return Node
        """
        copy = Node()
        copy.level = self.level
        copy.rootNamespace = self.rootNamespace
        copy.formatType = self.formatType
        copy.namespace = self.namespace
        copy.nsMapper = self.nsMapper
        copy.hasText = self.hasText
        copy.text = None
        copy.keepText = self.keepText
        copy.tag = self.tag
        for k, v in self.attrib.items():
            if k in metadata.KEEP_ATTRIBUTES:
                copy.attrib[k] = v
        copy.ambiguous = self.ambiguous
        copy.attribType = self.attribType
        copy.isList = self.isList
        copy.isItem = self.isItem
        copy.suppressed = self.suppressed
        copy.multiple = self.multiple
        copy.var = self.var
        copy.parent = self.parent
        return copy

    def toString(self):
        """
        For debugging purposes

        @return string
        """
        out = ""
        out += '- '*self.level + " +> "
        out += self.tag + ": [" + self.mod(self.hasText, "T") + self.mod(self.empty, "E") + self.mod(self.deadBranch, "D") + self.mod(self.ambiguous, "A") + self.mod(self.attribType, "R") + self.mod(self.isList, "L") + self.mod(self.isItem, "I") + self.mod(self.suppressed, "S") + self.mod(self.multiple, "M") +  self.mod(self.keepText, "K") + self.mod(self.var, "V") + str(len(self.children)) + "] "+ str(self.attrib) + " (up:" + self.parent.tag + ")" + "\n"
        for c in self.children:
            out += c.toString()
        return out

    def mod(self, bol, string):
        if bol:
            return string
        return string.lower()

    def build(self):
        """
        Provides XML representation of the linked nodes. Makes sense
        to call only on the root node.

        @return string
        """
        if self.parent.tag != "root":
            _log.warn("Trying to build from non root node with a tag '%s'", self.tag)
        if self.parent.tag == "root":
            for k,v in self.rootNamespace.items():
                if k == "":
                    self.attrib["xmlns"] = v
                else:
                    self.attrib["xmlns:" + k] = v
            if self.attrib.get(metadata.ATTR_SCHEMA_LOCATION):
                if self.rootNamespace.get("xsi"):
                    self.attrib["xsi:" + metadata.ATTR_SCHEMA_LOCATION] = self.attrib[metadata.ATTR_SCHEMA_LOCATION]
                    del self.attrib[metadata.ATTR_SCHEMA_LOCATION]
        root = Element(self.tag, self.attrib)
        self.__build(self, root)
        return tostring(root)
        

    def __build(self, node, builder):
        for child in node.children:
            if child.namespace != child.rootNamespace:
                if child.nsMapper.get(child.namespace):
                    child.tag = child.nsMapper[child.namespace] + ":" + child.tag
            _sub = SubElement(builder, child.tag, child.attrib)
            if child.hasText:
                _sub.text = child.text
            self.__build(child, _sub)

class RichMetadata(object):

    def __init__(self, api=False):
        self.core = dict()
        self.payment = dict()
        self.advertising = dict()
        self.scalability = dict()
        self.did_base = dict()
        self.did_additional = dict()
        self.method2attrib = dict()
        self.metadataType = metadata.METADATA_CORE
        self.update = False
        if api:
            self.api()
        self.initilized = True

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            return None
            
    def __getitem__(self, key):
      return self.__getattr__(key)
      
    def __setitem__(self, key, val):
      return self.__setattr__(name, val)
      
    def iteritems(self):
      return [(key, self.__dict__[key]) for key in self.keys()]
      
    def __iter__(self):
      return iter(self.iteritems())
      
    def keys(self):
      return [key for key in self.__dict__.keys() if key[:3] not in ['get', 'set']]

    def __setattr__(self, name, value):
        """
        Alows adding only known attributes. Others are ignored and
        warning is passed through the logging system.
        """
        if not self.initilized:
            self.__dict__[name]  = value
        elif self.__dict__.has_key(name):
            self.__dict__[name]  = value
        else:
            if name in getattr(self, self.metadataType) or self.update:
                self.__dict__[name] = value
            else:
                _log.warn("Unknown attribute for metadata of type '%s', not set: '%s', with supplied value '%s'", self.metadataType, name, str(value))
        return self

    def api(self):
        """
        Dynamically generated class API according to the metadata type. 
        """
        self.update = True
        for m in metadata.METADATA_SETS:
            if self.metadataType == m:
                self.__api(getattr(self,m))
        self.update = False

    def __api(self, attribDict):
        instancemethod = type(getattr(self,"__setattr__"))
        for k in attribDict.keys():
            fn = metadata.HUMAN_DESCRIPTION.get(k).replace(" ","")
            if fn != None:
                # Setters
                self.method2attrib["set" + fn] = k
                if k in metadata.ITM_ATTRIBUTES:
                    def s(self, value, name=k):
                        return getattr(self, metadata.ITEM_SET)(value, name)
                    setattr(self, "set" + fn, instancemethod(s, self, self.__class__))
                else:
                    def s(self, value, name=k):
                        return getattr(self, "__setattr__")(name, value.strip())
                    setattr(self, "set" + fn, instancemethod(s, self, self.__class__))
                # 2.5, 2.6, and 3.0 compatibility, same bellow
                try:
                    getattr(self, "set" + fn).__func__.func_name = "set" + fn
                except:
                    getattr(self, "set" + fn).im_func.func_name = "set" + fn
                # Getters
                self.method2attrib["get" + fn] = k
                def g(self, name=k):
                    return getattr(self, "__getattr__")(name)
                setattr(self, "get" + fn, instancemethod(g, self, self.__class__))
                try:
                    getattr(self, "get" + fn).__func__.func_name = "get" + fn
                except:
                    getattr(self, "get" + fn).im_func.func_name = "set" + fn


    def getAPIMethods(self):
        """
        Returns a list of available RichMetadata API methods
        @return list
        """
        methods = self.method2attrib.keys()
        methods.sort()
        return methods

    def setItem(self, string, name):
        split_items = metadata.ITEM_SET_METHODS[metadata.SPLIT_ITEMS]
        split_pairs = metadata.ITEM_SET_METHODS[metadata.SPLIT_PAIRS]
        res =dict()
        for i in split_items(string):
            d = split_pairs(i)
            # lead value is second item in a tuple
            res[d[0][1]] = dict(d)
        setattr(self, name, res)
        return self

    def copy(self, rmeta):
        """
        Copy known metadata from another metadata instance. Other
        instance should be of the same type as this instance otherwise
        no data is copied.

        @param rmeta Other RichMetadata instance
        """
        if self.metadataType != rmeta.metadataType:
            return
        for k in getattr(rmeta, rmeta.metadataType):
            if getattr(rmeta, k) != None:
                setattr(self, k, getattr(rmeta, k))

    def __cmp__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            _log.debug("Metadata instances are of different class, %s != %s", self.__class__.__name__, other.__class__.__name__)
            return -1
        if self.metadataType != other.metadataType:
            _log.debug("Metadata instances are of different type, %s != %s", self.metadataType, other.metadataType)
            return -1
        equal = True
        for k in getattr(self, self.metadataType):
            if getattr(self, k) != getattr(other, k):
                equal = False
                _log.debug("Metadata instances differ in the following attribute - '%s': '%s' != '%s'", k, getattr(self, k), getattr(other, k))
        if equal:
            return 0
        return -1

    def toString(self, humanize=False):
        """
        For debugging purposes. 

        @param humanize Returns human oriented description of the
        defined instance attributes
        @return string
        """
        out = "* RichMetadata class instance\n"
        out += "+ Class attributes:\n"
        out += " "*3 + "Metadata type:   " + str(self.metadataType) + "\n"
        for m in metadata.METADATA_SETS:
            if self.metadataType == m:
                out += "+ " + m.capitalize() + " attributes: " + "\n"
                out += self.__stringify(getattr(self, m), humanize)
        return out

    def __stringify(self, attrSet, humanize):
        out = ""
        attr = attrSet.keys()
        attr.sort()
        for k in attr:
            if k != None and k != "":
                tmp = ""
                try:
                    if humanize:
                        tmp += " "*3 + metadata.HUMAN_DESCRIPTION[k] + ": "
                    else:
                        tmp += " "*3 + k + ": "
                    out += tmp + str(getattr(self, k)) + "\n"
                except:
                    pass
        return out
