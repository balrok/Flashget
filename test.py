import unittest
from tests.stream import suite as streamSuite
from tests.cache import suite as cacheSuite
import tools.log
tools.log.dummy = 0 # for pylint

def test():
    runner = unittest.TextTestRunner()
    runner.run(streamSuite())
    runner.run(cacheSuite())

if __name__ == "__main__":
    test()
