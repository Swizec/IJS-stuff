from django.db import models

# Create your models here.
class AtomFeed(models.Model):
    time = models.DateTimeField(auto_now=True)
    feed = models.TextField()
    path = models.CharField(max_length=255);
