# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import QueryDict, HttpRequest
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string

import os, urllib, re, shutil, json
import lxml
from lxml import etree
from datetime import datetime

from lib import feedparser
from lib import talk_to_cli as cli
from forms import MetaForm, ListDirForm, AddFeedForm, PathForm, CreateFeedForm, AddItemForm
from models import AtomFeed

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

def begin(request):
    def parse(feed):
        feed = feedparser.parse(settings.FEED_DIR+feed)
        feed.channel.description = feed.channel.description.encode('utf-8')
        return {'data': feed,
                'edit_form': MetaForm(QueryDict(urllib.urlencode(feed.channel)))}
    
    #feeds = map(parse, os.listdir(settings.FEED_DIR))

    # TODO this could do with some refactoring too
    if request.method == 'POST':
        form = MetaForm(request.POST)
        if form.is_valid():
            def rewriteWithNew(xml):
                rmg = RichMetadataGenerator.getInstance()
                meta = rmg.getRichMetadata(open(xml, 'r'))
            
                for key in form.cleaned_data.keys():
                    if key not in ['filename', 'should_cascade']:
                        meta.__getattr__(key)(form.cleaned_data[key])
                
                f = open(xml, 'w')
                f.write(rmg.build(meta))
                f.close()
              
            feed = settings.FEED_DIR+form.cleaned_data['filename']
            rewriteWithNew(feed)
            
            if form.cleaned_data['should_cascade'] == 'True':
                dir = feed.rsplit('/', 1)[0]
                for file in os.listdir(dir):
                    if file.endswith(".xml"):
                        rewriteWithNew(dir+file)
                
            
            return HttpResponseRedirect('/')
    else:
        form = AddFeedForm()

    context = {'feeds': [],
               'MEDIA_URL': settings.MEDIA_URL,
               'add_form': form,
               'create_form': CreateFeedForm()}
    context.update(csrf(request))
    
    return render_to_response('browse.html', context)

def add_feed(request):
  form = AddFeedForm(request.POST)
  if form.is_valid():
      proc = os.popen(' && '.join(["export PYTHONPATH=$(pwd)/../../",
                                   "python ../ProviderToolbox/tools/getfeed.py -l '%s'"\
                                   % form.cleaned_data['url']]))
    
      return HttpResponse(proc.read(),
                          mimetype="text")
  else:
      return HttpResponseBadRequest("Wrong data posted")
    
def create_feed(request):
  form = CreateFeedForm(request.POST)
  if form.is_valid():
      dir = settings.FEED_DIR+"created/"
      if not os.path.isdir(dir):
          os.mkdir(dir)
      
      feed_dir = dir+form.cleaned_data['title'].replace(' ', '_')
    
      (so,se,rv) = cli.create_feed(form, feed_dir)
      if rv == 0:
          return HttpResponseRedirect('/')
      else:
          return HttpResponseBadRequest("se")
  else:
      return HttpResponseBadRequest("Wrong data posted")

def fetch_feed(request):
    form = PathForm(request.GET)
    if form.is_valid():
        path = form.cleaned_data['path']

        if path.endswith('.xml'):
            (feed, item) = path.rsplit('/', 1)
            item = item.split('.')[0]

            tree = etree.fromstring(AtomFeed.objects.get(feed).feed.encode('utf-8'))
            for child in tree:
                if child.tag == '{http://www.w3.org/2005/Atom}entry':
                    href = child.find('{http://www.w3.org/2005/Atom}link').attrib.get('href')
                    if href.rsplit('/', 1)[1].split('.')[0] == item:
                        return HttpResponse(etree.tostring(child, pretty_print=True))
                
            return HttpResponse("Couldn't find item in feed")
        else:
            return HttpResponse(AtomFeed.objects.get(path).feed)
    else:
        return HttpResponseBadRequest("Expected a path")
                

def delete_feed(request):
    form = PathForm(request.GET)
    if form.is_valid():
        path = form.cleaned_data['path']
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
        return HttpResponse('OK')
    else:
        return HttpResponseBadRequest("Expected a path")

@csrf_exempt
def add_item(request):
    form = AddItemForm(request.POST)
    if form.is_valid():
        (so,se,rv) = cli.add_item(form)
        if rv == 0:
            return HttpResponseRedirect('/')
        else:
            return HttpResponseBadRequest("se")
    else:
        return HttpResponseBadRequest("Bad data")


def list_dir(request):
    alphanum = re.compile('[^0-9a-zA-Z/]+')
    form = ListDirForm(request.GET)

    #TODO: refactor this very fugly section
  
    def get_data(item):
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
            filename = dir.replace(settings.FEED_DIR, '')+parent+item+'.xml'
            main_meta = True
        else:
            if not item.endswith('.xml') or item[:-4] == parent[1:-1]:
                return None
            meta = rmg.getRichMetadata(settings.FEED_DIR+parent+"/"+item)
            filename = parent+"/"+item
            main_meta = False
            
        rich_meta = {}
        formdata = {}

        for api in meta.getAPIMethods():
            entry = None
            if api.startswith("get"):
                try:
#                    entry = meta[api]().encode('utf-8')
                    f  = meta.__getattr__(api)
                    entry = f().encode('utf-8')
                except AttributeError:
                    entry = None

                if entry:
                    rich_meta[metadata.HUMAN_DESCRIPTION.get(meta.method2attrib[api])] = entry
                    formdata[api.replace('get', 'set')] = entry
                else:
                    formdata[api.replace('get', 'set')] = ''

        formdata['filename'] = filename
        formdata['should_cascade'] = main_meta

        return {'dir': os.path.isdir(dir),
                'dirpath': item,
                'fresh': item in request.session.get('fresh_items', []),
                'tabs': ['f', 'v'] if os.path.isdir(dir) else ['f', 't', 'v'],
                'name': item,
                'created_feed': basic_meta.get('location', '').startswith("file://"),
                'filename': filename,
                'basic_meta': basic_meta,
                'rich_meta': rich_meta,
                'parent': form.cleaned_data['dir'],
                'item_form': AddItemForm(),
                'edit_form': MetaForm(QueryDict(urllib.urlencode(formdata)), main_meta=main_meta),
                'id': ''.join([alphanum.sub('', parent) ,alphanum.sub('', item)]).replace('/', '-')}

    if form.is_valid():
        items = filter(lambda i: i != None, 
                       map(get_data,
                           sorted(os.listdir(settings.FEED_DIR+form.cleaned_data['dir']))))

        # TODO figuring out if this is a created_feed needs refactoring
        # this is just a temporary implementation
        created_feed = False

        try:
            basic_meta = {}
            for line in  open(settings.FEED_DIR+form.cleaned_data['dir']+'/.properties'):
                (key, val) = line.split(' = ')
                basic_meta[key] = val
            created_feed = basic_meta['location'].startswith('file://')
        except IOError:
            pass

        # fresh data is only valid once
        request.session['fresh_items'] = []

        context = {'created_feed': created_feed,
                   'item_form': AddItemForm(),
                   'items': items,
                   'parent': form.cleaned_data['dir'],
                   'MEDIA_URL': settings.MEDIA_URL}
        context.update(csrf(request))

        return render_to_response('list_dir.html', context, mimetype="text/html")


def update_feed(request):
    form = PathForm(request.GET)
    if form.is_valid():
        path = form.cleaned_data['path']

        feed = AtomFeed.objects.get(path)
        if (datetime.now()-feed.time).seconds > 10:
            diff = feed.update()
            request.session['fresh_items'] = diff['fresh']
            print diff['fresh']

        
        return HttpResponse('OK')
    else:
        return HttpResponseBadRequest("Expected a path")
