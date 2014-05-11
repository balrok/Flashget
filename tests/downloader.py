import unittest
import logging
import tempfile
import os

from testHelper import fix_sys_path, setUpModule, tearDownModule

fix_sys_path()

import tools.log
tools.log.dummy = 0 # for pylint
from tools.downloader import Downloader
from tools.stream import VideoInfo
log = logging.getLogger()


class DownloaderTests(unittest.TestCase):
    def CheckDownloader(self):
        downloader = Downloader(1)
        pinfo = VideoInfo('http://www.movshare.net/video/af6huuwg14nqo')
        pinfo.name = "testname"
        pinfo.title = "testtiel"
        cacheFolder = tempfile.mkdtemp()
        downloadPath = os.path.join(cacheFolder, pinfo.subdir, pinfo.title + ".flv")
        pinfo.stream.get(pinfo) # call this, so flvUrl is set inside stream
        downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])
        downloader.run()
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
