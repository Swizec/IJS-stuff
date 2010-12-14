"""
Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
Syndication feed generation library -- used for generating RSS, etc.

Sample usage:

>>> from django.utils import feedgenerator
>>> feed = feedgenerator.Rss201rev2Feed(
...     title=u"Poynter E-Media Tidbits",
...     link=u"http://www.poynter.org/column.asp?id=31", 
...     description=u"A group weblog by the sharpest minds in online media/journalism/publishing.",
...     language=u"en",
... )
>>> feed.add_item(
...     title="Hello",
...     link=u"http://www.holovaty.com/test/",
...     description="Testing."
... )
>>> fp = open('test.rss', 'w')
>>> feed.write(fp, 'utf-8')
>>> fp.close()

For definitions of the different versions of RSS, see:
http://diveintomark.org/archives/2004/02/04/incompatible-rss
"""

import datetime
import urlparse
from functional import Promise

def rfc2822_date(date):
    # We do this ourselves to be timezone aware, email.Utils is not tz aware.
    if date.tzinfo:
        time_str = date.strftime('%a, %d %b %Y %H:%M:%S ')
        offset = date.tzinfo.utcoffset(date)
        timezone = (offset.days * 24 * 60) + (offset.seconds / 60)
        hour, minute = divmod(timezone, 60)
        return time_str + "%+03d%02d" % (hour, minute)
    else:
        return date.strftime('%a, %d %b %Y %H:%M:%S -0000')

def rfc3339_date(date):
    if date.tzinfo:
        time_str = date.strftime('%Y-%m-%dT%H:%M:%S')
        offset = date.tzinfo.utcoffset(date)
        timezone = (offset.days * 24 * 60) + (offset.seconds / 60)
        hour, minute = divmod(timezone, 60)
        return time_str + "%+03d:%02d" % (hour, minute)
    else:
        return date.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_tag_uri(url, date):
    """
    Creates a TagURI.

    See http://diveintomark.org/archives/2004/05/28/howto-atom-id
    """
    url_split = urlparse.urlparse(url)

    # Python 2.4 didn't have named attributes on split results or the hostname.
    hostname = getattr(url_split, 'hostname', url_split[1].split(':')[0])
    path = url_split[2]
    fragment = url_split[5]

    d = ''
    if date is not None:
        d = ',%s' % date.strftime('%Y-%m-%d')
    return u'tag:%s%s:%s/%s' % (hostname, d, path, fragment)

# From RFC4287 (http://tools.ietf.org/html/rfc4287)
#
#  o  atom:feed elements MUST contain one or more atom:author elements,
#    unless all of the atom:feed element's child atom:entry elements
#    contain at least one atom:author element.
# Not a MUST 
# o  atom:feed elements MAY contain any number of atom:category
#    elements.
# o  atom:feed elements MAY contain any number of atom:contributor
#    elements.
# o  atom:feed elements MUST NOT contain more than one atom:generator
#    element.
# o  atom:feed elements MUST NOT contain more than one atom:icon
#    element.
# o  atom:feed elements MUST NOT contain more than one atom:logo
#    element.
# o  atom:feed elements MUST contain exactly one atom:id element.
# MUST - feed_guid or feed_link, always 
# o  atom:feed elements SHOULD contain one atom:link element with a rel
#    attribute value of "self".  This is the preferred URI for
#    retrieving Atom Feed Documents representing this Atom feed.
# Not exactly a MUST
# o  atom:feed elements MUST NOT contain more than one atom:link
#    element with a rel attribute value of "alternate" that has the
#    same combination of type and hreflang attribute values.
# o  atom:feed elements MAY contain additional atom:link elements
#    beyond those described above.
# o  atom:feed elements MUST NOT contain more than one atom:rights
#    element.
# o  atom:feed elements MUST NOT contain more than one atom:subtitle
#    element.
# o  atom:feed elements MUST contain exactly one atom:title element.
# MUST - ok
# o  atom:feed elements MUST contain exactly one atom:updated element.
# MUST - automatically provided

# atomFeed =
#    element atom:feed {
#       atomCommonAttributes,
#       (atomAuthor*
#        & atomCategory*
#        & atomContributor*
#        & atomGenerator?
#        & atomIcon?
#        & atomId
#        & atomLink*
#        & atomLogo?
#        & atomRights?
#        & atomSubtitle?
#        & atomTitle
#        & atomUpdated
#        & extensionElement*),
#       atomEntry*
#    }


class SyndicationFeed(object):
    "Base class for all syndication feeds. Subclasses should provide write()"
    def __init__(self, title, feed_url, description=None, language=None, 
                 author_email=None, author_name=None, author_link=None, 
                 subtitle=None, categories=None, link=None, 
                 feed_copyright=None, feed_guid=None, ttl=None, 
                 logo=None, icon=None, image=None, **kwargs):
        to_unicode = lambda s: force_unicode(s, strings_only=True)
        if categories and isinstance(categories, tuple):
            categories = [force_unicode(c) for c in categories]
        elif categories and isinstance(categories, list):
            for i in categories:
                i = [force_unicode(c) for c in i]
        if ttl is not None:
            # Force ints to unicode
            ttl = force_unicode(ttl)
        self.feed = {
            'title': to_unicode(title),
            'link': iri_to_uri(link),
            'description': to_unicode(description),
            'language': to_unicode(language),
            'author_email': to_unicode(author_email),
            'author_name': to_unicode(author_name),
            'author_link': iri_to_uri(author_link),
            'subtitle': to_unicode(subtitle),
            'categories': categories or (),
            'feed_url': iri_to_uri(feed_url),
            'feed_copyright': to_unicode(feed_copyright),
            'id': feed_guid or feed_url,
            'ttl': ttl,
            'logo': logo,
            'icon': icon,
            'image': to_unicode(image)
        }
        self.feed.update(kwargs)
        self.items = []

# o  atom:entry elements MUST contain one or more atom:author elements,
#    unless the atom:entry contains an atom:source element that
#    contains an atom:author element or, in an Atom Feed Document, the
#    atom:feed element contains an atom:author element itself.
# o  atom:entry elements MAY contain any number of atom:category
#    elements.
# o  atom:entry elements MUST NOT contain more than one atom:content
#    element.
# o  atom:entry elements MAY contain any number of atom:contributor
#    elements.
# o  atom:entry elements MUST contain exactly one atom:id element.
# MUST - implicitely handled
# o  atom:entry elements that contain no child atom:content element
#    MUST contain at least one atom:link element with a rel attribute
#    value of "alternate".
# MUST if no content
# o  atom:entry elements MUST NOT contain more than one atom:link
#    element with a rel attribute value of "alternate" that has the
#    same combination of type and hreflang attribute values.
# o  atom:entry elements MAY contain additional atom:link elements
#    beyond those described above.
# o  atom:entry elements MUST NOT contain more than one atom:published
#    element.
# o  atom:entry elements MUST NOT contain more than one atom:rights
#    element.
# o  atom:entry elements MUST NOT contain more than one atom:source
#    element.
# o  atom:entry elements MUST contain an atom:summary element in either
#    of the following cases:
#    *  the atom:entry contains an atom:content that has a "src"
#       attribute (and is thus empty).
#    *  the atom:entry contains content that is encoded in Base64;
#       i.e., the "type" attribute of atom:content is a MIME media type
#       [MIMEREG], but is not an XML media type [RFC3023], does not
#       begin with "text/", and does not end with "/xml" or "+xml".
# o  atom:entry elements MUST NOT contain more than one atom:summary
#    element.
# o  atom:entry elements MUST contain exactly one atom:title element.
# MUST - ok
# o  atom:entry elements MUST contain exactly one atom:updated element.
# MUST - implicitely provided

# atomEntry =
#    element atom:entry {
#       atomCommonAttributes,
#       (atomAuthor*
#        & atomCategory*
#        & atomContent?
#        & atomContributor*
#        & atomId
#        & atomLink*
#        & atomPublished?
#        & atomRights?
#        & atomSource?
#        & atomSummary?
#        & atomTitle
#        & atomUpdated
#        & extensionElement*)
#    }

    def add_item(self, title, description, link=None, unique_id=None, 
                 author_email=None, author_name=None, author_link=None, 
                 pubdate=None, comments=None, enclosure=None, 
                 categories=(), item_copyright=None, ttl=None, 
                 image=None, content=None, link_type = None,
                 description_type = None, **kwargs):
        """
        Adds an item to the feed. All args are expected to be Python Unicode
        objects except pubdate, which is a datetime.datetime object, and
        enclosure, which is an instance of the Enclosure class.
        """
        to_unicode = lambda s: force_unicode(s, strings_only=True)
        if categories and isinstance(categories, tuple):
            categories = [to_unicode(c) for c in categories]
        elif categories and isinstance(categories, list):
            for i in categories:
                i = [to_unicode(c) for c in i]
        if ttl is not None:
            # Force ints to unicode
            ttl = force_unicode(ttl)
        item = {
            'title': to_unicode(title),
            'link': iri_to_uri(link),
            'link_type': to_unicode(link_type),
            # According to P2P-Next specification
            'content': content if not link else None, 
            'description': to_unicode(description),
            'description_type': to_unicode(description_type),
            'author_email': to_unicode(author_email),
            'author_name': to_unicode(author_name),
            'author_link': iri_to_uri(author_link),
            'pubdate': pubdate,
            'unique_id': to_unicode(unique_id),
            'enclosure': enclosure,
            'categories': categories or (),
            'item_copyright': to_unicode(item_copyright),
            'ttl': ttl,
            'image': image,
            # RSS
            'comments': to_unicode(comments),
        }
        item.update(kwargs)
        self.items.append(item)

    def num_items(self):
        return len(self.items)

    def root_attributes(self):
        """
        Return extra attributes to place on the root (i.e. feed/channel) element.
        Called from write().
        """
        return {}

    def add_root_elements(self, handler):
        """
        Add elements in the root (i.e. feed/channel) element. Called
        from write().
        """
        pass

    def item_attributes(self, item):
        """
        Return extra attributes to place on each item (i.e. item/entry) element.
        """
        return {}

    def add_item_elements(self, handler, item):
        """
        Add elements on each item (i.e. item/entry) element.
        """
        pass

    def write(self, outfile, encoding):
        """
        Outputs the feed in the given encoding to outfile, which is a file-like
        object. Subclasses should override this.
        """
        raise NotImplementedError

    def writeString(self, encoding='utf-8'):
        """
        Returns the feed in the given encoding as a string.
        """
        from StringIO import StringIO
        s = StringIO()
        self.write(s, encoding)
        return s.getvalue()

    def latest_post_date(self):
        """
        Returns the latest item's pubdate. If none of them have a pubdate,
        this returns the current date/time.
        """
        updates = [i['pubdate'] for i in self.items if i['pubdate'] is not None]
        if len(updates) > 0:
            updates.sort()
            return updates[-1]
        else:
            return datetime.datetime.now()

class Enclosure(object):
    "Represents an RSS enclosure"
    def __init__(self, url, length, mime_type):
        "All args are expected to be Python Unicode objects"
        self.length, self.mime_type = length, mime_type
        self.url = iri_to_uri(url)

# Commented out since have changed some logic of the SyndicationFeed,
# not all original author assumptions holds

# class RssFeed(SyndicationFeed):
#     mime_type = 'application/rss+xml'
#     def write(self, outfile, encoding):
#         handler = SimplerXMLGenerator(outfile, encoding)
#         handler.startDocument()
#         handler.startElement(u"rss", self.rss_attributes())
#         handler.startElement(u"channel", self.root_attributes())
#         self.add_root_elements(handler)
#         self.write_items(handler)
#         self.endChannelElement(handler)
#         handler.endElement(u"rss")

#     def rss_attributes(self):
#         return {u"version": self._version,
#                 u"xmlns:atom": u"http://www.w3.org/2005/Atom"}

#     def write_items(self, handler):
#         for item in self.items:
#             handler.startElement(u'item', self.item_attributes(item))
#             self.add_item_elements(handler, item)
#             handler.endElement(u"item")

#     def add_root_elements(self, handler):
#         handler.addQuickElement(u"title", self.feed['title'])
#         handler.addQuickElement(u"link", self.feed['link'])
#         handler.addQuickElement(u"description", self.feed['description'])
#         handler.addQuickElement(u"atom:link", None, {u"rel": u"self", u"href": self.feed['feed_url']})
#         if self.feed['language'] is not None:
#             handler.addQuickElement(u"language", self.feed['language'])
#         for cat in self.feed['categories']:
#             handler.addQuickElement(u"category", cat)
#         if self.feed['feed_copyright'] is not None:
#             handler.addQuickElement(u"copyright", self.feed['feed_copyright'])
#         handler.addQuickElement(u"lastBuildDate", rfc2822_date(self.latest_post_date()).decode('utf-8'))
#         if self.feed['ttl'] is not None:
#             handler.addQuickElement(u"ttl", self.feed['ttl'])

#     def endChannelElement(self, handler):
#         handler.endElement(u"channel")

# class RssUserland091Feed(RssFeed):
#     _version = u"0.91"
#     def add_item_elements(self, handler, item):
#         handler.addQuickElement(u"title", item['title'])
#         handler.addQuickElement(u"link", item['link'])
#         if item['description'] is not None:
#             handler.addQuickElement(u"description", item['description'])

# class Rss201rev2Feed(RssFeed):
#     # Spec: http://blogs.law.harvard.edu/tech/rss
#     _version = u"2.0"
#     def add_item_elements(self, handler, item):
#         handler.addQuickElement(u"title", item['title'])
#         handler.addQuickElement(u"link", item['link'])
#         if item['description'] is not None:
#             handler.addQuickElement(u"description", item['description'])

#         # Author information.
#         if item["author_name"] and item["author_email"]:
#             handler.addQuickElement(u"author", "%s (%s)" % \
#                 (item['author_email'], item['author_name']))
#         elif item["author_email"]:
#             handler.addQuickElement(u"author", item["author_email"])
#         elif item["author_name"]:
#             handler.addQuickElement(u"dc:creator", item["author_name"], {u"xmlns:dc": u"http://purl.org/dc/elements/1.1/"})

#         if item['pubdate'] is not None:
#             handler.addQuickElement(u"pubDate", rfc2822_date(item['pubdate']).decode('utf-8'))
#         if item['comments'] is not None:
#             handler.addQuickElement(u"comments", item['comments'])
#         if item['unique_id'] is not None:
#             handler.addQuickElement(u"guid", item['unique_id'])
#         if item['ttl'] is not None:
#             handler.addQuickElement(u"ttl", item['ttl'])

#         # Enclosure.
#         if item['enclosure'] is not None:
#             handler.addQuickElement(u"enclosure", '',
#                 {u"url": item['enclosure'].url, u"length": item['enclosure'].length,
#                     u"type": item['enclosure'].mime_type})

#         # Categories.
#         for cat in item['categories']:
#             handler.addQuickElement(u"category", cat)

class Atom1Feed(SyndicationFeed):
    # Spec: http://atompub.org/2005/07/11/draft-ietf-atompub-format-10.html
    mime_type = 'application/atom+xml'
    ns = u"http://www.w3.org/2005/Atom"

    def write(self, outfile, encoding):
        handler = SimplerXMLGenerator(outfile, encoding)
        handler.startDocument()
        handler.startElement(u'feed', self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        handler.endElement(u"feed")

    def root_attributes(self):
        if self.feed['language'] is not None:
            return {u"xmlns": self.ns, u"xml:lang": self.feed['language']}
        else:
            return {u"xmlns": self.ns}

    def add_root_elements(self, handler):
        handler.addQuickElement(u"title", self.feed['title'])
        handler.addQuickElement(u"link", "", {u"rel": u"alternate", u"href": self.feed['link']})
        if self.feed['feed_url'] is not None:
            handler.addQuickElement(u"link", "", {u"rel": u"self", u"href": self.feed['feed_url']})
        handler.addQuickElement(u"id", self.feed['id'])
        handler.addQuickElement(u"updated", rfc3339_date(self.latest_post_date()).decode('utf-8'))
        if self.feed['author_name'] is not None:
            handler.startElement(u"author", {})
            handler.addQuickElement(u"name", self.feed['author_name'])
            if self.feed['author_email'] is not None:
                handler.addQuickElement(u"email", self.feed['author_email'])
            if self.feed['author_link'] is not None:
                handler.addQuickElement(u"uri", self.feed['author_link'])
            handler.endElement(u"author")
        if self.feed['subtitle'] is not None:
            handler.addQuickElement(u"subtitle", self.feed['subtitle'])
        for cat in self.feed['categories']:
            handler.addQuickElement(u"category", "", {u"term": cat})
        if self.feed['feed_copyright'] is not None:
            handler.addQuickElement(u"rights", self.feed['feed_copyright'])

    def write_items(self, handler):
        for item in self.items:
            handler.startElement(u"entry", self.item_attributes(item))
            self.add_item_elements(handler, item)
            handler.endElement(u"entry")

    def add_item_elements(self, handler, item):
        handler.addQuickElement(u"title", item['title'])
        handler.addQuickElement(u"link", u"", {u"href": item['link'], u"rel": u"alternate"})
        if item['pubdate'] is not None:
            handler.addQuickElement(u"updated", rfc3339_date(item['pubdate']).decode('utf-8'))

        # Author information.
        if item['author_name'] is not None:
            handler.startElement(u"author", {})
            handler.addQuickElement(u"name", item['author_name'])
            if item['author_email'] is not None:
                handler.addQuickElement(u"email", item['author_email'])
            if item['author_link'] is not None:
                handler.addQuickElement(u"uri", item['author_link'])
            handler.endElement(u"author")

        # Unique ID.
        if item['unique_id'] is not None:
            unique_id = item['unique_id']
        else:
            unique_id = get_tag_uri(item['link'], item['pubdate'])
        handler.addQuickElement(u"id", unique_id)

        # Summary.
        if item['description'] is not None:
            handler.addQuickElement(u"summary", item['description'], {u"type": u"html"})

        # Enclosure.
        if item['enclosure'] is not None:
            handler.addQuickElement(u"link", '',
                {u"rel": u"enclosure",
                 u"href": item['enclosure'].url,
                 u"length": item['enclosure'].length,
                 u"type": item['enclosure'].mime_type})

        # Categories.
        for cat in item['categories']:
            handler.addQuickElement(u"category", u"", {u"term": cat})

        # Rights.
        if item['item_copyright'] is not None:
            handler.addQuickElement(u"rights", item['item_copyright'])

# This isolates the decision of what the system default is, so calling code can
# do "feedgenerator.DefaultFeed" instead of "feedgenerator.Rss201rev2Feed".
DefaultFeed = Atom1Feed

### Dependencies

import types
from xml.sax.saxutils import XMLGenerator
from decimal import Decimal
import urllib

class SimplerXMLGenerator(XMLGenerator):
    def addQuickElement(self, name, contents=None, attrs=None):
        "Convenience method for adding an element with no children"
        if attrs is None: attrs = {}
        self.startElement(name, attrs)
        if contents is not None:
            self.characters(contents)
        self.endElement(name)

def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and is_protected_type(s):
        return s
    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = ' '.join([force_unicode(arg, encoding, strings_only,
                            errors) for arg in s])
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        if not isinstance(s, Exception):
            raise DjangoUnicodeDecodeError(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_unicode(arg, encoding, strings_only,
                    errors) for arg in s])
    return s

def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_unicode(strings_only=True).
    """
    return isinstance(obj, (
        types.NoneType,
        int, long,
        datetime.datetime, datetime.date, datetime.time,
        float, Decimal)
    )

class DjangoUnicodeDecodeError(UnicodeDecodeError):
    def __init__(self, obj, *args):
        self.obj = obj
        UnicodeDecodeError.__init__(self, *args)

    def __str__(self):
        original = UnicodeDecodeError.__str__(self)
        return '%s. You passed in %r (%s)' % (original, self.obj,
                type(self.obj))


def iri_to_uri(iri):
    """
    Convert an Internationalized Resource Identifier (IRI) portion to a URI
    portion that is suitable for inclusion in a URL.

    This is the algorithm from section 3.1 of RFC 3987.  However, since we are
    assuming input is either UTF-8 or unicode already, we can simplify things a
    little from the full method.

    Returns an ASCII string containing the encoded result.
    """
    # The list of safe characters here is constructed from the "reserved" and
    # "unreserved" characters specified in sections 2.2 and 2.3 of RFC 3986:
    #     reserved    = gen-delims / sub-delims
    #     gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    #     sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
    #                   / "*" / "+" / "," / ";" / "="
    #     unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # Of the unreserved characters, urllib.quote already considers all but
    # the ~ safe.
    # The % character is also added to the list of safe characters here, as the
    # end of section 3.1 of RFC 3987 specifically mentions that % must not be
    # converted.
    if iri is None:
        return iri
    return urllib.quote(smart_str(iri), safe="/#%[]=:;$&()+,!?*@'~")

def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if isinstance(s, Promise):
        return unicode(s).encode(encoding, errors)
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s
