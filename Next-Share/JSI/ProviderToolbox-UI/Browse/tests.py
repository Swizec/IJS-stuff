
from django.test import TestCase
from django.conf import settings

import os

class BasicTest(TestCase):
    def test_begin(self):
        response = self.client.get('/')

        self.assertEquals(response.status_code, 200)
        self.assert_("<body>" in response.content)

    def test_list_root(self):
        response = self.client.get('/list_dir/', {'dir': '/'})

        self.assertEquals(response.status_code, 200)

        for feed in os.listdir(settings.FEED_DIR):
            if ".properties" in os.listdir(settings.FEED_DIR+feed):
                self.assert_(response.content.find(feed) >= 0)

    def test_list(self):
        feed = os.listdir(settings.FEED_DIR)[0]

        response = self.client.get('/list_dir/',
                                   {'dir': feed})

        self.assertEquals(response.status_code, 200)

        for f in os.listdir(settings.FEED_DIR+feed):
            if f.endswith('.xml'):
                self.assert_(response.content.find(f) >= 0)
