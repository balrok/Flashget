# vim: set fileencoding=utf-8 :
import config
from tools.cache import Cache
import requests

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

# writes data,redirection into cache
class UrlMgr(object):
    isStream = False

    def __init__(self, **kwargs):
        # those variables are used intern, to access them remove the __ (example: url.request)
        self.clear_connection()

        cache_dir = config.cache_dir
        self.url  = kwargs['url']

        subdirs = self.url.split('/')
        subdirs[0] = cache_dir

        if 'post' in kwargs:
            subdirs.append("POST %d" % hash(kwargs["post"]))

        self.cache = Cache(subdirs)

        if 'cache_writeonly' in kwargs and kwargs['cache_writeonly']:
            self.setCacheWriteOnly()
        if 'cache_readonly' in kwargs and kwargs['cache_readonly']:
            self.setCacheReadOnly()
        if 'nocache' in kwargs and kwargs['nocache']:
            self.setCacheWriteOnly()
            self.setCacheReadOnly()

        self.kwargs = kwargs

    def initHeader(self):
        header = {}
        header['user-agent'] = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1'
        header['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        header['accept-language'] = 'en-us,en;q=0.5'
        header['accept-charset'] = 'utf-8;q=0.7'
        if self.position:
            header['range'] = 'bytes=%d-' % self.position
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
            except:
                pass
        requestArgs["headers"] = self.initHeader()
        requestArgs["stream"] = self.isStream
        return requestArgs

    @staticmethod
    def filterData(data):
        if "\0" in data:
            if len(data) < 100:
                # when <p> and </p> inside data it is not binary
                if '<p>' in data and '</p>' in data:
                    return False
            log.info("filter binary file")
            raise Exception
        if data == "":
            log.info("no length")
            return True

    def setCacheWriteOnly(self):
        self.cache.lookup_size = void
        self.cache.lookup = void
    def setCacheReadOnly(self):
        self.cache.write = void

    def clearCache(self):
        for i in ('data', 'redirection', 'size'):
            try:
                self.cache.remove(i)
            except Exception:
                pass

    def clear_connection(self):
        self.__data = None
        self.__request = None
        self.__size = None
        self.__redirection = ''
        self.position = 0

    def del_request(self):
        self.__request = None

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

        return self.__request

    def get_redirection(self):
        self.__redirection = self.cache.lookup('redirection')
        if not self.__redirection:
            if len(self.request.history) > 0:
                self.__redirection = self.request.url
            else:
                self.__redirection = ''
            self.cache.write('redirection', self.__redirection)
        return self.__redirection

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
                if self.filterData(self.__data):
                    if self.redirection:
                        origUrl = self.request.history[0].url
                    else:
                        origUrl = self.request.url
                    log.info("Data from %s was filtered", origUrl)
                    return ''
                self.cache.write('data', self.__data)
        return self.__data

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

    def get_response_cookies(self):
        if not self.request:
            log.error('trying to get response cookies, but no request was given')
            return []
        return self.request.cookies.get_dict()

    def get_response_status(self):
        if not self.request:
            log.error('trying to get response status, but no request was given')
            return []
        return self.request.status_code

    request = property(fget=get_request, fdel=del_request)
    data = property(fget=get_data)
    size = property(fget=get_size)
    redirection = property(fget=get_redirection)


from tools.cache import FileCache
from tools.helper import textextract, EndableThreadingClass
import os
import time

class LargeDownload(UrlMgr, EndableThreadingClass):
    uids = 0
    STATE_ERROR = 1
    STATE_FINISHED = 2
    STATE_ALREADY_COMPLETED = 4
    STATE_DOWNLOAD_CONTINUE = 8
    STATE_DOWNLOAD = 16
    isStream = True
    retries = 1 # maximum of retries for a file 

    def __init__(self, **kwargs):
        UrlMgr.__init__(self, **kwargs)
        self.timeout = 10

        cache_dir2 = config.cache_dir_for_flv

        cache_folder = self.url
        if 'cache_folder' in kwargs:
            cache_folder = kwargs['cache_folder']
        self.cache = FileCache([cache_dir2, cache_folder])

        self.hooks = {}
        if 'hooks' in kwargs:
            self.hooks = kwargs['hooks']
        self.downloaded = 0
        self.save_path = '' # we will store here the savepath of the downloaded stream
        self.uid = LargeDownload.uids
        LargeDownload.uids += 1
        self.state = 0
        log.debug('%d initializing Largedownload with url %s and cachedir %s', self.uid, self.url, cache_dir2)
        EndableThreadingClass.__init__(self)

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
                    del self.request    # set this to None so that next request forces a redownload - and will resume then
                    self.set_resume()       # handle special resume-cases
        self.__dict__[name] = value

    def set_resume(self):
        if self.position == 0:
            return

    def got_requested_position(self):
        # this function will just look if the server realy let us continue at our requested position
        if self.get_response_status() == 206: # 206 - Partial Content ... i think if the server sends us this response, he also accepted our range
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

    def resumeDownload(self):
        if self.size > self.downloaded:
            # try to resume
            log.debug('%d trying to resume', self.uid)
            self.position = self.downloaded
            if self.got_requested_position():
                log.debug('%d can resume', self.uid)
                stream = self.cache.get_append_stream('data')
                self.state |= LargeDownload.STATE_DOWNLOAD_CONTINUE
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
        block_size = 1024 # the amount of bytes to download - initially just 1kb
        retry = 0 # amount of retries for the download - will reset to 0 with each successful download
        while self.downloaded < self.size:
            if self.ended():
                break
            # Download and write
            before = time.time()
            missing = self.size - self.downloaded
            if block_size > missing:
                block_size = missing
            data_block = self.request.raw.read(block_size)
            after = time.time()
            if not data_block:
                log.info('%d received empty data_block %s %s', self.uid, self.downloaded, self.size)
                retry += 1
                if retry >= self.retries:
                    break
                else:
                    time.sleep(1)
                    del self.request # reconnect
                continue
            else:
                retry = 0

                data_block_len = len(data_block)
                streamFile.write(data_block)

                self.downloaded += data_block_len
                block_size = LargeDownload.best_block_size(after - before, data_block_len)
                self.response()

    def response(self):
        if 'response' in self.hooks:
            self.hooks["response"](self)

    def finished_success(self):
        if 'finished_success' in self.hooks:
            self.hooks["finished_success"](self)

    def finished_error(self):
        if 'finished_error' in self.hooks:
            self.hooks["finished_error"](self)

    def run(self):
        self.downloaded = self.cache.lookup_size('data')
        if self.downloaded is None:
            self.downloaded = 0
        self.save_path = self.cache.get_path('data')

        if self.downloaded > 0 and self.size == self.downloaded:
            self.state = LargeDownload.STATE_ALREADY_COMPLETED | LargeDownload.STATE_FINISHED
            self.finished_success()
            return

        if not self.request:
            log.error('%d couldn\'t resolve url', self.uid)
            self.state = LargeDownload.STATE_ERROR
            self.finished_error()
            return

        streamFile = self.resumeDownload()

        self.state |= LargeDownload.STATE_DOWNLOAD
        if streamFile is None:
            streamFile = self.cache.get_stream('data')
            self.downloaded = 0
            self.position   = 0

        self.downloadLoop(streamFile)
        streamFile.close()

        # end() was called from outside
        if self.ended():
            self.state = LargeDownload.STATE_ERROR
            self.finished_error()
            return

        if self.downloaded != self.size:
            if self.downloaded < self.size:
                errorType = "short"
            else:
                errorType = "long"
            log.error('%d Content too %s: %s/%s bytes', self.uid, errorType, self.downloaded, self.size)
            self.state = LargeDownload.STATE_ERROR
            self.finished_error()
            return
        self.state = LargeDownload.STATE_FINISHED
        self.finished_success()
