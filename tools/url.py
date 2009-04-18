import re
import os
import urllib2
import urllib
from logging import LogHandler
import config
import sys
import time
import threading

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
    def __init__(self, dir, url, post, log):
        self.log = LogHandler('Cache', log)
        urlpath  = self.get_filename(url)
        postpath = self.get_filename(post)
        self.path = os.path.join(dir, urlpath, postpath)
        if os.path.isdir(self.path) is False:
            self.create_path = True
        else:
            self.create_path = False

    @staticmethod
    def get_filename(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def get_path(self, section):
        if self.create_path:
            os.makedirs(self.path)
        self.create_path = False
        return os.path.join(self.path, section)

    def lookup(self, section):
        file = self.get_path(section)
        if os.path.isfile(file) is True:
            self.log.info("using cache [" + section + "] path: " + file)
            f = open(file, "r")
            return ''.join(f.readlines())
        else:
            return ''

    def lookup_size(self, section):
        # TODO cache this size in this class
        file = self.get_path(section)
        if os.path.isfile(file):
            return os.path.getsize(file)

    def get_stream(self, section):
        file = self.get_path(section)
        return open(file, 'wb')

    def get_append_stream(self, section):
        file = self.get_path(section)
        return open(file, 'ab')

    def write(self, section, data):
        file = self.get_path(section)
        f=open(file, "w")
        f.writelines(data)


class UrlMgr(object):
    def __init__(self,args):
        self.__pointer = None  # this variable is used intern, to access it use url.pointer
        self.__data = None  # this variable is used intern, to access it use url.data
        self.__size = None  # this variable is used intern, to access it use url.size
        self.__redirection = '' # this variable is used intern, to access it use url.redirection
        self.position = 0

        if 'cache_dir' in args:
            cache_dir = args['cache_dir']
        else:
            cache_dir = config.cache_dir

        if 'log' in args:
            self.log = LogHandler('download', args['log'])
        else:
            self.log = LogHandler('download', None)

        self.url  = args['url']
        self.post = ''
        if 'post' in args:
            self.post = args['post']

        self.cache = UrlCache(cache_dir, self.url, self.post, self.log)

    def del_pointer(self):
        self.__pointer = None

    def get_pointer(self):
        if self.__pointer:
            return self.__pointer
        self.log.info("downloading from: " + self.url)
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
                self.log.info("post")
                post_data = urllib.urlencode(self.post)
                self.__pointer = urllib2.urlopen(req, post_data)
            else:
                self.__pointer = urllib2.urlopen(req)

        except IOError, e:
            self.log.error('We failed to open: %s' % self.url)
            if hasattr(e, 'code'):
                   self.log.error('We failed with error code - %s.' % e.code)
            if hasattr(e, 'reason'):
                self.log.error("The error object has the following 'reason' attribute :")
                self.log.error(str(e.reason))
                self.log.error("This usually means the server doesn't exist,' is down, or we don't have an internet connection.")
        return self.__pointer

    def set_pointer(self, value):
        self.__pointer = value

    def get_redirection(self):
        self.__redirection = self.cache.lookup('redirection')

        if self.__redirection is '':
            self.__redirection = self.pointer.geturl()
            self.cache.write('redirection', self.__redirection)
        return self.__redirection

    def get_data(self):
        if self.__data:
            return self.__data

        self.__data = self.cache.lookup('data')
        if self.__data is '':
            if not self.pointer:
                self.log.error('trying to get the data, but no pointer was given')
                self.__data = ''
            else:
                self.__data = self.pointer.read()
                if self.pointer.headers.get('Content-Encoding') == 'gzip':
                    compressedstream = StringIO.StringIO(self.__data)
                    gzipper   = gzip.GzipFile(fileobj = compressedstream)
                    self.__data = gzipper.read()
                self.cache.write('data', self.__data)
        return self.__data

    def get_size(self):
        if self.__size:
            return self.__size

        self.__size = self.cache.lookup('size')
        if self.__size is not '':
            self.__size = int(self.__size)

        if self.__size is '':
            if not self.pointer:
                self.log.error('trying to get the size, but no pointer was given')
                self.__size = 0
            else:
                content_length = self.pointer.info().get('Content-length', None)
                if content_length:
                    self.__size = int(content_length)
                    self.cache.write('size', str(self.__size))
                else:
                    self.log.error('no conent-length found - this can break the programm')
                    self.__size = 0
        return self.__size

    pointer = property(fget=get_pointer, fdel=del_pointer)
    data = property(fget=get_data)
    size = property(fget=get_size)
    redirection = property(fget=get_redirection)


class LargeDownload(UrlMgr, threading.Thread):
    STATE_ERROR = 1
    STATE_FINISHED = 2
    STATE_ALREADY_COMPLETED = 4
    STATE_DOWNLOAD_CONTINUE = 8
    STATE_DOWNLOAD = 16

    def __init__(self, args):
        threading.Thread.__init__(self)
        UrlMgr.__init__(self, args)

        if 'cache_dir2' not in args:
            cache_dir2 = config.cache_dir_for_flv
        else:
            cache_dir2 = args['cache_dir2']
        if 'cache_folder' not in args:
            cache_folder = self.url
        else:
            cache_folder = args['cache_folder']
        self.cache2 = UrlCache(cache_dir2, cache_folder, '', self.log)

        self.downloaded = 0
        self.megavideohack = False # megavideo resume is strange - so i implented an hack for it
        self.save_path = '' # we will store here the savepath of the downloaded stream
        self.queue = args['queue']
        self.id = 255
        self.state = 0

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name is 'position':
            del self.pointer        # set this to None so that next pointer request forces a redownload - and will resume then
            self.set_resume()       # handle special resume-cases

    def set_resume(self):
        if self.position == 0:
            return
        ''' This function is a preprocessor for get_pointer in case of resume. '''
        if(self.url.find('megavideo.com/files/') > 0):      # those links need a hack:
            self.log.info('resuming megavideo')

            self.megavideohack = True
            if not self.url.endswith('/'):
                self.url += '/'
            self.url += str(self.position)
            return

    def got_requested_position(self):
        if self.megavideohack:
            return True

        if not self.pointer:
            return False

        # this function will just look if the server realy let us continue at our requested position
        check = self.pointer.info().get('Content-Range', None)
        if not check:
            return False

        check = textextract(check,'bytes ', '-')
        self.log.info(str(check)+"  "+str(self.position))
        if int(check) == int(self.position):
            return True
        else:
            return False

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
        if elapsed_time < 0.001:
            return int(new_max)
        rate = bytes / elapsed_time
        if rate > new_max:
            return int(new_max)
        if rate < new_min:
            return int(new_min)
        return int(rate)

    def run(self):
        self.downloaded = self.cache2.lookup_size('data')
        self.save_path  = self.cache2.get_path('data')
        stream = None
        if self.downloaded > 0:
            if self.size == self.downloaded:
                self.state = LargeDownload.STATE_ALREADY_COMPLETED | LargeDownload.STATE_FINISHED
                self.queue.put(self.id)
                return
            elif self.size > self.downloaded:
                # try to resume
                self.log.info("trying to resume")
                self.position = self.downloaded
                if self.got_requested_position():
                    self.log.info("can resume")
                    stream = self.cache2.get_append_stream('data')
                    self.state = LargeDownload.STATE_DOWNLOAD_CONTINUE

        self.state |= LargeDownload.STATE_DOWNLOAD
        if stream is None:
            stream = self.cache2.get_stream('data')
            self.downloaded = 0
            self.position   = 0

        block_size = 1024
        start = time.time()
        abort = 0

        if not self.pointer:
            log.error('couldn\'t resolv url')
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.id)
            return

        while self.downloaded != self.size:
            # Download and write
            before = time.time()
            data_block = self.pointer.read(block_size)
            after = time.time()
            if not data_block:
                log.info("received empty data_block %s %s" % (self.downloaded, self.size))
                abort += 1
                if abort == 1:
                    break
                else:
                    time.sleep(10)
                continue
            abort = 0

            data_block_len = len(data_block)
            stream.write(data_block)

            self.downloaded += data_block_len
            block_size = LargeDownload.best_block_size(after - before, data_block_len)
            self.queue.put(self.id)

        try:
            stream.close()
        except (OSError, IOError), err:
            log.error('unable to write video data: %s' % str(err))
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.id)
            return

        if (self.downloaded) != self.size:
            # raise ValueError('Content too short: %s/%s bytes' % (self.downloaded, self.size))
            self.log.error('Content too short: %s/%s bytes' % (self.downloaded, self.size))
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.id)
            return
        self.state = LargeDownload.STATE_FINISHED
        self.queue.put(self.id)
