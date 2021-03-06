# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.core.context_processors import csrf
from django.conf import settings
from django.shortcuts import render_to_response

import os, urllib, re

from lib import feedparser
from forms import AddForm, ListDirForm

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator

def begin(request):
    def parse(feed):
        feed = feedparser.parse(settings.FEED_DIR+feed)
        feed.channel.description = feed.channel.description.encode('utf-8')
        return {'data': feed,
                'edit_form': AddForm(QueryDict(urllib.urlencode(feed.channel)))}
    
    #feeds = map(parse, os.listdir(settings.FEED_DIR))

    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            rmg = RichMetadataGenerator.getInstance()
            m = rmg.getRichMetadata()

            m.setTitle(form.cleaned_data['title'])
            #m.setLanguage(form.cleaned_data['language'])
            #m.setGenre(form.cleaned_data['genre'])
            
            print rmg.prettyPrint(rmg.build(m))
            

            return HttpResponseRedirect('/')
    else:
        form = AddForm()

    context = {'feeds': [],
               'MEDIA_URL': settings.MEDIA_URL,
               'add_form': form}
    context.update(csrf(request))
    
    return render_to_response('browse.html', context)

def list_dir(request):
    alphanum = re.compile('[^0-9a-zA-Z/]+')
    form = ListDirForm(request.GET)

    def parse(item):
        parent = form.cleaned_data['dir']
        return {'dir': os.path.isdir(settings.FEED_DIR+item),
                'name': item,
                'parent': form.cleaned_data['dir'],
                'id': ''.join([alphanum.sub('', parent) ,alphanum.sub('', item)]).replace('/', '-')}

    if form.is_valid():
        print form.cleaned_data['dir']
        items = map(parse, sorted(os.listdir(settings.FEED_DIR+form.cleaned_data['dir'])))
        
        context = {'items': items,
                   'parent': form.cleaned_data['dir'],
                   'MEDIA_URL': settings.MEDIA_URL}
        context.update(csrf(request))

        return render_to_response('list_dir.html', context)
