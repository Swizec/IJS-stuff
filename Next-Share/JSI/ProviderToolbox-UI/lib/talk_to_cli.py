from django.conf import settings
import subprocess
import shlex
import unicodedata
from os.path import abspath

from JSI.ProviderToolbox.conf import settings as pt_settings

# Needs:
# + -e export url
# + -p where the link will be published
# + -i image of the feed (file selector) 
def create_feed(form, feed_dir):
    c = "python %s -c -t '%s' -k '%s' -g '%s' -d '%s' -n '%s' -j '%s'" \
        % (pt_settings.PT_DIR + "/tools/managefeed.py", 
           form.cleaned_data['title'], 
           form.cleaned_data['description'], 
           form.cleaned_data['originator'],
           feed_dir,
           form.cleaned_data['language'],
           form.cleaned_data['publisher'])
    return command(asciify(c), env={"PYTHONPATH":pt_settings.PT_IMPORT_DIR})

def update_feed(form):
    path = abspath(form.cleaned_data['path'])
    c = "python %s -u '%s'" % (pt_settings.PT_DIR + "/tools/getfeed.py", 
                               path)
    # shlex is not unicode ready
    return command(asciify(c), env={"PYTHONPATH":pt_settings.PT_IMPORT_DIR})

def refetch_feed(form):
    path = abspath(form.cleaned_data['path'])
    c = "python %s -f '%s'" % (pt_settings.PT_DIR + "/tools/getfeed.py", 
                               path)
    # shlex is not unicode ready
    return command(asciify(c), env={"PYTHONPATH":pt_settings.PT_IMPORT_DIR})

# Needs:
# + -y mime type
def add_item(form):
    c = "python %s -a -d '%s' -z '%s' -s '%s' -t '%s'" \
        % (pt_settings.PT_DIR + "/tools/managefeed.py", 
           settings.FEED_DIR+form.cleaned_data['feed_dir'],
           form.cleaned_data['file'],
           form.cleaned_data['synopsis'],
           form.cleaned_data['title'])
    return command(asciify(c), env={"PYTHONPATH":pt_settings.PT_IMPORT_DIR})

def command(command, env=None):
    """
    Excecutes a command as a process and returns its stdout. 

    @param command Command to be run 
    @param env A dict specifying the process environment 
    @return tuple std output, std error and return code as tuple or an
                  empty string if OSError is raised
    """
    try:
        print "Command called: " + command
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        (so, se) = p.communicate()
        return (so.rstrip("\n"), se.rstrip("\n"), p.returncode)
    except OSError, e:
        print "Excecuting command '%s' has failed, reason: %s" % (command, e)
    return ""

def asciify(string):
    return unicodedata.normalize('NFKD', string).encode('ascii','ignore')


#def torrent_info(file):
#    c = "python %s %s" \
#        % (pt_settings.PT_DIR + "/tools/managefeed.py", 
#           settings.FEED_DIR+form.cleaned_data['feed_dir'],
#           form.cleaned_data['file'],
#           form.cleaned_data['synopsis'],
#           form.cleaned_data['title'])
#    return command(asciify(c), env={"PYTHONPATH":pt_settings.PT_IMPORT_DIR})
