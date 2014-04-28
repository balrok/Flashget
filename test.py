import unittest
from tests.stream import suite as streamSuite
from tests.cache import suite as cacheSuite
from tests.page import suite as pageSuite
from tests.urlmgr import suite as urlmgrSuite
import tools.log
tools.log.dummy = 0 # for pylint

def test():
    runner = unittest.TextTestRunner()
    runner.run(pageSuite())
    runner.run(streamSuite())
    runner.run(cacheSuite())
    runner.run(urlmgrSuite())

if __name__ == "__main__":
    test()
