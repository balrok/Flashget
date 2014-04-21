import config
import threading
try:
    import queue
except ImportError:
    import Queue as queue
from tools.helper import format_bytes, calc_speed, calc_eta, calc_percent, EndableThreadingClass
import os
import time
import sys
import logging
log = logging.getLogger('downloader')

# downloader itself is a thread so the website can be parsed and add data in parallel to the downloader
# the printing and processing of finished downloads is initiaded from the downloads themselfes
# they are threads and callback through hooks
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
        self.mutex_current_downloads = threading.Lock() # we update it when adding streams and processing finished downloads
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

        cacheDir = "%s_%s" % (pinfo.title, pinfo.flv_type)

        url_handle = pinfo.stream.download(
                cache_folder=os.path.join(pinfo.subdir, cacheDir),
                download_queue=self.download_queue,
                pinfo=pinfo,
                sleep=self.endableSleep,
                hooks = dict(response = self.downloadProgressCallback,
                    finished_success = self.processSuccessCallback,
                    finished_error = self.processErrorCallback
                    ))

        if not url_handle:
            log.error('we got no urlhandle - hopefully you got already a more meaningfull error-msg :)')
            return False
        if url_handle.size < 4096: # smaller than 4mb
            log.error('flashvideo is too small %d - looks like the streamer don\'t want to send us the real video %s', url_handle.size, pinfo.flv_url)
            return False

        self.download_limit -= 1

        start = time.time()
        dlInformation = {'start':start, 'url':url_handle, 'pinfo':pinfo, 'stream_str':pinfo.flv_type}
        self.mutex_current_downloads.acquire()
        self.current_downloads[url_handle.uid] = dlInformation
        self.print_current_downloads()
        self.mutex_current_downloads.release()
        url_handle.start()
        self.alternativeStreams[url_handle.uid] = streams[streamNum:]
        return True

    # will be assigned to the url_handle as callback
    def downloadProgressCallback(self, url_handle):
        dl = self.current_downloads[url_handle.uid]
        start = dl['start']

        percent_str = calc_percent(url_handle.downloaded, url_handle.size)
        eta_str     = calc_eta(start, url_handle.size - url_handle.position, url_handle.downloaded - url_handle.position)
        speed_str   = calc_speed(start, url_handle.downloaded - url_handle.position)
        downloaded_str = format_bytes(url_handle.downloaded)
        self.logProgress(' [%s%%] %s/%s at %s ETA %s  %s |%s|' % (percent_str, downloaded_str, format_bytes(url_handle.size), speed_str,
            eta_str, dl['pinfo'].title, dl['stream_str']), url_handle.uid)


    def processErrorCallback(self, url):
        uid = url.uid
        pinfo = self.current_downloads[uid]['pinfo']
        log.info('%d postprocessing download for %s', uid, pinfo.title)
        if not url.ended() and self.alternativeStreams[uid]:
            log.info("Because of downloading error - add %d alternative streams back to the queue", len(self.alternativeStreams[uid]))
            self.download_queue.put(self.alternativeStreams[uid])
        self.dl_postprocess(uid)

    def processSuccessCallback(self, url):
        uid = url.uid
        pinfo = self.current_downloads[uid]['pinfo']
        log.info('%d postprocessing download for %s', uid, pinfo.title)
        downloadfile = os.path.join(config.flash_dir.encode('utf-8'), pinfo.subdir.encode('utf-8'), pinfo.title.encode('utf-8') + b".flv")
        log.info('moving from %s to %s', url.save_path, downloadfile)
        os.rename(url.save_path, downloadfile)
        self.dl_postprocess(uid)

    def dl_postprocess(self, uid):
        self.logProgress(' ', uid) # clear our old line
        if not self.ended():
            self.mutex_current_downloads.acquire()
            del self.current_downloads[uid]
            self.print_current_downloads()
            self.mutex_current_downloads.release()
        self.download_limit += 1

    def endableSleep(self, timeout):
        if self.ended(True, timeout):
            log.info("Ended a sleeping prematurely")
            return False
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
                if self.ended():
                    return
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
    def run(self):
        self.downloadQueueProcessing()
        log.info("Ending Thread: %s.dl_preprocess()", self.__class__.__name__)
        self.mutex_current_downloads.acquire()
        for uid in self.current_downloads:
            self.current_downloads[uid]['url'].end()
            self.current_downloads[uid]['url'].join()
        self.mutex_current_downloads.release()
        log.info("Done: %s.dl_preprocess", self.__class__.__name__)


    def logProgress(self, text, dummy_uid):
        if text == ' ':
            return
        sys.stdout.write(text+u"\r")
        sys.stdout.flush()
