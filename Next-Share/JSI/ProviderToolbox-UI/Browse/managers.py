
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from datetime import datetime

class AtomFeedManager(models.Manager):
    def get(self, path, *args, **kwargs):
        try:
            feed = super(AtomFeedManager, self).get(path=path, *args, **kwargs)
        except ObjectDoesNotExist:
            feed = super(AtomFeedManager, self).create(path=path)

        if (datetime.now()-feed.time).days > settings.MAX_FEED_AGE:
            feed.update()

        if feed.feed == '':
            feed.refetch()

        return feed
        
