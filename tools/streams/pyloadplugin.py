# 
# from tools.url import UrlMgr, LargeDownload
# from tools.helper import textextract, textextractall
# import config
# from tools.extension import Extension
# from tools.basestream import BaseStream
# 
# import logging
# 
# log = logging.getLogger('streams')
# 
# 
# from tools.pyload import Pyload
# import new
# import inspect
# 
# 
# class Request(object):
#     def __init__(self):
#         print "new"
#         self.cookies = {}
# 
#     def getDomain(self, url):
#         domain = textextract(url, '://', '')
#         tmp = textextract(domain, '', '/')
#         if tmp is not None and len(tmp)<domain:
#             domain = tmp
#         tmp = textextract(domain, '', '?')
#         if tmp is not None and len(tmp)<domain:
#             domain = tmp
#         tmp = textextract(domain, '', '&')
#         if tmp is not None and len(tmp)<domain:
#             domain = tmp
#         return domain
# 
#     def load(self, *args, **kwargs):
#         post = ''
#         print args
#         if len(args)>2 and args[2] is not {}:
#             posttmp = args[2]
#             for i in posttmp:
#                 post+='&'+i+'='+posttmp[i]
# 
#         cookies = []
#         for domain in self.cookies:
#             if domain in args[0]:
#                 cookies = []
#                 for i in self.cookies[domain]:
#                     cookies.append(i+'='+self.cookies[domain][i])
#                 break
#         url = UrlMgr(url = args[0], post=post, nocache=True, cache_writeonly=True, cookies = cookies)
# 
#         domain = self.getDomain(args[0])
#         for i in url.pointer.cookies:
#             name = textextract(i, '', '=')
#             value = textextract(i, name+'=', ';')
#             if domain not in self.cookies:
#                 self.cookies[domain] = {}
#             self.cookies[domain][name] = value
# 
#         if url.data == 'mp4:15:0':
#             return 'mp4:1:0'
#         return url.data
# 
#     def setCookie(self, domain, name, value):
#         if domain not in self.parent.cookies:
#             self.parent.cookies[domain] = {}
#         self.parent.cookies[domain][name] = value
# 
# class PyFile(object):
#     def getAccountForPlugin(self, name):
#         print name
#         return None
#     def getRequest(self, name):
#         print name
#         ret = Request()
#         ret.cj = Request()
#         ret.cj.parent = ret
#         return ret
#     @staticmethod
#     def get(name, option):
#         print name, option
#     def setStatus(self, name):
#         print name
# 
# 
# 
# dummyDownloadUrl = ''
# def dummyDownload(url):
#     global dummyDownloadUrl
#     dummyDownloadUrl = url
# 
# class BaseDummy(object):
#     def get(self, VideoInfo, justId=False, isAvailable=False):
#         global dummyDownloadUrl
#         pyfile = PyFile()
#         pyfile.abort = False
#         core = PyFile()
#         core.debug = True
#         core.log = log
#         core.config = PyFile
#         core.accountManager = PyFile()
#         core.requestFactory = PyFile()
#         core.js = PyFile()
#         m = PyFile()
#         m.core = core
#         pyfile.m = m
#         pyfile.url = VideoInfo.stream_url
#         instance = self.baseClass(pyfile)
#         instance.setup()
#         instance.download = dummyDownload
#         instance.process(pyfile)
# 
#         self.flvUrl = dummyDownloadUrl
#         return dummyDownloadUrl
# 
# a=Pyload()
# c = 0
# for mod in a.run():
#     for name, obj in inspect.getmembers(mod, lambda x: inspect.isclass(x)):
#         if name in ('SimpleHoster', 'Hoster'):
#             continue
#         if hasattr(obj, "__pattern__") and hasattr(obj, '__name__'):
#             c += 1
#             dummy = new.classobj('dummy'+str(c), (BaseDummy, Extension, BaseStream), {})
#             dummy.ename = obj.__name__
#             dummy.eregex = obj.__pattern__
#             dummy.baseClass = obj
#             exec('dummy'+str(c)+' = dummy')
# 
