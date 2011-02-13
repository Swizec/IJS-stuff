
from django.conf import settings
import os

def create_feed(form):
    dir = settings.FEED_DIR+"created/"
    if not os.path.isdir(dir):
        os.mkdir(dir)
      
    feed_dir = dir+form.cleaned_data['title'].replace(' ', '_')
    
    proc = os.popen(' && '.join(["export PYTHONPATH=$(pwd)/../../",
                                 "python ../ProviderToolbox/tools/managefeed.py -c -t '%s' -k '%s' -g '%s' -d %s -n %s -j %s" %
                                 (form.cleaned_data['title'], 
                                  form.cleaned_data['description'], 
                                  form.cleaned_data['originator'],
                                  feed_dir,
                                  form.cleaned_data['language'],
                                  form.cleaned_data['publisher'])]))
    return proc


def update_feed(form):
    proc = os.popen(' && '.join(["export PYTHONPATH=$(pwd)/../../",
                                 "python ../ProviderToolbox/tools/getfeed.py -l '%s'"\
                                 % form.cleaned_data['path']]))
    return proc


def add_item(form):
    proc = os.popen(' && '.join(
        ["export PYTHONPATH=$(pwd)/../../",
         "python ../ProviderToolbox/tools/managefeed.py -a -d %s -z %s -s '%s' -t '%s'" \
         % (settings.FEED_DIR+form.cleaned_data['feed_dir'],
            form.cleaned_data['file'],
            form.cleaned_data['synopsis'],
            form.cleaned_data['title'])]))
    
    return proc
