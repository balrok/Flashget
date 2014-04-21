import unittest
from tools.stream import VideoInfo, flashExt
import tempfile
import time

class StreamTests(unittest.TestCase):
    def getHandler(self, link):
        streamHandler = flashExt.getExtensionByRegexStringMatch(link)
        return streamHandler()

    def CheckLink(self):
        streamHandler = self.getHandler(self.link)
        self.assertEqual(streamHandler.__class__.__name__, self.className)

    def CheckId(self):
        streamHandler = self.getHandler(self.link)
        videoInfo = VideoInfo(self.link)
        self.assertEqual(streamHandler.get(videoInfo, True), self.linkId)

    def CheckDownload(self):
        streamHandler = self.getHandler(self.link)
        videoInfo = VideoInfo(self.link)
        flvUrl = streamHandler.get(videoInfo)
        print(flvUrl)
        ld = streamHandler.download(cache_folder=tempfile.mkdtemp())
        self.assertEqual(ld.size, self.size)
        ld.start()
        time.sleep(1)
        ld.end()
        self.assertGreaterEqual(ld.downloaded, 500)

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

def suite():
    firedrive_suite = unittest.makeSuite(FiredriveTests, "Check")
    streamcloud_suite = unittest.makeSuite(StreamcloudTests, "Check")
    nowvideo_suite = unittest.makeSuite(NowvideoTests, "Check")
    return unittest.TestSuite((firedrive_suite, streamcloud_suite, nowvideo_suite))

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
