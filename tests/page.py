# -*- coding: utf-8 -*-
import unittest
import tools.log
tools.log.dummy = 0 # for pylint
import logging
from tools.page import pages
log = logging.getLogger()

class PageTests(unittest.TestCase):
    def getHandler(self, link):
        pageHandler = pages.getExtensionByRegexStringMatch(link)
        return pageHandler()

    def CheckLink(self):
        log.info("%s.CheckLink", self.__class__.__name__)
        streamHandler = self.getHandler(self.link)
        self.assertEqual(streamHandler.__class__.__name__, self.className)

    def CheckMedia(self):
        log.info("%s.CheckMedia", self.__class__.__name__)
        pageHandler = self.getHandler(self.link)
        media = pageHandler.get(self.link) # returns array of medias (extractAll) or just one media (download)
        self.assertEqual(media.name.encode("utf-8"), self.mediaName)
        self.assertEqual(len(media.getSubs()), self.partAmount)
        part = media.getSubs()[self.lookPart]
        self.assertEqual(part.name.encode("utf-8"), self.partName)
        # print media.__str__().encode("utf-8")



class DdlMe_Movie_Tests(PageTests):
    link = 'http://de.ddl.me/manche-moegens-hei-deutsch-stream-download_0_10654.html'
    className = 'SingleDdlMeExtension'
    mediaName = "Manche mögens heiß (1959)"
    # a single movie should always be 1
    partAmount = 1
    # specify here at which part we should look more closely
    lookPart = 0
    # and partName should always be that of the movie
    partName = "Manche mögens heiß (1959)"

class DdlMe_TVShow_Tests(PageTests):
    link = 'http://de.ddl.me/cowboy-bebop-deutsch-stream-download_1_20746.html'
    className = 'SingleDdlMeExtension'
    mediaName = "Cowboy Bebop (1998)"
    partAmount = 26
    # specify here at which part we should look more closely
    lookPart = 0
    partName = "Der Machtkampf"

def suite():
    tests = []
    tests.append(unittest.makeSuite(DdlMe_Movie_Tests, "Check"))
    tests.append(unittest.makeSuite(DdlMe_TVShow_Tests, "Check"))
    return unittest.TestSuite(tests)

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()



