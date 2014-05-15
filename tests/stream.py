import unittest
import flashget.log
flashget.log.dummy = 0 # for pylint
import logging
from flashget.stream import VideoInfo, getStreamByLink
import tempfile
import time
import os
log = logging.getLogger()

class StreamTests(unittest.TestCase):
    def getHandler(self, link):
        streamHandler = getStreamByLink(link)
        return streamHandler()

    def CheckLink(self):
        log.info("%s.CheckLink", self.__class__.__name__)
        streamHandler = self.getHandler(self.link)
        self.assertEqual(streamHandler.__class__.__name__, self.className)

    def CheckId(self):
        log.info("%s.CheckId", self.__class__.__name__)
        streamHandler = self.getHandler(self.link)
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
        streamHandler = self.getHandler(self.link)
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

        data = ''.ld.cache.read_stream('data').readlines()
        data2 = ''.ld2.cache.read_stream('data').readlines()
        log.info("comparing resumed download with %d in size", secondSize)
        self.assertEquals(data, data2[:secondSize])

class FiredriveTests(StreamTests):
    link = 'http://www.firedrive.com/file/6D7CC4DA175C7E76'
    linkId = '6D7CC4DA175C7E76'
    className = 'FireDrive'
    size = 146445261

class StreamcloudTests(StreamTests):
     link = 'http://streamcloud.eu/h0q5dfftfcep/Doctor.Who.S05E02.Der.Sternenwal.German.Dubbed.BDRip.XviD-ITG.avi.html'
     linkId = 'h0q5dfftfcep'
     className = 'Streamcloud'
     size = 136181347

class NowvideoTests(StreamTests):
    link = 'http://www.nowvideo.sx/video/5t9jwbb8qi41r'
    linkId = '5t9jwbb8qi41r'
    className = 'Nowvideo'
    size = 306894288

class VideoweedTests(StreamTests):
    link = 'http://www.videoweed.es/file/u97jjkitq3l9v'
    linkId = 'u97jjkitq3l9v'
    className = 'Videoweed'
    size = 223645836

class MovshareTests(StreamTests):
    link = 'http://www.movshare.net/video/af6huuwg14nqo'
    linkId = 'af6huuwg14nqo'
    className = 'Movshare'
    size = 160135435

def suite():
    tests = []
    tests.append(unittest.makeSuite(FiredriveTests, "Check"))
    # streamcloud is blocked for usa ip addresses - I don't want to see this error allways
    if 'TRAVIS' not in os.environ:
        tests.append(unittest.makeSuite(StreamcloudTests, "Check"))
    tests.append(unittest.makeSuite(NowvideoTests, "Check"))
    tests.append(unittest.makeSuite(VideoweedTests, "Check"))
    tests.append(unittest.makeSuite(MovshareTests, "Check"))
    return unittest.TestSuite(tests)

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
