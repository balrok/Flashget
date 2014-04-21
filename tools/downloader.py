import config
import threading
try:
    import queue
except ImportError:
    import Queue as queue
from tools.helper import SmallId, format_bytes, calc_speed, calc_eta, calc_percent, EndableThreadingClass
import os
import time
import sys
from tools.url import LargeDownload
import logging
log = logging.getLogger('downloader')

# downloader itself is a thread so the website can be parsed and add data in parallel to the downloader
# Downloader consists of two threads
# one is for looking at the streaming sites and adding the download file to current_downloads (pre_process)
# the other one is watching for changes of current_downloads and is printing them or processing (moving) them
class Downloader(EndableThreadingClass):
    # internal used
    download_limit = config.dl_instances # will count down to 0

    def __init__(self):
        # from outside the streams can be put in this queue
        # and the downloader will try to start them
        self.download_queue = queue.Queue()  # from this queue we will get all flashfiles
        # holds all current running downloads with some information
        # access by an uid
        self.current_downloads = {}
        # this queue determines which current download should be processed next
        # it prints out progress information or processes a finished/broken download
        self.process_current_downloads_queue = queue.Queue()
        self.mutex_current_downloads = threading.Lock() # we update it when adding streams and processing finished downloads
        self.small_id       = SmallId(None, 0)
        self.alternativeStreams = {}
        EndableThreadingClass.__init__(self)

    def print_current_downloads(self):
        log.info('dl-list changed:')
        for uid in self.current_downloads:
            log.info('%d : %s', uid, self.current_downloads[uid]['pinfo'].title)

    # returns true if this pinfo is finished with downloading
    def processPinfo(self, pinfo, streamNum, streams):
        if not pinfo.title or not pinfo.stream_url:
            # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
            return False
        if not pinfo.subdir:
            log.error('pinfo.subdir in dl_preprocess missing flashfile: %s', pinfo.stream_url)
            return False

        downloadfile = os.path.join(config.flash_dir.encode('utf-8'), pinfo.subdir.encode('utf-8'), pinfo.title.encode('utf-8') + b".flv")
        if os.path.isfile(downloadfile):
            log.info('already completed %s', downloadfile)
            return True

        if not pinfo.flv_url:
            log.error('url has no flv_url and won\'t be used now %s', pinfo.url)
            return False
        log.info("flv_url: %s", pinfo.flv_url)


        cacheDir = pinfo.title
        cacheDir += '_' + pinfo.flv_type

        url_handle = pinfo.stream.download(cache_folder=os.path.join(pinfo.subdir, cacheDir), download_queue=self.download_queue, pinfo=pinfo)

        if not url_handle: # TODO sometimes flv_call also added this flv to the waitlist - so don't send this error then
            log.error('we got no urlhandle - hopefully you got already a more meaningfull error-msg :)')
            return False
        if url_handle.size < 4096: # smaller than 4mb
            log.error('flashvideo is too small %d - looks like the streamer don\'t want to send us the real video %s', url_handle.size, pinfo.flv_url)
            return False

        self.download_limit -= 1

        data_len_str = format_bytes(url_handle.size)
        start = time.time()
        dlInformation = {'start':start, 'url':url_handle, 'data_len_str':data_len_str, 'pinfo':pinfo, 'stream_str':pinfo.flv_type}
        self.mutex_current_downloads.acquire()
        self.current_downloads[url_handle.uid] = dlInformation
        self.print_current_downloads()
        self.mutex_current_downloads.release()
        self.process_current_downloads_queue.put(url_handle.uid)
        url_handle.start()
        self.alternativeStreams[url_handle.uid] = streams[streamNum:]
        return True


    def downloadQueueProcessing(self):
        while True:
            if self.ended():
                return
            if self.download_limit == 0:
                time.sleep(1)
                continue
            try:
                streams = self.download_queue.get(False)
            except queue.Empty:
                time.sleep(1)
                continue

            streamNum = 0
            # basically we just process one stream here.. only if an error occurs in preprocessing we try the other streams
            # self.alternativeStreams is to pass the other streams to post_processing
            for data in streams:
                streamNum += 1
                name, pinfoList = data
                log.info("Streamdata of %s %s", name, pinfoList)

                gotAllParts = True
                # cycle through all available streams for this one title (can consist of multiple files cd1,cd2,..)
                for pinfo in pinfoList:
                    if self.ended():
                        return
                    if not self.processPinfo(pinfo, streamNum, streams):
                        gotAllParts = False
                        break
                # when we got all parts we don't need all the other streams
                if gotAllParts:
                    break
                else:
                    # TODO if it got at least one part correctly - this one should be deleted
                    pass

    # this will run as a thread and process all incoming files which com from the downloadqueue
    # it will only initialize and start the largedownloader
    # future watching should be done somewhere else (Downloader.run while loop currently)
    def dl_preprocess(self):
        self.downloadQueueProcessing()
        log.info("Ending Thread: %s.dl_preprocess()", self.__class__.__name__)
        for uid in self.current_downloads:
            self.current_downloads[uid]['url'].end()
            self.current_downloads[uid]['url'].join()
        log.info("Done: %s.dl_preprocess", self.__class__.__name__)

    def dl_postprocess(self, uid):
        dl = self.current_downloads[uid]
        url = dl['url']
        pinfo = dl['pinfo']
        log.info('%d postprocessing download for %s', uid, pinfo.title)
        if url.state & LargeDownload.STATE_FINISHED:
            downloadfile = os.path.join(config.flash_dir.encode('utf-8'), pinfo.subdir.encode('utf-8'), pinfo.title.encode('utf-8') + b".flv")
            log.info('moving from %s to %s', url.save_path, downloadfile)
            os.rename(url.save_path, downloadfile)
        elif url.state == LargeDownload.STATE_ERROR: # error means we should try
            if self.alternativeStreams[uid]:
                self.download_queue.put(self.alternativeStreams[uid])
        self.logProgress(' ', uid) # clear our old line
        self.mutex_current_downloads.acquire()
        del self.current_downloads[uid]
        self.print_current_downloads()
        self.mutex_current_downloads.release()
        self.download_limit += 1

    # process a download: either printing progress or finishing
    def process(self, uid):
        dl = self.current_downloads[uid]
        url = dl['url']
        start = dl['start']
        data_len_str = dl['data_len_str']

        if LargeDownload.STATE_FINISHED or url.state & LargeDownload.STATE_ERROR:
            self.dl_postprocess(uid)
            return False

        percent_str = calc_percent(url.downloaded, url.size)
        eta_str     = calc_eta(start, url.size - url.position, url.downloaded - url.position)
        speed_str   = calc_speed(start, url.downloaded - url.position)
        downloaded_str = format_bytes(url.downloaded)
        self.logProgress(' [%s%%] %s/%s at %s ETA %s  %s |%s|' % (percent_str, downloaded_str, data_len_str, speed_str,
            eta_str, dl['pinfo'].title, dl['stream_str']), uid)
        return True

    # will continue all downloads
    def run(self):
        # preprocessing of downloads becomes own thread to not block current downloads
        preprocessor = threading.Thread(target=self.dl_preprocess)
        preprocessor.start()
        while True:
            try:
                uid = self.process_current_downloads_queue.get(False)
            except Exception:
                if self.ended():
                    break
            else:
                if self.process(uid):
                    self.process_current_downloads_queue.put(uid)
            time.sleep(2)
        preprocessor.join()
        log.info("Ending Thread: %s", self.__class__.__name__)

    def logProgress(self, text, dummy_uid):
        if text == ' ':
            return
        sys.stdout.write(text+u"\r")
        sys.stdout.flush()
