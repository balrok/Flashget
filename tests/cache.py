import unittest
import flashget.log
flashget.log.dummy = 0 # for pylint
import logging
import flashget.cache as cache
log = logging.getLogger()
import tempfile

class FileCacheTests(unittest.TestCase):
    def CheckAll(self):
        tmp_folder = tempfile.mkdtemp()
        self.cache = cache.FileCache([tmp_folder, "sub1", "sub2"])
        # mkdtemp should make a completely new dir for us so create_path is true
        self.assertTrue(self.cache.create_path)

        # both are always the same
        self.assertEqual(self.cache.path, self.cache.key)

        # test getting path without creating it
        path = self.cache.get_path('test', False)
        self.assertIsNone(path)
        self.assertTrue(self.cache.create_path)

        path = self.cache.get_path('test', True)
        self.assertFalse(self.cache.create_path)
        self.assertIsNotNone(path)

        test_created = cache.FileCache([tmp_folder, "sub1", "sub2"])
        self.assertFalse(test_created.create_path)

        self.assertIsNone(self.cache.lookup("notexists"))


def suite():
    filecache_suite = unittest.makeSuite(FileCacheTests, "Check")
    return unittest.TestSuite((filecache_suite))

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == "__main__":
    test()
