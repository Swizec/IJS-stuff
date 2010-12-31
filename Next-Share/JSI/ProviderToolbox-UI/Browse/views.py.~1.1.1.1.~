# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.core.context_processors import csrf
from django.conf import settings
from django.shortcuts import render_to_response

import os, urllib

from lib import feedparser
from forms import AddForm

def begin(request):
    def parse(feed):
        feed = feedparser.parse(settings.FEED_DIR+feed)
        feed.channel.description = feed.channel.description.encode('utf-8')
        return {'data': feed,
                'edit_form': AddForm(QueryDict(urllib.urlencode(feed.channel)))}
    
    feeds = map(parse, os.listdir(settings.FEED_DIR))

    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            # handle
            return HttpResponseRedirect('/')
    else:
        form = AddForm()

    context = {'feeds': feeds,
               'MEDIA_URL': settings.MEDIA_URL,
               'add_form': form}
    context.update(csrf(request))
    
    return render_to_response('browse.html', context)
