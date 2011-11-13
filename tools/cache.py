import config
import re
import os
import logging

log = logging.getLogger('urlCache')

FILENAME_MAX_LENGTH = 100 # maxlength of filenames
class FileCache(object):
    def __init__(self, dir, subdirs = [], log = None):
        ''' subdirs must be an array '''
        self.log = config.logger['urlCache']
        for i in xrange(0, len(subdirs)):
            dir = os.path.join(dir, self.create_filename(subdirs[i]))
        self.path = dir
        # create the path only if we write something there, thats why those variables getting set
        if os.path.isdir(self.path) is False:
            self.create_path = True
        else:
            self.create_path = False

    @staticmethod
    def create_filename(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def get_path(self, section, create = False):
        if self.create_path:
            if create:
                try:
                    os.makedirs(self.path)
                except:
                    pass
            else:
                return None
        self.create_path = False
        return os.path.join(self.path, section)

    def lookup(self, section):
        file = self.get_path(section)
        if file and os.path.isfile(file):
            self.log.debug('using cache [%s] path: %s' % (section, file))
            f = open(file, 'r')
            return ''.join(f.readlines())
        return None

    def lookup_size(self, section):
        file = self.get_path(section)
        if file and os.path.isfile(file):
            return os.path.getsize(file)
        return None

    def read_stream(self, section):
        file = self.get_path(section)
        if file:
            return open(file, 'rb')
        return None

    def truncate(self, section, x):
        file = self.get_path(section)
        if file:
            a = open(file, 'r+b')
            a.truncate(x)

    def get_stream(self, section):
        file = self.get_path(section, True)
        return open(file, 'wb')

    def get_append_stream(self, section):
        file = self.get_path(section, True)
        return open(file, 'ab')

    def write(self, section, data):
        file = self.get_path(section, True)
        open(file, 'w').writelines(data)



Cache = FileCache

try:
    from kyotocabinet import *
finally:
    dbList = {}
    class KyotoCache(object):
        def __init__(self, dir, subdirs = [], log = None):
            if dir not in dbList:
                dbList[dir] = DB()
                dbList[dir].open(dir+".kch", DB.OWRITER | DB.OCREATE | DB.OAUTOSYNC)
            self.db = dbList[dir]
            self.key = "/".join(subdirs)

        def lookup(self, section):
            ret = self.db.get(self.key+"/"+section)
            return ret

        def lookup_size(self, section):
            raise Exception
        def read_stream(self, section):
            raise Exception
        def truncate(self, section, x):
            raise Exception
        def get_stream(self, section):
            raise Exception
        def get_append_stream(self, section):
            raise Exception

        def write(self, section, data):
            self.db.set(self.key+"/"+section, data)

    Cache = KyotoCache


if config.cachePort:
    from socket import *
    import pickle

    HOST = 'localhost'
    PORT = config.cachePort
    ADDR = (HOST,PORT)

    # we have a cacheserver - write a client for it
    class CacheClient(object):
        def __init__(self, dir, subdirs = [], log = None):
            self.dir = dir
            self.key = "/".join(subdirs)

        def lookup(self, section):
            return self.sendRecv('lookup', section)
        def write(self, section, data):
            return self.sendRecv('write', section, data)

        def sendRecv(self, command, section, value=''):
            s = socket(AF_INET,SOCK_STREAM)
            s.connect((ADDR))
            data = pickle.dumps({'c':command,'k':self.key,'section':section,'d':self.dir,'v':value})
            size = str(len(data))
            size += (8-len(size))*" "
            try:
                s.send(size+data)
            except:
                print data
            retdata = ''
            if command == 'lookup':
                size = int(s.recv(8).rstrip())
                if size:
                    retdata = ''
                    while size > 0:
                        chunk = s.recv(size)
                        if chunk == '':
                            break
                        retdata += chunk
                        size -= len(chunk)
                    try:
                        retdata = pickle.loads(retdata)
                    except:
                        print retdata
                else:
                    retdata = None
            s.close()
            return retdata

    Cache = CacheClient
