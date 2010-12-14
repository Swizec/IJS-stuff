# Create your views here.

from django.http import HttpResponse
from django.conf import settings

import os

from lib import feedparser

def begin(request):
    out = []
    for feed in os.listdir(settings.FEED_DIR):
        out.append(feedparser.parse(feed))
    
    return HttpResponse(out)
