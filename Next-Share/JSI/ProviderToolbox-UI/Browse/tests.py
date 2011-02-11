
from django.test import TestCase
from django.conf import settings

import os

class BasicTest(TestCase):
    def test_begin(self):
        response = self.client.get('/')

        self.assertEquals(response.status_code, 200)
        self.assert_("<body>" in response.content)

    def test_list(self):
        feed = os.listdir(settings.FEED_DIR)[0]

        html = self.client.get('/list_dir/',
                               {'dir': feed}).content

        for f in os.listdir(settings.FEED_DIR+feed):
            if f.endswith('.xml'):
                self.assert_(html.find(f) >= 0)
