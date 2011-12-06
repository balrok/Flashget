import config
import re
import os
import logging
from tools.helper import *
import sys
import atexit

log = logging.getLogger('urlCache')


# contains a list of {'class'..,'check'..,'noDefault'} where class is the cacheclass and check is a function
# which decides if we use this specific cache. The decission is made based on configuration or wether a cache-folder/file
# already exists
# the last item in the list is the most important
# noDefault is a bool which defines if we should use this cache when no other caches match
cacheList = []


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
    def __repr__(self):
        return self.__class__.__name__+':'+self.key

def convertCache(fromCache, toCache):
    print "converting caches"
    from time import time
    allkeyLen = fromCache.count()
    i = 0
    startTime = time()
    for data in fromCache.iterKeyValues():
        key, value = data
        i += 1
        if i%1000==1:
            eta = calc_eta(startTime, allkeyLen, i)
            percent = calc_percent(i, allkeyLen)
            print "%d of %d ETA: %s Percent %s\r" % (i, allkeyLen, eta, percent),
            sys.stdout.flush()
        keys = key.split("/")
        section = keys[-1][:]
        del keys[-1]
        toCache.key = '/'.join(keys)
        toCache.write(section, value)

FILENAME_MAX_LENGTH = 100 # maxlength of filenames
# the filecache has also some additional interface methods
class FileCache(BaseCache):
    def __init__(self, dir, subdirs = []):
        ''' subdirs must be an array '''
        for i in xrange(0, len(subdirs)):
            dir = os.path.join(dir, self.create_filename(subdirs[i]))
        self.path = dir
        self.key = dir
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
        for root, subFolders, files in os.walk(self.path):
            cleanRoot = root.replace(self.path+'/', '')
            for file in files:
                yield os.path.join(cleanRoot, file)
    def iterKeyValues(self):
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


def isFileCache(namespace):
    return os.path.isdir(namespace)
cacheList.append({'class':FileCache, 'check':isFileCache})


# below this i define several database caches - so they don't support append_stream and so on.. i won't store so big data inside

try:
    from kyotocabinet import *
except:
    config.cachePort = 0
    pass
else:
    dbList = {}

    @atexit.register
    def close():
        for dir in dbList:
            db = dbList[dir]
            db.close()

    class KyotoCache(BaseCache):
        def __init__(self, dir, subdirs = []):
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
            while True:
                cur.step()
                if cur.get_key() == None:
                    break
                yield (cur.get_key(), cur.get_value())
        def count(self):
            return self.db.count()

    def isKyotoCache(namespace):
        return os.path.exists(namespace+".kch")
    cacheList.append({'class':KyotoCache, 'check':isKyotoCache})

    class KyotoCacheComp(KyotoCache): # with compression
        def __init__(self, dir, subdirs = []):
            dir+="_zlib"
            if dir not in dbList:
                dbList[dir] = DB()
                dbList[dir].open(dir+".kch#ops=c#log="+dir+".log#logkinds=debu#zcomp=zlib", DB.OWRITER | DB.OCREATE)
            self.db = dbList[dir]
            self.key = "/".join(subdirs)

    def isKyotoCacheComp(namespace):
        return os.path.exists(namespace+"_zlib.kch")
    cacheList.append({'class':KyotoCacheComp, 'check':isKyotoCacheComp})

try:
    import lib.leveldb as leveldb
except:
    config.cachePort = 0
    pass
else:
    dbList = {}
    class LevelCache(object):
        def __init__(self, dir, subdirs = []):
            dir+=".ldb"
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

    def isLevelCache(namespace):
        return os.path.isdir(namespace+".ldb")
    cacheList.append({'class':LevelCache, 'check':isLevelCache})

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

def isCacheClient(namespace):
    return config.cachePort > 0
cacheList.append({'class':CacheClient, 'check':isCacheClient})


try:
    from hypertable.thriftclient import *
    from hyperthrift.gen.ttypes import *
except:
    pass
else:

    class HypertableCache(BaseCache):
        clientCache = None
        def __init__(self, dir, subdirs = []):
            if HypertableCache.clientCache == None:
                HypertableCache.clientCache = ThriftClient("localhost", 38080)
            self.client = HypertableCache.clientCache
            self.key = "/".join(subdirs)
            if not self.client.exists_namespace("flashget_"+dir):
                self.client.create_namespace("flashget_"+dir)
            self.namespace = self.client.open_namespace("flashget_"+dir)
            if not self.client.exists_table(self.namespace, "cache"):
                sections = ['data', 'redirect']
                self.client.hql_query(self.namespace, 'CREATE TABLE cache('+','.join(sections)+')');

        def lookup(self, section):
            key = self.key.replace('"', '\\"')
            res = self.client.hql_query(self.namespace, 'select '+section+' FROM cache WHERE row="'+key+'" REVS 1 NO_ESCAPE')
            if res.cells == []:
                return None
            return res.cells[0].value

        def write(self, section, data):
            key = self.key.replace('"', '\\"')
            if key == '':
                return None
            self.client.hql_query(self.namespace, 'INSERT INTO cache VALUES ("%s", "%s", \'%s\')' % (key, section, data.replace("\\", "\\\\").replace("'", "\\'").replace("\x00", "")));

        def remove(self, section):
            key = self.key.replace('"', '\\"')
            if section is None:
                section = '*'
            self.client.hql_query(self.namespace, 'DELETE %s FROM cache WHERE ROW="%s"' % (section, key))

        def iterKeyValues(self):
            res = self.client.hql_exec(self.namespace, 'select * FROM cache REVS 1', 0, 1)
            scanner = res.scanner
            while True:
                cells = self.client.next_row_as_arrays(scanner)
                if not len(cells): break
                key = cells[0][0]
                section = cells[0][1]
                data = cells[0][3]
                #timestamp = cells[0][4]
                yield (key+"/"+section, data)
            self.client.close_scanner(scanner)
    def isHypertableCache(namespace):
        return config.hypertable
    cacheList.append({'class':HypertableCache, 'check':isHypertableCache, 'noDefault':True})




# a factory, which will create the class based on cachelist
class Cache(object):
    _dirToCache = {} # internal mapping from dir to cache
    def __new__(cls, dir, subdirs=[]):
        cls = None
        if dir in Cache._dirToCache:
            cls = Cache._dirToCache[dir]
        if not cls:
            for i in cacheList[::-1]:
                if i['check'](dir):
                    cls = i['class']
                    break
            else:
                log.debug("no cache exists for %s" % dir)
                # no cache found yet chose a default cache
                for i in cacheList[::-1]:
                    if 'noDefault' in i and i['noDefault']:
                        continue
                    cls = i['class']
            if cls == None:
                raise Exception("No Cache is available")
        log.debug("using cache %s" % cls.__name__)
        Cache._dirToCache[dir] = cls
        return cls(dir, subdirs)
