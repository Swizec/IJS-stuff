
import os

def create_feed(form, feed_dir):
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
