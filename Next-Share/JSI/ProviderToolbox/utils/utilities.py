import os
import cPickle
from heapq import heappush, heappop
import shlex
import subprocess
import tempfile
import types
import unicodedata
import urllib
from urlparse import urlparse
from hashlib import sha1

import log
from JSI.ProviderToolbox.conf import settings
from JSI.ProviderToolbox.utils.exceptions import Error, FetchError

_log = log.getLog('Utilities')

def asciify(string):
    """
    Convert string to ascii
    """
    if isinstance(string, unicode):
        _tmp = unicodedata.normalize('NFKD', string)
        return _tmp.encode('ascii','ignore')
    return string

def textify(string):
    """
    Convertes input string to a simple text string suitable for a file name
    """
    _tmp = asciify(string)
    # We don't want these characters in the file name
    _tmp = _tmp.replace(' ','_')
    strip = ', # ! : ; < > ~ % & " \' /'.split()
    for s in strip:
        if _tmp.find(s):
            _tmp = _tmp.replace(s, '')
    return _tmp

def toString(class_to_print, header='', omit=None):
    if omit == None: omit = list()
    out = '\n+' + header + ':\n'
    for attr_name in dir(class_to_print):
        attr = getattr(class_to_print, attr_name)
        # Looking only for fields
        if type(attr) != types.MethodType and not attr_name.startswith('__'):
            # Omitted fields and local fields starting with underscore
            # are not printed
            if attr_name not in omit and not attr_name.startswith('_'): 
                if attr != None:
                    out += " " + attr_name + ": " + unicode(attr) + "\n"
    return out

def fullString(class_to_print, header='', omit=None):
    if omit == None: omit = list()
    out = '\n+' + header + ':\n'
    for attr_name in dir(class_to_print):
        attr = getattr(class_to_print, attr_name)
        out += " " + attr_name + ": " + unicode(attr) + "\n"
    return out


def getFields(my_class, omit=None):
    if omit == None: omit = list()
    _fields = list()
    for attr_name in dir(my_class):
            attr = getattr(my_class, attr_name)
            if type(attr) != types.MethodType:
                if attr_name not in omit and not attr_name.startswith('_'): 
                    _fields.append(attr_name)
    return _fields


def dumpObject(obj, path):
    if os.path.exists(path):
        if not os.path.isfile(path):
            raise Error("Filesystem path specified to dump an object does not specifiy a file!")
    _file = open(path, 'w') 
    _file.write(cPickle.dumps(obj)) 
    _file.close()


def readObject(path):
    _obj = None
    if os.path.exists(path):
        if not os.path.isfile(path):
            raise Error("Cannot read an object specified in the path!")
        _file = open(path, 'r') 
        try:
	        _obj = cPickle.load(_file) 
        except Exception, e:
            _log.error("Import error while restoring an object in path '%s', with an error: %s", path, e)
        _file.close()
    return _obj


def checkCreateDirectory(path):
    """
    Checkes the existence of a directory and if missing, creates
    it. Raises an error if the directory cannot be created or if the
    path is not a directory. The method can raise other Exceptions as
    well.
    """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        os.makedirs(path)
        _log.debug("Dirctory '%s' created.", path)
    elif not os.path.isdir(path):
        raise Error("Specified path '%s' already exists and is not a directory!", path)
    
def strsize(size):
    if size <= 1024:
        return str(size) + "B"
    if size <= 1022976:
        size = size/1024
        return str(size) + "kB"
    if size <= 1022976*1000:
        size = size/(1024*1000)
        return str(size) + "MB"
    if size <= 1022976*1000*1000:
        size = round(size/(1024*1000*1000.0),3)
        return str(size) + "GB"
    if size > 1022976*1000*1000:
        size = round(size/(1024*1000*1000*1000.0),3)
        return str(size) + "TB"

def strtime(seconds):
    if seconds < 60:
        return str(seconds) + "s"
    if seconds < 3600:
        min = int(seconds/60)
        sec = seconds%60
        return str(min) + "m:" + str(sec) + "s"
    if seconds < 3600*24:
        hour = int(seconds/3600)
        rest = seconds%3600
        return str(hour) + "h:" + strtime(rest)
    if seconds >= 3600*24:
        days = int(seconds/(3600*24))
        rest = seconds%(3600*24)
        return str(days) + "d:" + strtime(rest)

def command(command):
    """
    Excecutes a command via shell and returns its stdout. 

    @param command Command to be run in the shell
    @return tuple A tuple of std output, std error and return code
    """
    try:
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (so, se) = p.communicate()
        return (so.rstrip("\n"), se.rstrip("\n"), p.returncode)
    except OSError, e:
        _log.error("Excecuting command '%s' has failed, reason: %s" + e)
    return ""

def simple_command(command):
    return command(command)[0]

def classImport(modulename, klassname):
    try:
        mod = __import__(modulename)
        components = modulename.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        ctype = getattr(mod, klassname)
        return object.__new__(ctype)
    except Exception, e: 
        _log.debug("Failed to load specified class '%s' from module '%s', returning None, exception raised: %s", klassname, modulename, e)
        return None
    
class Fetch():
    """
    Fetches the content from the specified location. Much to simple
    fetch class. Will be rewriten later.
    """

    def __init__(self, store=None):
        self.store = store
        self.file = None
        self.initialized = False
        
    def acquire(self, reference):
        """
        Fetches the content specified by the reference. The return
        value is a reference to a file or None if the file already
        exists.

        @param reference Url reference to content
        @return File object or None if the file exists
        """
        fileName = ''
        try: 
            url = urlparse(reference)
            if url.scheme == 'http':
                fileName = os.path.basename(url.path)
            self.__init_store(fileName)
            if self.initialized:
                _log.info("Fetching content from the reference: '%s'", reference)
                urllib.urlretrieve(reference, self.file.name)
        except Exception, e:
            if self.file:
                self.file.close()
            raise FetchError("Failed to fetch content from the reference '%s', exception raised %s", reference, str(e))
        return self.file
           
    def __init_store(self, fileName):
        if self.store == None:
            self.file = tempfile.NamedTemporaryFile()
            self.initialized = True
        else:
            if not os.path.isdir(self.store):
                raise FetchError("The store pased " + str(self.store) + "is not a directory")
            if not os.path.exists(os.path.join(self.store, fileName)):
                self.file = file(os.path.join(self.store, fileName), 'wb')
                self.initialized = True
            else:
                _log.debug("The file in path '%s' already exists, won't acquire.", os.path.join(self.store, fileName))
                self.file = file(os.path.join(self.store, fileName), 'r')

class TimeSorter():

    def __init__(self):
        self.sorter = list()

    def fill(self, dateObjectTuple):
        """
        Fills the sorter
        """
        self.sorter.append(dateObjectTuple)

    def remove(self, dateObjectTuple):
        try:
            self.sorter.remove(dateObjectTuple)
        except:
            _log.debug("Specified tuple %s is not present in sorter", dateObjectTuple)

    def sort(self):
        """
        Sorts the tuples regarding the time object and returns a list
        of sorted objects. 
        """
        sorted = list()
        heap = list()
        for item in self.sorter:
            heappush(heap, item)
        while heap:
            sorted.append(heappop(heap)[1])
        return sorted

class Service(object):
    """
    Skeleton service class defining the service interface.
    """
    
    def __init__(self, serviceName=None, releaseVersion=None):
        if releaseVersion == None:
            self.releaseVersion = settings.VERSION
        self.type = self.__class__.__name__
        if serviceName == None:
            self.serviceName = self.type
        self.identifier = None
        self.working_directory = None
        self.config_file = None
        self.handler = None
        self.running = False

    def name(self):
        """
        Returns the name of the service
        """
        return self.serviceName

    def getIdentifier(self, string_identifier=None):
        """ 
        Returns an indentifier based on unique string supplied through
        method argument.
        """
        if self.identifier == None:
            if string_identifier == None:
                string_identifier = self.type
            self.identifier = sha1(unicode(string_identifier)).hexdigest()
        return self.identifier

    def getInstance(working_directory=None, config_file=None, handler=None):
        """ Creates an instance of a service."""
        _log.debug(self.status())
    getInstance = staticmethod(getInstance)

    def initialize(self):
        """
        Initializes the service.
        """
        _log.debug(self.status())

    def start(self):
        """
        Starts the service.
        """
        _log.debug(self.status())

    def restart(self):
        """
        Restarts the service.
        """
        _log.debug(self.status())

    def stop(self):
        """
        Stops the service.
        """
        _log.debug(self.status())

    def update(self):
        """
        Updates the service data structure.
        """
        _log.debug(self.status())

    def status(self):
        """
        Reports the service status.
        """
        _log.debug("Dummy service '%s' of type '%s', version '%s' status.", self.name(), self.type, self.version())

    def show(self, modifier=None):
        """
        Shows the service internals
        """
        out = ""
        if self.serviceName != None:
            out += self.serviceName + " "
        else:
            out += "/ "
        if self.identifier != None:
            out += self.identifier + " "
        else:
            out += "/ "
        if self.working_directory != None:
            out += self.working_directory + " "
        else:
            out += "/ "
        if self.config_file != None:
            out += self.config_file + " "
        else:
            out += "/ "
        out += self.type + " "
        out += self.version() + " "
        out += "\n"
        return out

    def version(self):
        """
        Returns the version of the service
        """
        return self.releaseVersion

def strsize(size):
    if size <= 1024:
        return str(size) + "B"
    if size <= 1022976:
        size = size/1024
        return str(size) + "kB"
    if size <= 1022976*1000:
        size = size/(1024*1000)
        return str(size) + "MB"
    if size <= 1022976*1000*1000:
        size = round(size/(1024*1000*1000.0),3)
        return str(size) + "GB"
    if size > 1022976*1000*1000:
        size = round(size/(1024*1000*1000*1000.0),3)
        return str(size) + "TB"

def strtime(seconds):
    if seconds < 60:
        return str(seconds) + "s"
    if seconds < 3600:
        min = int(seconds/60)
        sec = seconds%60
        return str(min) + "m:" + str(sec) + "s"
    if seconds < 3600*24:
        hour = int(seconds/3600)
        rest = seconds%3600
        return str(hour) + "h:" + strtime(rest)
    if seconds >= 3600*24:
        days = int(seconds/(3600*24))
        rest = seconds%(3600*24)
        return str(days) + "d:" + strtime(rest)

def time2duration(dtime):
    try:
        seconds = int(dtime)
        hours = seconds/3600
        mins = (seconds/60)%60
        secs = seconds%60
        return 'PT%02.0fH%02.0fM%02.0fS' % (hours,mins,secs)
    except (ValueError, TypeError, IndexError):
        try:
            t = dtime.split(":")
            if len(t) != 3:
                return dtime
            s = t[2].split(".")[0]
            return 'PT%sH%sM%sS' % (t[0],t[1],s)
        except Exception, e:
            return dtime
    
