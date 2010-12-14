import os
import unittest
import time

from JSI.ProviderToolbox.Publisher import Publisher, UpdateService
from JSI.ProviderToolbox.ContentSource import Channel
from JSI.ProviderToolbox.utils import log 
from JSI.ProviderToolbox.conf import settings

# Import after the JSI imports so the logging gets properly
# initialized
from BaseLib.Core.Session import *
from BaseLib.Core.SessionConfig import *
from BaseLib.Core.DownloadConfig import DownloadStartupConfig

_log = log.getLog('TestPublisher')
log.setLevel(log.DEBUG)

class TestPublisher(unittest.TestCase):
    """ 
    Test framework for testing a publisher (seeder)
    """
    data = None
    
    alpha = "ABCDEFGHIJKLMNOPRSTUXYWZ"
    test_counter = 0
    run_test = True
    tests = {"A": False, #testAStartStopSeeder
             "B": False, #testBAddContent
             "C": True, #testCUpdate
             }

    def setUp(self):
        """ Set up method """
        if not TestPublisher.tests.get(TestPublisher.alpha[TestPublisher.test_counter]):
            TestPublisher.run_test = False
        TestPublisher.test_counter += 1


    def tearDown(self):
        """ Tear down method """
        TestPublisher.run_test = True

    def testAStartSeeder(self):
        _log.info("Start seeder ------------")
        if not TestPublisher.run_test:
            _log.debug("Test avoided.")
            return
        seeder = Publisher.getInstance()
        seeder.start()
        tclear = list()
        if os.path.isdir(settings.TORRENT_DIRECTORY):
            tlist = os.listdir(settings.TORRENT_DIRECTORY)
            for t in tlist:
                if t.endswith('tstream') or t.endswith('url'):
                    tclear.append(t)
        pubs = len(seeder.publications)
        seeder.stop()
        self.assertTrue(len(tclear) == pubs)

    def testBAddRemoveContent(self):
        _log.info("Add/remove content ------------")
        _log.info("The test will sleep few times to give Next-Share enough time to recover from changes")
        if not TestPublisher.run_test:
            _log.debug("Test avoided.")
            return
        seeder = Publisher.getInstance()
        seeder.start()
        oldseeds = len(seeder.publications)
        # Get something new
        channel = Channel.getContentSource("http://www.rtvslo.si/podcasts/slovencem_po_svetu.xml")
        items1 = len(channel.items)
        seeder.update()
        time.sleep(5)
        seeds1 = len(seeder.publications)
        # Remove an item
        i = None
        for k in channel.items:
            i = k
            break
        if i != None:
            channel.removeContentUnit(i)
        seeder.update()
        time.sleep(5)
        seeds2 = len(seeder.publications)
        channel.update()
        # just to be sure
        items2 = len(channel.items)
        seeder.update()
        time.sleep(5)
        seeds3 = len(seeder.publications)
        channel.remove()
        time.sleep(5)
        seeder.update()
        seeds4 = len(seeder.publications)
        seeder.stop()
        self.assertTrue(seeds1 == oldseeds + items1)
        self.assertTrue(seeds2 == oldseeds + items1 - 1)
        self.assertTrue(seeds3 == oldseeds + items2)
        self.assertTrue(seeds4 == oldseeds)

    def testCUpdate(self):
        _log.info("Update ------------")
        if not TestPublisher.run_test:
            _log.debug("Test avoided.")
            return
        seeder = Publisher.getInstance()
        seeder.start()
        update = UpdateService.getInstance(getattr(seeder, "update"))
        update.start()
        time.sleep(70)
        update.stop()
        seeder.stop()

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestPublisher)

if __name__ == "__main__":
    unittest.main()


