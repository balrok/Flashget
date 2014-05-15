import unittest
import flashget.log
flashget.log.dummy = 0 # for pylint
import logging
from flashget.url import UrlMgr
log = logging.getLogger()

class UrlMgrTests(unittest.TestCase):
    def CheckCookies(self):
        # checking once for post and once for get
        url = UrlMgr(url='http://httpbin.org/cookies/set/sessioncookie/123456789', nocache=True)
        cookieData = url.data
        self.assertGreater(cookieData.find("123456789"), 1, "the cookie wasn't correctly set")
        url = UrlMgr(url="http://httpbin.org/cookies", nocache=True)
        self.assertEquals(cookieData, url.data)
        url = UrlMgr(url="http://httpbin.org/cookies", postdata='ads=asd', nocache=True)
        self.assertEquals(cookieData, url.data)

def suite():
    urlmgr_suite = unittest.makeSuite(UrlMgrTests, "Check")
    return unittest.TestSuite((urlmgr_suite))

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
