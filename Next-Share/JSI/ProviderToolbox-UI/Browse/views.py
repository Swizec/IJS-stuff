# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.core.context_processors import csrf
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string

import os, urllib, re

from lib import feedparser
from forms import MetaForm, ListDirForm

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

def begin(request):
    def parse(feed):
        feed = feedparser.parse(settings.FEED_DIR+feed)
        feed.channel.description = feed.channel.description.encode('utf-8')
        return {'data': feed,
                'edit_form': MetaForm(QueryDict(urllib.urlencode(feed.channel)))}
    
    #feeds = map(parse, os.listdir(settings.FEED_DIR))

    if request.method == 'POST':
        form = MetaForm(request.POST)
        if form.is_valid():
            rmg = RichMetadataGenerator.getInstance()
            meta = rmg.getRichMetadata()
            
            for key in form.cleaned_data.keys():
              if key != 'filename':
                meta.__getattr__(key)(form.cleaned_data[key])
              
            # TODO: security issue
            #print form.cleaned_data['filename']
            f = open(form.cleaned_data['filename'], 'w')
            f.write(rmg.build(meta))
            f.close()
            
            return HttpResponseRedirect('/')
    else:
        form = MetaForm()

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
        dir = settings.FEED_DIR+parent+"/"+item+"/"
        basic_meta = {}
        rmg = RichMetadataGenerator.getInstance()
        
        if os.path.isdir(dir):
          if '.properties' not in os.listdir(settings.FEED_DIR+item):
            return None
        
          for line in open(dir+'.properties'):
            (key, val) = line.split(' = ')
            basic_meta[key] = val
          
          meta = rmg.getRichMetadata(dir+parent+item+'.xml')
          filename = dir+item+'.xml'
          main_meta = True
        else:
          if not item.endswith('.xml') or item[:-4] == parent[1:-1]:
            return None
          meta = rmg.getRichMetadata(settings.FEED_DIR+parent+"/"+item)
          filename = settings.FEED_DIR+parent+"/"+item
          main_meta = False
            
        rich_meta = {}
        formdata = {}
        
        for api in meta.getAPIMethods():
          if api.startswith("get"):
            try:
              entry = meta[api]().encode('utf-8')
            except AttributeError:
              entry = ''
            
            if entry != '':
              rich_meta[metadata.HUMAN_DESCRIPTION.get(meta.method2attrib[api])] = entry
              MetaForm
            formdata[api.replace('get', 'set')] = entry
            
        formdata['filename'] = filename
            
        return {'dir': os.path.isdir(dir),
                'dirpath': item,
                'name': item,
                'basic_meta': basic_meta,
                'rich_meta': rich_meta,
                'parent': form.cleaned_data['dir'],
                'edit_form': MetaForm(QueryDict(urllib.urlencode(formdata)), main_meta=main_meta),
                'id': ''.join([alphanum.sub('', parent) ,alphanum.sub('', item)]).replace('/', '-')}

    if form.is_valid():
        items = filter(lambda i: i != None, 
                       map(parse, sorted(os.listdir(settings.FEED_DIR+form.cleaned_data['dir']))))
        
        context = {'items': items,
                   'parent': form.cleaned_data['dir'],
                   'MEDIA_URL': settings.MEDIA_URL}
        context.update(csrf(request))
        
        #print render_to_string('list_dir.html', context)

        return render_to_response('list_dir.html', context, mimetype="text/html")
