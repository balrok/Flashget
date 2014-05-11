import config
import re
import os
import logging
import atexit
import time

log = logging.getLogger(__name__)

from tools.helper import open


# contains a list of {'class'..,'check'..,'noDefault'} where class is the cacheclass and check is a function
# which decides if we use this specific cache. The decission is made based on configuration or wether a cache-folder/file
# already exists
# the last item in the list is the most important
# noDefault is a bool which defines if we should use this cache when no other caches match
cacheList = []


class BaseCache(object): # interface for all my caches
    def __init__(self, keys):
        # keys[0] is used as main key - like db name, folder name ...
        self.key = "/".join(keys[1:])
    def remove(self, section):
        pass
    def lookup(self, section):
        return None
    def write(self, section, data):
        pass
    def __repr__(self):
        return self.__class__.__name__+':'+self.key

# from tools.helper import calc_eta, calc_percent
# def convertCache(fromCache, toCache):
#     log.info("converting caches")
#     allkeyLen = fromCache.count()
#     i = 0
#     startTime = time.time()
#     for data in fromCache.iterKeyValues():
#         key, value = data
#         i += 1
#         if i%1000==1:
#             eta = calc_eta(startTime, allkeyLen, i)
#             percent = calc_percent(i, allkeyLen)
#             sys.stdout.write("%d of %d ETA: %s Percent %s\r" % (i, allkeyLen, eta, percent))
#             sys.stdout.flush()
#         keys = key.split("/")
#         section = keys[-1][:]
#         del keys[-1]
#         toCache.key = '/'.join(keys)
#         toCache.write(section, value)


FILENAME_MAX_LENGTH = 100 # maxlength of filenames
# the filecache has also some additional interface methods
class FileCache(BaseCache):
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


def isFileCache(namespace):
    return config.preferFileCache or os.path.isdir(namespace)
cacheList.append({'class':FileCache, 'check':isFileCache})


# below this i define several database caches - so they don't support append_stream and so on.. i won't store so big data inside

try:
    from kyotocabinet import DB
except ImportError:
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
        def __init__(self, keys):
            if keys[0] not in dbList:
                dbList[keys[0]] = DB()
                dbList[keys[0]].open("%s.kch" % keys[0], DB.OWRITER | DB.OCREATE)
            self.db = dbList[keys[0]]
            self.key = "/".join(keys[1:])
        def lookup(self, section):
            ret = self.db.get(self.key+"/"+section)
            return ret
        def write(self, section, data):
            self.db.set(self.key+"/"+section, data)
        def remove(self, section):
            self.db.remove(self.key+"/"+section)

    def isKyotoCache(namespace):
        return os.path.exists(namespace+".kch")
    cacheList.append({'class':KyotoCache, 'check':isKyotoCache})

    class KyotoCacheComp(KyotoCache): # with compression
        def __init__(self, keys):
            keys[0] += "_zlib"
            if keys[0] not in dbList:
                dbList[keys[0]] = DB()
                dbList[keys[0]].open("%s.kch#ops=c#log=%s.log#logkinds=debu#zcomp=zlib" % (keys[0], keys[0]), DB.OWRITER | DB.OCREATE)
            self.db = dbList[keys[0]]
            self.key = "/".join(keys[1:])

    def isKyotoCacheComp(namespace):
        return os.path.exists(namespace+"_zlib.kch")
    cacheList.append({'class':KyotoCacheComp, 'check':isKyotoCacheComp})

try:
    import lib.leveldb as leveldb
except ImportError:
    config.cachePort = 0
    pass
else:
    dbList = {}
    class LevelCache(BaseCache):
        def __init__(self, keys):
            keys[0] += ".ldb"
            if keys[0] not in dbList:
                dbList[keys[0]] = leveldb.LevelDB(keys[0])
            self.db = dbList[keys[0]]
            self.key = "/".join(keys[1:])

        def lookup(self, section):
            ret = self.db.Get(self.key+"/"+section)
            return ret
        def write(self, section, data):
            self.db.Put(self.key+"/"+section, data)
        def remove(self, section):
            self.db.Delete(self.key+"/"+section)

    def isLevelCache(namespace):
        return os.path.isdir(namespace+".ldb")
    cacheList.append({'class':LevelCache, 'check':isLevelCache})

import socket
import pickle

HOST = 'localhost'
PORT = config.cachePort
ADDR = (HOST,PORT)

conList = {}

# we have a cacheserver - write a client for it
class CacheClient(BaseCache):
    def __init__(self, keys):
        self.dir = keys[0]
        self.setKey(keys[1:])
        if self.dir not in conList:
            self.connect()
            conList[self.dir] = self.c
        self.c = conList[self.dir]

    def connect(self):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        for i in range(60):
            try:
                s.connect((ADDR))
            except Exception:
                time.sleep(1)
                log.warning("couldn't connect to cache server")
            else:
                break
        self.c = s

    def setKey(self, subdirs):
        self.key = "/".join(subdirs)

    def lookup(self, section):
        return self.sendRecv('lookup', section)
    def remove(self, section):
        return self.sendRecv('remove', section)
    def write(self, section, data):
        return self.sendRecv('write', section, data)

    sendRecvCalls = 0
    def sendRecv(self, command, section, value=''):
        try:
            data = pickle.dumps({'c':command,'k':self.key,'section':section,'d':self.dir,'v':value}, 1)
            size = str(len(data))
            size += (8-len(size))*" "
            self.c.sendall(size+data)
            retdata = ''
            if command in ('lookup',):
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
        except socket.error as e:
            log.error("socketerror %s", str(e))
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
    from hypertable.thriftclient import ThriftClient
    # from hyperthrift.gen.ttypes import *
except ImportError:
    pass
else:

    class HypertableCache(BaseCache):
        clientCache = None
        def __init__(self, keys):
            if HypertableCache.clientCache == None:
                HypertableCache.clientCache = ThriftClient("localhost", 38080)
            self.client = HypertableCache.clientCache
            self.key = "/".join(keys[1:])
            if not self.client.exists_namespace("flashget_%s" % keys[0]):
                self.client.create_namespace("flashget_%s" % keys[0])
            self.namespace = self.client.open_namespace("flashget_%s" % keys[0])
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

    def isHypertableCache(namespace):
        return config.preferHypertable
    cacheList.append({'class':HypertableCache, 'check':isHypertableCache, 'noDefault':True})


if config.preferHypertable:
    for i in cacheList:
        if i['class'] == HypertableCache:
            cacheList.append(i)
            break
if config.preferFileCache:
    for i in cacheList:
        if i['class'] == FileCache:
            cacheList.append(i)
            break


# a factory, which will create the class based on cachelist
class Cache(BaseCache):
    _dirToCache = {} # internal mapping from dir to cache
    def __new__(cls, keys):
        cls = None
        if keys[0] in Cache._dirToCache:
            cls = Cache._dirToCache[keys[0]]
        if not cls:
            for i in cacheList[::-1]:
                if i['check'](keys[0]):
                    cls = i['class']
                    break
            else:
                log.debug('no cache exists for %s', keys[0])
                # no cache found yet chose a default cache
                for i in cacheList[::-1]:
                    if 'noDefault' in i and i['noDefault']:
                        continue
                    cls = i['class']
            if cls == None:
                raise Exception("No Cache is available")
        log.debug('using cache %s', cls.__name__)
        Cache._dirToCache[keys[0]] = cls
        return cls(keys)
