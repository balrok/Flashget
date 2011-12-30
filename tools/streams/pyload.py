
from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract, textextractall
import config
from tools.extension import Extension
from tools.basestream import BaseStream

import logging

log = logging.getLogger('streams')


from tools.pyload import Pyload
import new
import inspect

class PyFile(object):
    def getAccountForPlugin(self, name):
        print name
        return None
    def getRequest(self, name):
        print name
        ret = PyFile()
        ret.cj = PyFile()
        return ret
    def setCookie(self, domain, name, value):
        pass
    def load(self, *args, **kwargs):
        print "-----"
        print args
        print kwargs
        post = ''
        if 2 in args and args[2] is not {}:
            posttmp = args[2]
            for i in posttmp:
                post+='&'+i+'='+posttmp[i]
        print post
        print "-----"
        url = UrlMgr(url = args[0], post=post, nocache=True, cache_writeonly=True)
        print url.cookies
        if post != '':
            print url.data
        print url.data
        return url.data
    @staticmethod
    def get(name, option):
        print name, option



dummyDownloadUrl = ''
def dummyDownload(url):
    global dummyDownloadUrl
    dummyDownloadUrl = url

class BaseDummy(object):
    def get(self, VideoInfo, justId=False, isAvailable=False):
        global dummyDownloadUrl
        pyfile = PyFile()
        pyfile.abort = False
        core = PyFile()
        core.debug = True
        core.log = log
        core.config = PyFile
        core.accountManager = PyFile()
        core.requestFactory = PyFile()
        core.js = PyFile()
        m = PyFile()
        m.core = core
        pyfile.m = m
        pyfile.url = VideoInfo.stream_url
        instance = self.baseClass(pyfile)
        instance.setup()
        instance.download = dummyDownload
        instance.process(pyfile)

        self.flvUrl = dummyDownloadUrl
        return dummyDownloadUrl

a=Pyload()
c = 0
for mod in a.run():
    for name, obj in inspect.getmembers(mod, lambda x: inspect.isclass(x)):
        if name in ('SimpleHoster', 'Hoster'):
            continue
        if hasattr(obj, "__pattern__") and hasattr(obj, '__name__'):
            c += 1
            dummy = new.classobj('dummy'+str(c), (BaseDummy, Extension, BaseStream), {})
            dummy.ename = obj.__name__
            dummy.eregex = obj.__pattern__
            dummy.baseClass = obj
            exec('dummy'+str(c)+' = dummy')

