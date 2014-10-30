# vim: set fileencoding=utf-8 :
from .config import config
from .cache import FileCache
import requests

from .helper import textextract, EndableThreadingClass
import os
import time
import tempfile
import logging


def debug_on_httplevel():
    try:
        import httplib # python 2
        httplib.HTTPConnection.debuglevel = 1
    except ImportError:
        import http # python 3
        http.client.HTTPConnection.debuglevel = 1

# debug_on_httplevel()

log = logging.getLogger(__name__)


def void(*dummy):
    return None

rsession = requests.Session()


# writes data into cache
class UrlMgr(object):
    isStream = False
    default_base_cache_dir = config.get('cache_dir', tempfile.mkdtemp())
    default_cache_class = FileCache

    def __init__(self, url, **kwargs):
        self.clear_connection()

        self.url = url

        # cache related
        base_cache_dir = kwargs.pop('base_cache_dir', self.default_base_cache_dir)
        cache_folder = kwargs.pop('cache_folder', self.url)
        if 'post' in kwargs:
            cache_folder += "POST %d" % hash(frozenset(kwargs["post"]))
        self.cache = self.default_cache_class([base_cache_dir, cache_folder])

        if 'cache_writeonly' in kwargs and kwargs['cache_writeonly']:
            self.setCacheWriteOnly()
        if 'cache_readonly' in kwargs and kwargs['cache_readonly']:
            self.setCacheReadOnly()
        if 'nocache' in kwargs and kwargs['nocache']:
            self.setCacheWriteOnly()
            self.setCacheReadOnly()
        self.position = 0
        self.__data = None
        self.__request = None
        self.__size = None
        self.kwargs = kwargs

    def initHeader(self):
        header = {
        'user-agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'en-us,en;q=0.5', 'accept-charset': 'utf-8;q=0.7'}
        if self.position:
            header['range'] = 'bytes=%d-' % self.position
        if "header" in self.kwargs:
            for key in self.kwargs["header"]:
                value = self.kwargs["header"][key]
                header[key] = value
        return header

    def initRequestArgs(self):
        requestArgs = {}
        if "post" in self.kwargs:
            requestArgs['method'] = "post"
            requestArgs["data"] = self.kwargs["post"]
        else:
            requestArgs['method'] = "get"
        requestArgs["url"] = self.url
        for i in ["params", "cookies"]:
            try:
                requestArgs[i] = self.kwargs[i]
            except KeyError:
                pass
        requestArgs["headers"] = self.initHeader()
        requestArgs["stream"] = self.isStream
        requestArgs["timeout"] = 10
        return requestArgs

    def setCacheWriteOnly(self):
        self.cache.lookup_size = void
        self.cache.lookup = void

    def setCacheReadOnly(self):
        self.cache.write = void

    def clearCache(self):
        for i in ('data', 'size'):
            try:
                self.cache.remove(i)
            except Exception:
                pass

    def clear_connection(self):
        # those variables are used intern, to access them remove the __ (example: url.request)
        self.__data = None
        self.__request = None
        self.__size = None
        self.position = 0

    def get_request(self):
        if self.__request:
            return self.__request

        requestArgs = self.initRequestArgs()
        try:
            self.__request = rsession.request(**requestArgs)
        except requests.exceptions.Timeout:
            self.__data = ''
            self.cache.write('data', self.__data)
            return None
        if "encoding" in self.kwargs:
            self.__request.encoding = self.kwargs["encoding"]

        #cacheControl = self.__request.headers.get("Cache-Control")
        #if "
        # TODO look at https://pypi.python.org/pypi/CacheControl/0.10.2
        # controller.py how to implement a check
        # the idea is to automatically stop caching when a no-cache header is represent

        return self.__request

    def get_data(self):
        if self.__data is not None:
            return self.__data
        self.__data = self.cache.lookup('data')
        if self.__data is None:
            if not self.request:
                log.error('trying to get the data, but no request was given')
                self.__data = ''
            else:
                self.__data = self.request.text
                self.cache.write('data', self.__data)
        return self.__data

    def get_rawdata(self):
        return self.request.content

    def get_size(self):
        if self.__size:
            return self.__size

        self.__size = self.cache.lookup('size')
        if not self.__size:
            self.__size = 0
        self.__size = int(self.__size)

        if self.__size == 0:
            if not self.request:
                log.error('trying to get the size, but no request was given')
                self.__size = 0
            else:
                if 'content-length' in self.request.headers:
                    content_length = self.request.headers['content-length']
                    self.__size = int(content_length)
                    self.cache.write('size', str(self.__size))
                else:
                    log.error('no content-length found - this can break the programm')
                    self.__size = 0
        return self.__size

    request = property(fget=get_request)
    data = property(fget=get_data)
    size = property(fget=get_size)



class LargeDownload(UrlMgr, EndableThreadingClass):
    uids = 0
    isStream = True
    retries = 1  # maximum of retries for a file

    default_base_cache_dir = config.get('cache_dir_for_flv', tempfile.mkdtemp())
    default_cache_class = FileCache

    def __init__(self, url, **kwargs):
        UrlMgr.__init__(self, url, **kwargs)

        self.hooks = kwargs.pop('hooks', {})
        self.downloaded = 0
        self.save_path = ''  # we will store here the savepath of the downloaded stream
        self.uid = LargeDownload.uids
        LargeDownload.uids += 1
        log.debug('%d initializing Largedownload with url %s and cachedir %s', self.uid, self.url, self.cache.get_path())
        EndableThreadingClass.__init__(self)
        self.isResume = False
        try:
            self.limit = int(config.get('limit')) * 1024
        except:
            self.limit = 0

    def __str__(self):
        # TODO sometimes size is not working (when link is broken) maybe return different strings or try/except
        return "%s: %s %d/%d" % (self.__class__.__name__, self.save_path, self.downloaded, self.size)

    def __setattr__(self, name, value):
        if name is 'position':
            if value == 0:
                self.__dict__[name] = value
            else:
                if self.position != value:
                    self.__dict__[name] = value
                    self.clear_connection()
                    self.set_resume()       # handle special resume-cases
        self.__dict__[name] = value

    def set_resume(self):
        if self.position == 0:
            return

    def got_requested_position(self):
        # this function will just look if the server realy let us continue at our requested position
        # 206 - Partial Content ... i think if the server sends us this response, he also accepted our range
        if self.request.status_code == requests.codes.ok:
            return True
        check = None
        if 'content-range' in self.request.headers:
            check = self.request.headers['content-range']
        if not check:
            return False
        check = int(textextract(check,'bytes ', '-'))
        if check == self.position:
            log.info('%d check if we got requested position, requested: %d got: %d => OK', self.uid, check, self.position)
            return True
        else:
            log.error('%d check if we got requested position, requested: %d got: %d => WRONG', self.uid, check, self.position)
            return False

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_max = min(max(bytes * 2, 1), 4194304)
        if elapsed_time < 0.001:
            return new_max
        rate = bytes / elapsed_time
        if rate > new_max:
            return new_max
        new_min = max(bytes / 2, 1)
        if rate < new_min:
            return int(new_min)
        return int(rate)

    def apply_limit(self, elapsed_time, block_size):
        """ applies the rate limit to the block_size and might sleep a bit if it goes
        too fast """
        if self.limit > 0 and block_size > self.limit:
            block_size = self.limit
            if elapsed_time < 1:
                time.sleep(1 - elapsed_time)
        return block_size

    def resumeDownload(self):
        if self.size > self.downloaded:
            # try to resume
            log.debug('%d trying to resume', self.uid)
            self.position = self.downloaded
            if self.got_requested_position():
                log.debug('%d can resume', self.uid)
                stream = self.cache.get_append_stream('data')
                self.isResume = True
                return stream
            else:
                log.debug('%d resuming not possible', self.uid)
        else:
            log.error('%d filesize was to big. Downloaded: %d but should be %d', self.uid, self.downloaded, self.size)
            log.debug('%d moving from %s to %s.big', self.uid, self.save_path, self.save_path)
            os.rename(self.save_path, self.save_path + '.big')
            log.info('%d restarting download now', self.uid)
        return None

    def downloadLoop(self, streamFile):
        block_size = 1024  # the amount of bytes to download - initially just 1kb
        retry = 0  # amount of retries for the download - will reset to 0 with each successful download
        while self.downloaded < self.size:
            if self.ended():
                break
            # Download and write
            before = time.time()
            missing = self.size - self.downloaded
            if block_size > missing:
                block_size = missing
            #if self.isResume:
            #    data_block = self.request.raw.read(3)
            #    # if first 3 chars of a resume are "FLV" this is an flv-header and we need to discard
            #    # the first 9 (3+6) bytes
            #    if data_block == "FLV":
            #        data_block = self.request.raw.read(6)
            #        log.warning("Resumed download contains an FLV-header - the stream might contain errors %d", self.uid)
            #        print(data_block)
            #        data_block = self.request.raw.read(block_size)
            #    self.isResume = False
            #else:
            try:
                data_block = self.request.raw.read(block_size)
            except:
                data_block = False
            if not data_block:
                log.info('%d received empty data_block %s %s', self.uid, self.downloaded, self.size)
                retry += 1
                if retry >= self.retries:
                    break
                else:
                    time.sleep(1)
                    del self.__request # reconnect
                continue
            else:
                retry = 0
                data_block_len = len(data_block)
                streamFile.write(data_block)
                self.downloaded += data_block_len

                after = time.time()
                block_size = LargeDownload.best_block_size(after - before, data_block_len)
                block_size = self.apply_limit(after - before, block_size)
                self.response()

    def response(self):
        if 'response' in self.hooks:
            self.hooks["response"](self)

    def finished_success(self):
        self.end()
        if 'finished_success' in self.hooks:
            self.hooks["finished_success"](self)

    def finished_error(self):
        self.end()
        if 'finished_error' in self.hooks:
            self.hooks["finished_error"](self)

    def run(self):
        self.downloaded = self.cache.lookup_size('data')
        if self.downloaded is None:
            self.downloaded = 0
        self.save_path = self.cache.get_path('data')

        if 0 < self.downloaded == self.size:
            self.finished_success()
            return

        if not self.request:
            log.error('%d couldn\'t resolve url', self.uid)
            self.finished_error()
            return

        streamFile = self.resumeDownload()

        if streamFile is None:
            streamFile = self.cache.get_stream('data')
            self.downloaded = 0
            self.position   = 0

        self.downloadLoop(streamFile)
        streamFile.close()

        # end() was called from outside
        if self.ended():
            self.finished_error()
            return

        if self.downloaded != self.size:
            if self.downloaded < self.size:
                error_type = "short"
            else:
                error_type = "long"
            log.error('%d Content too %s: %s/%s bytes', self.uid, error_type, self.downloaded, self.size)
            self.finished_error()
            return
        self.finished_success()
