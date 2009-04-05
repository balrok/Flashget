import re
import os
import urllib2
import urllib
from logging import LogHandler
from config import config
import sys

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





def textextract(data,startstr,endstr):
    pos1=data.find(startstr)
    if pos1<0:
        return
    pos1+=len(startstr)
    pos2=data.find(endstr,pos1)
    if pos2<0:
        return
    return data[pos1:pos2]










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

        print self.url
        self.cache = UrlCache(cache_dir, self.url, self.post)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name is 'position':
            try:
                del self.pointer        # set this to None so that next pointer request forces a redownload - and will resume then
            except:
                pass
            self.set_resume()       # handle special resume-cases

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
        # TODO i guess i have to throw an error here

    def set_resume(self):
        ''' This function is a preprocessor for get_pointer in case of resume. '''
        if(self.url.find('megavideo.com/files/') > 0):      # those links need a hack:
            log.info('resuming megavideo')
            self.megavideohack = True
            if not self.url.endswith('/'):
                self.url += '/'
            self.url += str(self.position)
            return


    def got_requested_position(self):
        if self.megavideohack:
            return True

        # this function will just look if the server realy let us continue at our requested position
        check = self.pointer.info().get('Content-Range', None)
        if not check:
            return False

        check = textextract(check,'bytes ', '-')
        print str(check)+"  "+str(self.position)
        if int(check) == int(self.position):
            return True
        else:
            return False

    def get_pointer(self):
        log.info("downloading from: " + self.url)
        import time
        try:
            req = urllib2.Request(self.url)
            if GZIP:
                req.add_header('Accept-Encoding', 'gzip')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-us,en;q=0.5')
            req.add_header('Accept-Charset', 'utf-8,ISO-8859-1;q=0.7,*;q=0.7')
            if self.position:
                req.add_header('Range', 'bytes=%d-' % (self.position))
            # req.add_header('Keep-Alive', '300')
            # req.add_header('Connection', 'keep-alive')

            if self.post:
                post_data = urllib.urlencode(self.post)
                self.pointer = urllib2.urlopen(req, post_data)
            else:
                self.pointer = urllib2.urlopen(req)

        except IOError, e:
            log.error('We failed to open: %s' % self.url)
            if hasattr(e, 'code'):
                   log.error('We failed with error code - %s.' % e.code)
            if hasattr(e, 'reason'):
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
            self.data = self.pointer.read()
            if self.pointer.headers.get('Content-Encoding') == 'gzip':
                compressedstream = StringIO.StringIO(data)
                gzipper   = gzip.GzipFile(fileobj = compressedstream)
                self.data = gzipper.read()
            self.cache.write('data', self.data)

    def get_size(self):
        self.size = self.cache.lookup('size')
        if self.size is '':
            self.size = int(self.pointer.info().get('Content-length', None))
            self.cache.write('size', str(self.size))
        else:
            self.size = int(self.size)