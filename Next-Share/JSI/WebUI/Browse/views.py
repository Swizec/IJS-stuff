# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.core.context_processors import csrf
from django.conf import settings
from django.shortcuts import render_to_response

import os

from lib import feedparser
from forms import AddForm

def begin(request):
    def parse(feed):
        return feedparser.parse(settings.FEED_DIR+feed)
    
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
