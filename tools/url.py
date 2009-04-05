import re
import os
import urllib2
import urllib
from logging import LogHandler
from config import config

log = LogHandler('download')

try:
    from keepalive import HTTPHandler
except:
    pass
else:
    keepalive_handler = HTTPHandler()
    opener = urllib2.build_opener(keepalive_handler)
    urllib2.install_opener(opener)
    log.info('keepalive support active')

GZIP = 0
try:
    import StringIO
    import gzip
except:
    pass
else:
    GZIP = 1
    log.info('gzip support active')

class UrlCache(object):
    # TODO implement function to truncate to long files for old filesystems
    # or for very long post-data
    def __init__(self, dir, url, post):
        urlpath  = self.get_filename(url)
        postpath = self.get_filename(post)
        self.path = os.path.join(dir, urlpath, postpath)
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)

    @staticmethod
    def get_filename(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def lookup(self, section):
        file = os.path.join(self.path, section)
        if os.path.isfile(file) is True:
            log.info("using cache [" + section + "] path: " + file)
            f = open(file, "r")
            return ''.join(f.readlines())
        else:
            return ''

    def write(self, section, data):
        file = os.path.join(self.path, section)
        f=open(file, "w")
        f.writelines(data)


class UrlMgr(object):
    def __init__(self,args):
        if 'cache_dir' in args:
            cache_dir = args['cache_dir']
        else:
            cache_dir = config.cache_dir

        self.url  = args['url']
        self.post = ''
        if 'post' in args:
            self.post = args['post']

        self.cache = UrlCache(cache_dir, self.url, self.post)

    @staticmethod
    def get_filename(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def __getattr__(self, name):
        if name is 'pointer':
            self.get_pointer()
            return self.pointer
        if name is 'data':
            self.get_data()
            return self.data
        if name is 'size':
            self.get_size()
            return self.size

    def get_pointer(self):
        log.info("downloading from:" + self.url)
        try:
            req = urllib2.Request(self.url)
            if GZIP:
                req.add_header('Accept-Encoding', 'gzip')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-us,en;q=0.5')
            req.add_header('Accept-Charset', 'utf-8,ISO-8859-1;q=0.7,*;q=0.7')
            #req.add_header('Keep-Alive', '300')
            #req.add_header('Connection', 'keep-alive')
            if self.post is not None:
                post_data = urllib.urlencode(self.post)
                self.pointer = urllib2.urlopen(req, post_data)
            else:
                self.pointer = urllib2.urlopen(req)
        except IOError, e:
            log.error('We failed to open "%s".' % self.url)
            if hasattr(e, 'code'):
                   log.error('We failed with error code - %s.' % e.code)
            elif hasattr(e, 'reason'):
                log.error("The error object has the following 'reason' attribute :")
                log.error(e.reason)
                log.error("This usually means the server doesn't exist,' is down, or we don't have an internet connection.")
            sys.exit()

    def get_redirection(self):
        self.redirection = self.cache.lookup('redirection')

        if self.redirection is '':
            self.redirection = self.pointer.geturl()
            self.cache.write('redirection', self.redirection)

    def get_data(self):
        self.data = self.cache.lookup('data')

        if self.data is '':
            data = self.pointer.read()
            if self.pointer.headers.get('Content-Encoding') == 'gzip':
                compressedstream = StringIO.StringIO(data)
                gzipper   = gzip.GzipFile(fileobj = compressedstream)
                self.data = gzipper.read()
                self.cache.write('data', self.data)

    def get_size(self):
        self.size = self.cache.lookup('size')
        if self.size is '':
            self.size = int(self.pointer.info().get('Content-length', None))
            self.cache.write('size', self.size)
