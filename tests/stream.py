import unittest
import logging
import tempfile
import time
log = logging.getLogger()
from testHelper import fix_sys_path, setUpModule, tearDownModule
fix_sys_path()
import flashget.log
flashget.log.dummy = 0 # for pylint
from flashget.stream import VideoInfo, getStreamByLink, flashExt

class StreamTests(unittest.TestCase):
    def CheckLink(self):
        log.info("%s.CheckLink", self.__class__.__name__)
        streamHandler = getStreamByLink(self.link)
        self.assertEqual(streamHandler.__class__.__name__, self.className)

    def CheckId(self):
        log.info("%s.CheckId", self.__class__.__name__)
        streamHandler = getStreamByLink(self.link)
        self.assertEqual(streamHandler.getId(), self.linkId)


    def doDownload(self, largeDownloadHandler, size):
        largeDownloadHandler.start()
        for i in range(0,4):
            if largeDownloadHandler.downloaded > size:
                break
            time.sleep(1)
        largeDownloadHandler.end()
        self.assertGreaterEqual(largeDownloadHandler.downloaded, size)
        return largeDownloadHandler

    def CheckDownload(self):
        log.info("%s.CheckDownload", self.__class__.__name__)
        streamHandler = getStreamByLink(self.link)
        videoInfo = VideoInfo(self.link)
        flvUrl = videoInfo.stream.flvUrl
        # when return is None, it could not find the video
        self.assertIsNotNone(flvUrl)
        # the returned flvUrl must be set to the class too
        self.assertEqual(flvUrl, streamHandler.flvUrl)

        # now check the download
        cacheFolder = tempfile.mkdtemp()
        ld = streamHandler.download(cache_folder=cacheFolder)
        self.assertEqual(ld.size, self.size)
        ld = self.doDownload(ld, 100)
        firstSize = ld.downloaded

        # now check resume

        # 1. resume previous download
        ld = streamHandler.download(cache_folder=cacheFolder)
        ld = self.doDownload(ld, firstSize+100)
        secondSize = ld.downloaded

        # 2. create new download where the same size gets downloaded in one go
        cacheFolder2 = tempfile.mkdtemp()
        ld2 = streamHandler.download(cache_folder=cacheFolder2)
        ld2 = self.doDownload(ld2, secondSize)

        # TODO how to check downloadfiles (maybe comparing sha1)
        # data = ''.join(ld.cache.read_stream('data').readlines())
        # data2 = ''.join(ld2.cache.read_stream('data').readlines())
        # log.info("comparing resumed download with %d in size", secondSize)
        # self.assertEquals(data, data2[:secondSize])


def suite():
    tests = []

    # initialize flashExt
    getStreamByLink('')
    for stream in flashExt.extensions:
        try:
            stream.getTestData()
        except:
            print("%s has no tests" % stream.ename)
        else:
            testClass = type('{}Tests'.format(stream.ename), (StreamTests,), stream.getTestData())
            tests.append(unittest.makeSuite(testClass, "Check"))

    return unittest.TestSuite(tests)

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    setUpModule()       # pre-python-2.7
    test()
    tearDownModule()
