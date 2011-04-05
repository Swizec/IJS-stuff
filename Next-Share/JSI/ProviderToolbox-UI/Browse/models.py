from django.db import models
from django.http import QueryDict

import urllib

from managers import AtomFeedManager
from forms import PathForm
from lib import talk_to_cli as cli

# Create your models here.
class AtomFeed(models.Model):
    time = models.DateTimeField(auto_now=True)
    feed = models.TextField()
    path = models.CharField(max_length=255)

    objects = AtomFeedManager()

    def update(self):
        form = PathForm(QueryDict(urllib.urlencode({'path': self.path})))
        if form.is_valid():
            (so,se,rv) = cli.update_feed(form)
            if rv == 0:
                self.feed = so
                self.save()
            else:
                raise Exception(se)
        else:
            raise Exception("This should never happen!")
