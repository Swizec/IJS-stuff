import os
import sys
from optparse import OptionParser, OptionGroup

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator, __revision__
from JSI.RichMetadata.conf import metadata
from JSI.RichMetadata.utils import log

_log = log.getLog('metagen')
log.setLevel(log.ERROR)

class MetaGen(object):

    def __init__(self):
        self.rmm = RichMetadataGenerator.getInstance()
        self.parser = None
        self.options = None
        self.metadataType = None
        self.meta = None
        self.setValue = False

    def run(self):
        """
        Runs the metagen tool and returns generated rich metadata on std out
        """
        if options.payments:
            self.metadataType = metadata.METADATA_PAYMENT
        if options.advertising:
            self.metadataType = metadata.METADATA_ADVERTISING
        if options.scalability:
            self.metadataType = metadata.METADATA_SCALABILITY
        if options.didbase:
            self.metadataType = metadata.METADATA_DID_BASE
            if options.setMetaCore:
                self.options["setMetaCore"] = self.readFile("setMetaCore")
        if options.didadditional:
            self.metadataType = metadata.METADATA_DID_ADDITIONAL
            if options.setMetaAdvertisement:
                self.options["setMetaAdvertisement"] = self.readFile("setMetaAdvertisement")
            if options.setMetaPayment:
                self.options["setMetaPayment"] = self.readFile("setMetaPayment")
            if options.setMetaScalability:
                self.options["setMetaScalability"] = self.readFile("setMetaScalability")
            if options.setCss:
                self.options["setCss"] = self.readFile("setCss")
            if options.setLogo:
                self.options["setLogo"] = self.readFile("setLogo")
            if options.setJavascript:
                self.options["setJavascript"] = self.readFile("setJavascript")
            if options.setHtml:
                self.options["setHtml"] = self.readFile("setHtml")
        self.meta = self.rmm.getRichMetadata(None, self.metadataType)
        if self.options["format"]:
            if self.options["format"] not in metadata.SUPPORTED_ROOT_TAGS:
                self.exitOnInputError()
        counter = 0
        for k, v in self.options.items():
            if v:
               if k in self.meta.method2attrib:
                   _log.debug("function: %s, arg: %s", k, v)
                   f = getattr(self.meta, k)
                   f(v)
                   counter += 1
        if counter == 0:
            _log.warn("No appropriate metadata variables set, quit!")
            self.exitOnInputError()
        _log.debug("\n" + self.meta.toString())
        if options.compact:
            print rmm.build(self.meta, self.options["format"])
        else:
            print rmm.prettyPrint(rmm.build(self.meta, self.options["format"]))

    def readFile(self, option):
        meta = None
        source = self.options[option]
        if os.path.isfile(source):
            f = file(source,"r")
            meta = f.read()
        else:
            _log.error("The option '%s' requires file of XML data as input, no such file '%s'", option, self.options[option])
            self.exitOnInputError()
        return meta

    def exit(self):
        sys.exit(0)

    def exitOnInputError(self):
        self.parser.print_help()
        sys.exit(0)

def uncapitalize(string):
    return string[0].lower() + string[1:]

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Generates P2P-Next compliant metadata according to command parameters.\n  Consult tool help (-h) for more options."

    # Command line options
    rmm = RichMetadataGenerator.getInstance()
    parser = OptionParser(usage, version="%prog 0.1")
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-c", "--compact", help = "Provide compact output suitable for inclusion into a torrent file", action="store_true", dest="compact", default = False)
    parser.add_option("-f", "--format-type", help = "Target XML format (TVAMain or Mpeg7)", action="store", dest="format", default = None)
    parser.add_option("-p", "--payments", help = "Build payments XML metadata", action="store_true", dest="payments", default = False)
    parser.add_option("-a", "--advertising", help = "Build advertising XML metadata", action="store_true", dest="advertising", default = False)
    parser.add_option("-s", "--scalability", help = "Build scalability XML metadata", action="store_true", dest="scalability", default = False)
    parser.add_option("-b", "--did-base", help = "Build MPEG 21 DID base metadata", action="store_true", dest="didbase", default = False)
    parser.add_option("-d", "--did-additional", help = "Build MPEG 21 DID additional metadata", action="store_true", dest="didadditional", default = False)
    haveBeenSeen = dict()
    for m in metadata.METADATA_SETS:
        meta = rmm.getRichMetadata(None, m)
        methods = meta.getAPIMethods()
        methods.sort()
        group = OptionGroup(parser, m.capitalize() + " metadata options")
        addHelp = ""
        plusHelp = ""
        for a in methods:
            if a.startswith("set"):
                if not haveBeenSeen.has_key(a):
                    haveBeenSeen[a] = None
                    astriped = a.lstrip("set")
                    if astriped in metadata.ITEM_SET_HELP:
                        plusHelp = " "  + metadata.ITEM_SET_HELP[astriped]
                    opt = uncapitalize(astriped)
                    human =  metadata.HUMAN_DESCRIPTION.get(meta.method2attrib[a])
                    group.add_option("", "--" + opt, help="Sets '" + human + "' value." + plusHelp, action="store", type="str", dest=a, default = None)
                    plusHelp = ""
                else:
                    addHelp += "--" +  uncapitalize(a.lstrip("set")) + ", "
        if addHelp != "":
            addHelp = addHelp.strip().rstrip(",")
            addHelp = " (Honors the following options as well: " + addHelp + ")"
            group.title = group.title + addHelp
        parser.add_option_group(group)
    (options, args) = parser.parse_args()

    metagen = MetaGen()
    metagen.parser = parser
    metagen.options = options.__dict__
    
    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The metagen has been called with the following options:")
        for k, v in metagen.options.items():
            _log.debug(k + ": " + str(v))

    try:
        metagen.run()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt caught, quit!")
        metagen.exit()
