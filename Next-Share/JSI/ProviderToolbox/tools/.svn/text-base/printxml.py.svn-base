import os
import sys
from optparse import OptionParser, OptionGroup

from JSI.ProviderToolbox.ContentSource import Channel, ContentUnit, RTVVoDContent
from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils import log

_log = log.getLog('printxml')
log.setLevel(log.DEBUG)

class PrintXml(object):

    def __init__(self):
        self.rmg = RichMetadataGenerator.getInstance()
        self.parser = None
        self.options = None  

    def run(self):
        """
        Runs the printxml tool, and pretty prints the xml content on
        std output
        """
        if options.file != None:
            if os.path.exists(options.file):
                rm = self.rmg.getRichMetadata(options.file)
                if rm != None:
                    print self.rmg.prettyPrint(self.rmg.build(rm), options.encoding)
                else:
                    self.exitOnInputError("The file supplied is not in one of P2P-Next specified XML \n                    formats: " + options.file)
            else:
                self.exitOnInputError("XML file specified does not exists: " + options.file)
        else:
            self.exitOnInputError("Please specify xml file to print")


    def exitOnInputError(self, message=None):
        if message:
            print "\n" + "Reason for failure: " + message + "\n"
        self.parser.print_help()
        sys.exit(0)

if __name__ == "__main__":

    usage = "usage: %prog [options]\n\n  Pretty prints xml file content on std output."

    # Command line options
    parser = OptionParser(usage, version="%prog v" + settings.VERSION)
    parser.add_option("-v", "--verbose", help = "Be verbose", action="store_true", dest="verbose", default = False)
    parser.add_option("-f", "--file", help = "File to print", action="store", dest="file", default = None)
    parser.add_option("-e", "--encoding", help = "Encoding of the printed output, default utf-8", action="store", dest="encoding", default = 'utf-8')
    (options, args) = parser.parse_args()

    printxml = PrintXml()
    printxml.parser = parser
    printxml.options = options.__dict__
    
    if options.verbose:
        # Set appropriate log level
        log.setLevel(log.DEBUG)
        _log.debug("The printxml has been called with the following options:")
        for k, v in printxml.options.items():
            _log.debug(k + ": " + str(v))

    try:
        printxml.run()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt caught, quit!")
        printxml.exit()
