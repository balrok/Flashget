import re
import os
import logging

log = logging.getLogger(__name__)

from .helper import open

FILENAME_MAX_LENGTH = 100 # maxlength of filenames
# the filecache has also some additional interface methods
class FileCache(object):
    create_path = False
    path = ""
    key = ""
    def __init__(self, keys):
        ''' subdirs must be an array '''
        directory = keys[0]
        for i in range(1, len(keys)):
            directory = os.path.join(directory, self.create_filename(keys[i]))
        self.path = directory
        self.key = directory
        # create the path only if we write something there, thats why those variables getting set
        if os.path.isdir(self.path) is False:
            self.create_path = True

    @staticmethod
    def create_filename(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def get_path(self, section='', create = False):
        if self.create_path:
            if create:
                try:
                    os.makedirs(self.path)
                except OSError:
                    pass
                else:
                    self.create_path = False
            else:
                return None
        return os.path.join(self.path, section)

    def remove(self, section):
        filePath = self.get_path(section)
        if filePath and os.path.isfile(filePath):
            os.remove(filePath)
        else:
            raise Exception("We never create directories %s" % filePath)
            # import shutil
            # shutil.rmtree(filePath)

    def lookup(self, section):
        filePath = self.get_path(section)
        if filePath and os.path.isfile(filePath):
            log.debug('using cache [%s] path: %s', section, filePath)
            with open(filePath, "r", encoding="utf-8") as f:
                return ''.join(f.readlines())
        return None

    def lookup_size(self, section):
        filePath = self.get_path(section)
        if filePath and os.path.isfile(filePath):
            return os.path.getsize(filePath)
        return None

    def read_stream(self, section):
        filePath = self.get_path(section)
        if filePath:
            return open(filePath, 'rb')
        return None

    def truncate(self, section, x):
        filePath = self.get_path(section)
        if filePath:
            a = open(filePath, 'r+b')
            a.truncate(x)

    def get_stream(self, section):
        filePath = self.get_path(section, True)
        return open(filePath, 'wb')

    def get_append_stream(self, section):
        filePath = self.get_path(section, True)
        return open(filePath, 'ab')

    def write(self, section, data):
        filePath = self.get_path(section, True)
        with open(filePath, 'w', encoding='utf-8') as f:
            f.write(data)

