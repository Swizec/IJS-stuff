
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from datetime import datetime

class AtomFeedManager(models.Manager):
    def get(self, path, *args, **kwargs):
        try:
            feed = super(AtomFeedManager, self).get(path=path, *args, **kwargs)
            needs_update = (datetime.now()-feed.time) > settings.MAX_FEED_AGE
        except ObjectDoesNotExist:
            feed = super(AtomFeedManager, self).create(path=path)
            needs_update = True

        if needs_update:
            feed.update()

        return feed
        
