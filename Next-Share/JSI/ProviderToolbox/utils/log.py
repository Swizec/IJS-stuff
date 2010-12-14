import logging, logging.handlers
import sys

from JSI.ProviderToolbox.conf import settings

init = False
level = settings.LOG_LEVEL
SYSLOG = settings.LOG_SYSLOG
_log = None

# Loglevels

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Store ProviderToolbox loggers names
ptloggers = list()

def initLog():
    # logging to a console using basicConfig, setting the format and time 
    logging.basicConfig(level=logging.NOTSET,
                        format='%(levelname)-7s %(asctime)s %(module)s [%(lineno)d]: %(message)s',
                        datefmt='%H:%M:%S')
    # logging to a sysylog 
    if SYSLOG:
        syslog_available = False
        if sys.platform == "darwin":
            syslog = logging.handlers.SysLogHandler(('localhost', 514),
                         facility=logging.handlers.SysLogHandler.LOG_DAEMON)
            syslog_available = True
        if sys.platform == "linux2":
            syslog = logging.handlers.SysLogHandler('/dev/log',
                         facility=logging.handlers.SysLogHandler.LOG_DAEMON)
            syslog_available = True
        if syslog_available:
            # Set log level to info till we don't find a way to pass
            # unicode characters properly to syslog
            syslog.setLevel(level)
            # set a format for syslog handler
            formatter = logging.Formatter('NextShare: ProviderToolbox - %(levelname)-7s %(module)s [%(lineno)d]: %(message)s')
            # tell the syslog handler to use the format
            syslog.setFormatter(formatter)
            # add the handler to the root logger
            logging.getLogger('').addHandler(syslog)
    # set logging level for the root logger to NOTSET. For any
    # other loggers the log level needs to be defined for them
    # explicitly.
    logging.getLogger('').setLevel(logging.NOTSET)
    global _log, ptloggers
    _log = logging.getLogger('Log')
    ptloggers.append('Log')

def getLog(name):
    """ 
    Returns a logger through which the log messages can be send. If an
    empty name is used the root logger is returned. When the function
    is called for the first time the logging gets initialized.
    """
    global init, ptloggers
    if not init: 
        initLog()
        init = True
    ptloggers.append(name)
    return logging.getLogger(name) 

def removeLog(name):
    global init, ptloggers
    if not init:
        return
    if name in ptloggers:
        ptloggers.remove(name)

def listLogLevels():
    root = logging.getLogger('root')
    out = "= Root logger =\n"
    out += "root: " + logging.getLevelName(root.getEffectiveLevel()) + " manager disable: " +  logging.getLevelName(root.manager.disable) + " (" +  str(root.propagate) + ") " + "\n"
    out += "= ProviderToolbox logger: level =\n"
    for l in ptloggers:
        out += l + ": " + logging.getLevelName(logging.getLogger(l).getEffectiveLevel()) + " (" +  str(logging.getLogger(l).propagate) + ") " + "\n"
    out += " = Other loggers: level =\n"
    rl = logging.getLogger('')
    for k, v in rl.manager.loggerDict.items():
        if k not in ptloggers:
            out += k + ": " + logging.getLevelName(v.getEffectiveLevel()) + " (" +  str(v.propagate) + ") " + "\n"
    return out

def cycleLevel():
    """
    Cycles through the log level tresholds.
    """
    global level
    if level < logging.CRITICAL:
        level = level + 10
    else:
        level = logging.DEBUG
    setLevel(level)

def setLevel(l, name=None):
    """
    Sets the level tresholds as are defined in the logging framework:

             10 DEBUG
             20 INFO
             30 WARNING
             40 ERROR
             50 CRITICAL

    Default treshold level is 30.
    """
    global level, _log
    if l >= logging.DEBUG and l <= logging.CRITICAL:
        level = l
        if name != None:
            if name in ptloggers:
                logging.getLogger(name).setLevel(level)
            else:
                _log.error("No such logger %s!", name) 
        else:
            for n in ptloggers:
                setLevel(l, n)

def shutUpOtherLoggers():
    rl = logging.getLogger('')
    su = ""
    for k, v in rl.manager.loggerDict.items():
        if k not in ptloggers:
            su += " " + k + "(" + logging.getLevelName(v.getEffectiveLevel()) + "->" + logging.getLevelName(logging.CRITICAL) + ")"
            logging.getLogger(k).setLevel(logging.CRITICAL)
    _log.info("Shutting up other loggers: " + su)


def validateLevel(level):
    try:
        l = int(level)
    except Exception, e:
        _log.warn("Log level is not an integer value! (" + str(level) + ")")
        return None
    if l > logging.CRITICAL or l < logging.DEBUG:
        _log.warn("Log level is not in valid range! (" + str(logging.DEBUG) + "-" + str(logging.CRITICAL) + ")")
        return None
    return l - l%10
    

def force(message):
    """
    Forces logging of the mesagge with the debug level disregard the
    log level currently set.
    """
    log = getLog('')
    oldLevel = level
    log.setLevel(logging.DEBUG)
    log.debug(message)
    log.setLevel(oldLevel)

def shutdown():
    logging.shutdown()

