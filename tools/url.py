# vim: set fileencoding=utf-8 :
import config
from cache import Cache
import requests

import logging

log = logging.getLogger('urlDownload')

def void(*args):
    return None

# writes data,redirection into cache
class UrlMgr(object):

    def __init__(self, *args, **kwargs):
        if args != ():
            args = args[0]
        if kwargs != {}:
            args = kwargs
        # those variables are used intern, to access them remove the __ (example: url.request)
        self.clear_connection()

        cache_dir = config.cache_dir
        self.referer = None
        self.cookies = {}
        self.http_version = None
        self.post = ''
        self.url  = args['url']
        self.content_type = None
        self.encoding = ''
        self.keepalive = True
        self.timeout = 10

        if 'referer' in args:
            self.referer = args['referer']
        if 'cookies' in args:
            self.cookies = args['cookies']
        if 'http_version' in args:
            self.http_version = args['http_version']
        if 'post' in args:
            self.post = args['post']
        if 'content_type' in args:
            self.content_type = args['content_type']
        if 'encoding' in args:
            self.encoding = args['encoding']
        if 'keepalive' in args:
            self.keepalive = args['keepalive']
        if 'timeout' in args:
            self.timeout = args['timeout']
        subdirs = self.url.split('/')

        del subdirs[0]
        if self.post:
            subdirs.append(str(self.post).replace('{','').replace('}',''))

        self.cache = Cache(cache_dir, subdirs)

        if 'cache_writeonly' in args and args['cache_writeonly']:
            self.setCacheWriteOnly()
        if 'cache_readonly' in args and args['cache_readonly']:
            self.setCacheWriteOnly()
        if 'nocache' in args and args['nocache']:
            self.setCacheWriteOnly()
            self.setCacheReadOnly()

    @staticmethod
    def filterData(data):
        if "\0" in data:
            if len(data) < 100:
                # when <p> and </p> inside data it is not binary
                if '<p>' in data and '</p>' in data:
                    return False
            raise Exception
            log.info("filter binary file")
            return True
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
            except(Exception):
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

        header = {}
        header['user-agent'] = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1'
        header['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        header['accept-language'] = 'en-us,en;q=0.5'
        header['accept-charset'] = 'utf-8,ISO-8859-1;q=0.7,*;q=0.7'
        if self.content_type:
            header['content-type'] = self.content_type
        if self.referer:
            header['referer'] = self.referer
        if self.position:
            header['range'] = 'bytes=%d-' % self.position
        try:
            if self.post: # TODO I think self.post is asd=123%xyz=jkl but should be an object
                self.__request = requests.post(self.url, data=self.post, cookies=self.cookies, timeout=self.timeout)
            else:
                self.__request = requests.get(self.url, cookies=self.cookies, timeout=self.timeout)
        except(requests.exceptions.Timeout):
            self.__data = ''
            self.cache.write('data', self.__data)
            return None

        return self.__request

    def get_redirection(self):
        self.__redirection = self.cache.lookup('redirection')
        if not self.__redirection:
            if len(self.requests.history) > 0:
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
                    log.info("Data from %s was filtered" % (origUrl))
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


import threading
from cache import FileCache
from helper import textextract
import os
import time

class LargeDownload(UrlMgr, threading.Thread):
    uids = 0
    STATE_ERROR = 1
    STATE_FINISHED = 2
    STATE_ALREADY_COMPLETED = 4
    STATE_DOWNLOAD_CONTINUE = 8
    STATE_DOWNLOAD = 16

    def __init__(self, *args, **kwargs):
        if args != ():
            args = args[0]
        if kwargs != {}:
            args = kwargs
        self.stop = False
        threading.Thread.__init__(self)
        UrlMgr.__init__(self, args)
        self.timeout = 120

        cache_dir2 = config.cache_dir_for_flv

        if 'cache_folder' not in args:
            cache_folder = self.url
        else:
            cache_folder = args['cache_folder']
        self.cache = FileCache(cache_dir2, [cache_folder])

        self.downloaded = 0
        self.save_path = '' # we will store here the savepath of the downloaded stream
        self.queue = args['queue']
        self.uid = LargeDownload.uids # TODO: we should push to queue (id, key:value) then this can be later used for multiprocessing
        LargeDownload.uids += 1
        self.state = 0
        self.megavideo = False
        if 'megavideo' in args:
            self.megavideo = args['megavideo']
        self.reconnect_wait = 0
        if 'reconnect_wait' in args:
            self.reconnect_wait = args['reconnect_wait']
        self.retries= 0
        if 'retries' in args:
            self.retries= args['retries']
        log.debug('%d initializing Largedownload with url %s and cachedir %s' % (self.uid, self.url, cache_dir2))

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
        ''' This function is a preprocessor for get_request in case of resume. '''
        if self.megavideo: # megavideo is handled special
            log.info('%d resuming megavideo' % self.uid)
            if not self.url.endswith('/'):
                self.url += '/'
            self.url += str(self.position)
            return

    def got_requested_position(self):
        if self.megavideo: # megavideo won't provide us usefull information here
            return True
        if not self.request:
            return False
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
            log.info('%d check if we got requested position, requested: %d got: %d => OK' % (self.uid, check, self.position))
            return True
        else:
            log.error('%d check if we got requested position, requested: %d got: %d => WRONG' % (self.uid, check, self.position))
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
            return new_min
        return int(rate)

    def run(self):
        self.downloaded = self.cache.lookup_size('data')
        self.save_path  = self.cache.get_path('data')
        stream = None
        if self.downloaded > 0:
            if self.size == self.downloaded:
                self.state = LargeDownload.STATE_ALREADY_COMPLETED | LargeDownload.STATE_FINISHED
                self.queue.put(self.uid)
                return
            elif self.size > self.downloaded:
                # try to resume
                log.debug('%d trying to resume' % self.uid)
                self.position = self.downloaded
                if self.got_requested_position():
                    log.debug('%d can resume' % self.uid)
                    stream = self.cache.get_append_stream('data')
                    self.state |= LargeDownload.STATE_DOWNLOAD_CONTINUE
                    if self.megavideo:
                        # after resume megavideo will resend the FLV-header, which looks like this:
                        #FLV^A^E^@^@^@>--
                        # it's exactly 9 chars, so we will now drop the first 9 bytes
                        self.request.raw.read(9)
                else:
                    log.debug('%d resuming not possible' % self.uid)
            else:
                log.error('%d filesize was to big. Downloaded: %d but should be %d' % (self.uid, self.downloaded, self.size))
                log.debug('%d moving from %s to %s.big' % (self.uid, self.save_path, self.save_path))
                os.rename(self.save_path, self.save_path + '.big')
                log.info('%d restarting download now' % self.uid)

        self.state |= LargeDownload.STATE_DOWNLOAD
        if stream is None:
            stream = self.cache.get_stream('data')
            self.downloaded = 0
            self.position   = 0

        block_size = 1024
        #start = time.time()
        abort = 0

        if not self.request:
            log.error('%d couldn\'t resolve url' % self.uid)
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.uid)
            return

        data_block_len = 0
        while self.downloaded < self.size:
            if self.stop:
                break
            # Download and write
            before = time.time()
            missing = self.size - self.downloaded
            if block_size > missing:
                block_size = missing
            data_block = self.request.raw.read(block_size)
            after = time.time()
            if not data_block:
                log.info('%d received empty data_block %s %s' % (self.uid, self.downloaded, self.size))
                abort += 1
                if abort >= self.retries:
                    break
                else:
                    time.sleep(self.reconnect_wait)
                    del self.request # reconnect
                continue
            else:
                abort = 0

                data_block_len = len(data_block)
                stream.write(data_block)

                self.downloaded += data_block_len
                block_size = LargeDownload.best_block_size(after - before, data_block_len)
                self.queue.put(self.uid)

        try: # TODO maybe drop this try, i've never seen an exception here
            stream.close()
        except (OSError, IOError), err:
            log.error('%d unable to write video data: %d %s %s' % (self.uid, err, OSError, IOError))
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.uid)
            return

        if self.stop:
            self.state = LargeDownload.STATE_ERROR
            return

        if (self.downloaded) != self.size:
            if self.downloaded < self.size:
                log.error('%d Content to short: %s/%s bytes - last downloaded %d' % (self.uid, self.downloaded, self.size, data_block_len))
                if self.megavideo and data_block_len > 0:
                    # if the timelimit from megavideo starts, it will sends me rubbish, if the timelimit is at the beginning of the
                    # download, i get:
                    #FLV     �
                    #onCuePoinnameMVcode
                    #parameterwait  1747played  4320mb93vidcount641  time@>typeevent
                    # else i won't get the "FLV"-header part, but the other things looking the same
                    stream = self.cache.read_stream('data')
                    if data_block_len < 200:
                        junk_start = self.downloaded - data_block_len
                    else:
                        junk_start = self.downloaded - 200 # mostly this special thing is ~171bytes, but it's not bad to remove a bit more
                        if junk_start < 0:
                            junk_start = 0
                    stream.seek(junk_start)
                    junk_data = stream.read()
                    if junk_data.find('FLV') == -1:
                        log.error("no waittime maybe they just have a temporary problem?")

                    log.error('%d megavideo don\'t let us download for some minutes now data_block_len: %d' % (self.uid, data_block_len))
                    waittime = textextract(junk_data, 'wait', 'played') # result: ^B^@^F   811^@^F
                    #self.cache.write('waittime', waittime)
                    if waittime:
                        waittime = waittime[5:-2]
                    else:
                        log.error("no waittime")
                        log.error(junk_data)
                        waittime = "123"
                    # cause the waittime can be 1000 or 100 or 1 i need to check when the first integer will start
                    len_waittime = len(waittime)
                    i = 0
                    for i in xrange(0, len_waittime):
                        if waittime[i:i+1] not in '123456789':
                            i += 1
                        else:
                            break
                    waittime = int(waittime[i:])

                    if waittime > 0:
                        log.warning('%d we need to wait %d minutes and %d seconds' % (self.uid, waittime / 60, waittime % 60))
                        config.megavideo_wait = time.time() + waittime
                    else:
                        log.error('%d couldnt extract waittime' % self.uid)
                    stream.close()
                    stream = self.cache.truncate('data', junk_start)
            else:
                log.error('%d Content to long: %s/%s bytes' % (self.uid, self.downloaded, self.size))
            self.state = LargeDownload.STATE_ERROR
            self.queue.put(self.uid)
            return
        self.state = LargeDownload.STATE_FINISHED
        self.queue.put(self.uid)

