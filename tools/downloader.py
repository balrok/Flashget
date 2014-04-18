import config
import threading
try:
    import queue
except ImportError:
    import Queue as queue
from tools.helper import SmallId, format_bytes, calc_speed, calc_eta, calc_percent
import os
import time
import sys
from tools.url import LargeDownload
import logging
log = logging.getLogger('downloader')

class Downloader(threading.Thread):
    # internal used
    download_limit = config.dl_instances # will count down to 0
    dl_list = {}               # list of current active downloads

    def __init__(self, download_queue):
        self.download_queue = download_queue  # from this queue we will get all flashfiles
        self.dl_queue       = queue.Queue()   # used for largedownload-communication
        self.mutex_dl_list  = threading.Lock() # used for updating the dl_list, cause we access in multiple threads to this list
        self.small_id       = SmallId(None, 0)
        self.stop           = False # use this to stop this thread
        threading.Thread.__init__(self)
        self.alternativeStreams = {}

    def print_dl_list(self):
        self.mutex_dl_list.acquire()
        log.info('dl-list changed:')
        for i in range(0, len(self.dl_list)):
            if i in self.dl_list:
                log.info('%d : %s', i, self.dl_list[i]['pinfo'].title)
        self.mutex_dl_list.release()

    # this will run as a thread and process all incoming files which com from the downloadqueue
    # it will only initialize and start the largedownloader
    # future watching should be done somewhere else (Downloader.run while loop currently)
    def dl_preprocess(self):
        url_handle = None
        while True:
            if self.download_limit == 0:
                time.sleep(1)
                continue
            try:
                streams = self.download_queue.get(False)
            except:
                if self.stop:
                    break
                time.sleep(1)
                continue

            streamNum = 0
            # basically we just process one stream here.. only if an error occurs in preprocessing we try the other streams
            # self.alternativeStreams is to pass the other streams to post_processing
            for data in streams:
                if self.stop:
                    break
                streamNum += 1
                name, pinfoList, wait_time = data

                next = False
                for pinfo in pinfoList:
                    if self.stop:
                        break
                    if not pinfo.title or not pinfo.stream_url:
                        # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
                        next = True
                        break
                    if not pinfo.subdir:
                        log.error('pinfo.subdir in dl_preprocess missing flashfile: %s', pinfo.stream_url)
                        next = True
                        break

                    downloadfile = os.path.join(config.flash_dir.encode('utf-8'), pinfo.subdir.encode('utf-8'), pinfo.title.encode('utf-8') + b".flv")
                    log.debug('preprocessing download for %s', downloadfile)
                    if os.path.isfile(downloadfile):
                        log.info('already completed')
                        next = True
                        break

                    if not pinfo.flv_url:
                        log.error('url has no flv_url and won\'t be used now %s', pinfo.url)
                        next = True
                        break
                    log.info("flv_url: %s", pinfo.flv_url)

                    self.download_limit -= 1

                    if wait_time:
                        display_pos = self.small_id.new()
                        wait = wait_time - time.time()
                        while wait > 0:
                            if self.stop:
                                break
                            self.logProgress('%s WAITTIME: %02d:%02d' % (pinfo.title, wait / 60, wait % 60), display_pos)
                            time.sleep(1)
                            wait = wait_time - time.time()
                        if self.stop:
                            continue
                        self.small_id.free(display_pos)
                        self.logProgress(' ', display_pos) # clear our old line

                    cacheDir = pinfo.title
                    cacheDir += '_' + pinfo.flv_type

                    url_handle = pinfo.stream.download(queue=self.dl_queue, cache_folder=os.path.join(pinfo.subdir, cacheDir), download_queue=self.download_queue, pinfo=pinfo)

                    if not url_handle: # TODO sometimes flv_call also added this flv to the waitlist - so don't send this error then
                        log.error('we got no urlhandle - hopefully you got already a more meaningfull error-msg :)')
                        self.download_limit += 1
                        next = True
                        break
                    if url_handle.size < 4096: # smaller than 4mb
                        log.error('flashvideo is too small %d - looks like the streamer don\'t want to send us the real video %s', url_handle.size, pinfo.flv_url)
                        self.download_limit += 1
                        next = True
                        break

                    display_pos = self.small_id.new()

                    data_len_str = format_bytes(url_handle.size)
                    start = time.time()
                    tmp   = {'start':start, 'url':url_handle, 'data_len_str':data_len_str, 'pinfo':pinfo, 'display_pos':display_pos,
                             'stream_str':pinfo.flv_type}
                    self.mutex_dl_list.acquire()
                    self.dl_list[url_handle.uid] = tmp
                    self.mutex_dl_list.release()
                    self.print_dl_list()
                    url_handle.start()
                    self.alternativeStreams[url_handle.uid] = streams[streamNum:]
                if next:
                    continue
                break # don't try the other streams
        log.info("Ending Thread: %s.dl_preprocess()", self.__class__.__name__)
        for uid in self.dl_list:
            data = self.dl_list[uid]
            url_handle = data['url']
            url_handle.stop = True
            url_handle.join()
        log.info("Done: %s.dl_preprocess", self.__class__.__name__)

    def dl_postprocess(self, uid):
        dl = self.dl_list[uid]
        url = dl['url']
        pinfo = dl['pinfo']
        display_pos = self.dl_list[uid]['display_pos']
        downloadfile = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
        log.info('%d postprocessing download for %s', uid, downloadfile)
        if url.state & LargeDownload.STATE_FINISHED:
            log.info('moving from %s to %s', url.save_path, downloadfile)
            os.rename(url.save_path, downloadfile)
        elif url.state == LargeDownload.STATE_ERROR: # error means we should try
            if self.alternativeStreams[uid]:
                self.download_queue.put(self.alternativeStreams[uid])
            pass # TODO
        elif url.state != LargeDownload.STATE_ERROR: # a plain error won't be handled here
            log.error('unhandled urlstate %d in postprocess', url.state)
        self.logProgress(' ', self.dl_list[uid]['display_pos']) # clear our old line
        self.mutex_dl_list.acquire()
        del self.dl_list[uid]
        self.mutex_dl_list.release()
        self.print_dl_list()
        self.small_id.free(display_pos)
        self.download_limit += 1

    # process a download: either printing progress or finishing
    def process(self, uid):
        dl  = self.dl_list[uid]
        url = dl['url']
        display_pos = dl['display_pos']
        start = dl['start']
        data_len_str = dl['data_len_str']

        if url.state == LargeDownload.STATE_ALREADY_COMPLETED or url.state & LargeDownload.STATE_FINISHED or url.state & LargeDownload.STATE_ERROR:
            self.dl_postprocess(uid)
            return

        percent_str = calc_percent(url.downloaded, url.size)
        eta_str     = calc_eta(start, url.size - url.position, url.downloaded - url.position)
        speed_str   = calc_speed(start, url.downloaded - url.position)
        downloaded_str = format_bytes(url.downloaded)

        self.logProgress(' [%s%%] %s/%s at %s ETA %s  %s |%s|' % (percent_str, downloaded_str, data_len_str, speed_str,
            eta_str, dl['pinfo'].title, dl['stream_str']), display_pos)

    # will continue all downloads
    def run(self):
        threads = []
        # preprocessing of downloads (own thread to not block current downloads)
        t = threading.Thread(target=self.dl_preprocess)
        threads.append(t)
        t.start()
        while True:
            try:
                uid  = self.dl_queue.get(False)
            except:
                if self.stop:
                    break
                time.sleep(1)
            else:
                if uid in self.dl_list: # it is possible that the worker for dl_queue is faster than this thread and added the uid more than once
                    self.process(uid)
        for i in threads:
            i.join()
        log.info("Ending Thread: %s", self.__class__.__name__)

    def logProgress(self, text, display_pos):
        if text == ' ':
            return
        # this is a syntaxerror in python 2 print(text+"\r", end='', flush=True)
        sys.stdout.write(text+u"\r")
        sys.stdout.flush()
