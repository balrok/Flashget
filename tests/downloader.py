import unittest
import logging
import tempfile
import os

from .testHelper import fix_sys_path, setUpModule, tearDownModule

fix_sys_path()

import flashget.log
flashget.log.dummy = 0 # for pylint
from flashget.downloader import Downloader
from flashget.stream import VideoInfo
log = logging.getLogger()
from flashget.url import LargeDownload
LargeDownload.default_base_cache_dir = tempfile.mkdtemp()


class DownloaderTests(unittest.TestCase):
    def CheckDownloader(self):
        downloader = Downloader(1)

        pinfo = VideoInfo('http://www.movshare.net/video/af6huuwg14nqo')
        pinfo.name = "testname"
        pinfo.title = "testtiel"

        cacheFolder = tempfile.mkdtemp()
        downloadPath = os.path.join(cacheFolder, pinfo.subdir, pinfo.title + ".flv")
        downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])
        # normally downloader.run() must be called - but I don't want to run it endlessly here
        # so call this method and shortly after stop the downloading
        downloader.downloadQueueProcessing()
        self.assertEqual(len(downloader.current_downloads), 1)
        # TODO dynamic sleeping
        # TODO make a teardown method - so the assert here won't stop the call to end()
        import time
        time.sleep(3)
        def testDownloads(dl):
            self.assertGreaterEqual(dl['url'].downloaded, 5)
            dl['url'].end()
        downloader.iterateCurrentDownloads(testDownloads)
        # TODO - do some checks
        self.assertTrue(True)

def suite():
    tests = []
    tests.append(unittest.makeSuite(DownloaderTests, "Check"))
    return unittest.TestSuite(tests)

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == '__main__':
    setUpModule()       # pre-python-2.7
    test()
    tearDownModule()
