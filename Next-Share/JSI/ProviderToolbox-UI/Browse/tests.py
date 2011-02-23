
# -*- coding: utf-8 -*-

from django.test import TestCase
from django.conf import settings

import os, time

# manjkajo še testi za odstranitev vsebine ter odstranitev vira.

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

    def test_create(self):
        feed = 'test_feed-%d' % time.time()
        response = self.client.post('/create_feed/',
                                    {'title': feed,
                                     'description': 'blah test',
                                     'originator': 'A test',
                                     'publisher': 'Also a test',
                                     'language': 'en'})
        
        self.assertEquals(response.status_code, 302)

        self.assert_(feed in os.listdir(settings.FEED_DIR))
        # Lahko bi še preveril, če direktorij dejansko obstaja, ter da
        # so lastnosti vira take, kot se je določilo


    def test_update(self):
        # TODO: wasn't sure how to make an actual test

        # Lahko preveriš, če se je getfeed uspešno izvedel, dobro bi
        # bilo videti, če se je dodalo kaj vsebine in kdaj je bil
        # izvedeno zadnje osveževanje vira. Pogledam, kako lahko
        # zagotovim nekaj več informacije o tem

        feed = os.listdir(settings.FEED_DIR)[0]

        response = self.client.get('/update_feed/',
                                    {'path': feed})

        self.assertEquals(response.status_code, 200)

    def test_add_item(self):
        # TODO: wasn't sure how to make an actual test

        # preveriti je treba, če je bila vsebina doddana, ter da sta
        # bili narejeni datoteka z metapodatki in torrent datoteka. Je
        # vsebina dejansko taka, kot je bila podana?

        feed = os.listdir(settings.FEED_DIR)[0]

        response = self.client.post('/add_item/',
                                    {'feed_dir': feed,
                                     'file': '/some/random/file',
                                     'synopsis': 'A short synopsis',
                                     'title': 'File title!'})

        self.assertEquals(response.status_code, 302)
