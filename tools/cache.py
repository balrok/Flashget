import config
import re
import os
import logging

log = logging.getLogger('urlCache')


class BaseCache(object): # interface for all my caches
    def allKeys(self):
        return []
    def remove(self, section):
        pass
    def lookup(self, section):
        return None
    def write(self, section, data):
        pass
    def allKeys(self):
        return [i for i in self.iterKeys()]
    def iterKeys(self):
        for i in self.iterKeyValues():
            yield i[0]
    def iterKeyValues(self):
        yield None
    def count(self):
        c = 0
        for i in self.iterKeys():
            c+=1
        return c


FILENAME_MAX_LENGTH = 100 # maxlength of filenames
# the filecache has also some additional interface methods
class FileCache(BaseCache):
    def __init__(self, dir, subdirs = [], log = None):
        ''' subdirs must be an array '''
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

    def iterKeys(self):
        import os
        import sys
        for root, subFolders, files in os.walk(self.path):
            cleanRoot = root.replace(self.path+'/', '')
            for file in files:
                yield os.path.join(cleanRoot, file)
    def iterKeyValues(self):
        import os
        import sys
        for root, subFolders, files in os.walk(self.path):
            cleanRoot = root.replace(self.path+'/', '')
            for file in files:
                f = os.path.join(cleanRoot, file)
                yield (f, open(self.path+"/"+f, 'r').readlines())

    def remove(self, section):
        raise Exception("TODO implement")

    def lookup(self, section):
        file = self.get_path(section)
        if file and os.path.isfile(file):
            log.debug('using cache [%s] path: %s' % (section, file))
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



# below this i define several database caches - so they don't support append_stream and so on.. i won't store so big data inside

try:
    from kyotocabinet import *
except:
    config.cachePort = 0
    pass
else:
    dbList = {}
    class KyotoCache(BaseCache):
        def __init__(self, dir, subdirs = [], log = None):
            if dir not in dbList:
                dbList[dir] = DB()
                dbList[dir].open(dir+".kch", DB.OWRITER | DB.OCREATE)
            self.db = dbList[dir]
            self.key = "/".join(subdirs)
        def lookup(self, section):
            ret = self.db.get(self.key+"/"+section)
            return ret
        def write(self, section, data):
            self.db.set(self.key+"/"+section, data)
        def remove(self, section):
            self.db.remove(self.key+"/"+section)
        def iterKeys(self):
            for i in self.db:
                yield i
        def iterKeyValues(self):
            cur = self.db.cursor()
            cur.jump()
            def printproc(key, value):
                return Visitor.NOP
            while cur.accept(printproc):
                cur.step()
                yield (cur.get_key(), cur.get_value())
        def count(self):
            return self.db.count()


    Cache = KyotoCache

    class KyotoCacheComp(KyotoCache): # with compression
        def __init__(self, dir, subdirs = [], log = None):
            dir+="_zlib"
            if dir not in dbList:
                dbList[dir] = DB()
                dbList[dir].open(dir+".kch#ops=c#zcomp=zlib", DB.OWRITER | DB.OCREATE)
            self.db = dbList[dir]
            self.key = "/".join(subdirs)

try:
    import lib.leveldb as leveldb
except:
    config.cachePort = 0
    pass
else:
    dbList = {}
    class LevelCache(object):
        def __init__(self, dir, subdirs = [], log = None):
            if dir not in dbList:
                dbList[dir] = leveldb.LevelDB(dir)
            self.db = dbList[dir]
            self.key = "/".join(subdirs)

        def lookup(self, section):
            ret = self.db.Get(self.key+"/"+section)
            return ret
        def write(self, section, data):
            self.db.Put(self.key+"/"+section, data)
        def remove(self, section):
            self.db.Delete(self.key+"/"+section)

        def iterKeys(self):
            for i in self.db.RangeIter(include_value=False):
                yield i
        def iterKeyValues(self):
            for i in self.db.RangeIter():
                yield i


if config.cachePort:
    import socket
    import time
    import pickle

    HOST = 'localhost'
    PORT = config.cachePort
    ADDR = (HOST,PORT)

    conList = {}

    # we have a cacheserver - write a client for it
    class CacheClient(object):
        def __init__(self, dir, subdirs = []):
            self.dir = dir
            self.setKey(subdirs)
            if self.dir not in conList:
                self.connect()
                conList[self.dir] = self.c
            self.c = conList[self.dir]

        def connect(self):
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            for i in range(60):
                try:
                    s.connect((ADDR))
                except:
                    time.sleep(1)
                    log.warning("couldn't connect to cache server")
                else:
                    break
            self.c = s

        def setKey(self, subdirs = []):
            self.key = "/".join(subdirs)

        def lookup(self, section):
            return self.sendRecv('lookup', section)
        def remove(self, section):
            return self.sendRecv('remove', section)
        def write(self, section, data):
            return self.sendRecv('write', section, data)
        def allKeys(self):
            return self.sendRecv('allkeys')
        def iterKeys(self):
            allKeys = self.allKeys()
            for i in allKeys:
                yield i
        def iterKeyValues(self):
            raise Exception("can't be used over a connection since it will stream too much data - sorry")

        sendRecvCalls = 0
        def sendRecv(self, command, section, value=''):
            try:
                data = pickle.dumps({'c':command,'k':self.key,'section':section,'d':self.dir,'v':value}, 1)
                data=data
                size = str(len(data))
                size += (8-len(size))*" "
                self.c.sendall(size+data)
                retdata = ''
                if command in ('lookup', 'allkeys'):
                    size = int(self.c.recv(8).rstrip())
                    if not size:
                        raise socket.error(0, "no size")
                    retdata = ''
                    while size > 0:
                        chunk = self.c.recv(size)
                        if chunk == '':
                            raise socket.error(0, "received empty chunk but still data left")
                        retdata += chunk
                        size -= len(chunk)
                    retdata = pickle.loads(retdata)
                self.sendRecvCalls = 0 # reset retrys
                return retdata
            except socket.error, e:
                log.error("socketerror "+str(e))
                self.connect()
                self.sendRecvCalls+=1
                if self.sendRecvCalls < 2: # just one retry
                    log.warning("retry sendRecv")
                    return self.sendRecv(command, section, value)
                log.error("abort sendRecv")
                return None

    Cache = CacheClient
