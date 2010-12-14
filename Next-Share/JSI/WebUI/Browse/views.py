# Create your views here.

from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render_to_response

import os

from lib import feedparser

def begin(request):
    def parse(feed):
        return feedparser.parse(settings.FEED_DIR+feed)
    
    feeds = map(parse, os.listdir(settings.FEED_DIR))
    
    return render_to_response('browse.html',
                              {'feeds': feeds,
                               'MEDIA_URL': settings.MEDIA_URL})
