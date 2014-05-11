import config
from tools.helper import format_bytes, calc_speed, calc_eta, calc_percent, open
import os
import time
import sys
import logging
log = logging.getLogger(__name__)
import tools.commandline as commandline

# the printing and processing of finished downloads is initiaded from the downloads themselfes
# they are threads and callback through hooks
class Downloader(object):
    download_limit = config.dl_instances # will count down to 0

    def __init__(self):
        # streams can be put in this queue
        # and the downloader will try to start them
        self.download_queue = []
        # holds all current running downloads with some information
        # access by an uid
        self.current_downloads = {}
        # holds alternative streams of the current downloads
        self.alternativeStreams = {}
        # holds the other parts of the current download
        self.otherParts = {}

    def print_current_downloads(self):
        log.info('dl-list changed:')
        def callback(dl):
            log.info('%d : %s', dl["uid"], dl['pinfo'].title)
        self.iterateCurrentDownloads(callback)

    def iterateCurrentDownloads(self, callback):
        allUid = self.current_downloads.keys()
        for uid in allUid:
            try:
                dl = self.current_downloads[uid]
            except KeyError:
                pass
            else:
                callback(dl)

    # get the final path, were the download will be moved
    # when filePath is true it will return the actual path to the file
    # else the containing directory
    def getFinalPath(self, pinfo, filePath=True):
        downloadPath = os.path.join(config.flash_dir, pinfo.subdir)
        if filePath:
            return os.path.join(downloadPath, pinfo.title + ".flv")
        return downloadPath

    # will do the preparations for a new download
    # create the final path
    def prepareStartDownload(self, url_handle, pinfo, downloadPath):
        self.download_limit -= 1
        start = time.time()
        dlInformation = {'start':start, 'url':url_handle, 'pinfo':pinfo, 'uid':url_handle.uid}
        self.current_downloads[url_handle.uid] = dlInformation
        self.print_current_downloads()

        downloadPath = os.path.abspath(downloadPath)
        if os.path.isdir(downloadPath) is False:
            try:
                os.makedirs(downloadPath)
            except OSError:
                log.error('couldn\'t create subdir in %s', downloadPath)
                return False
            with open(os.path.join(downloadPath, '.flashget_log'), 'a', encoding="utf-8") as f:
                f.write(commandline.get_log_line() + '\n')
        return True

    # returns true if this pinfo is finished with downloading
    def processDownload(self, pinfo, downloadPath, stream):
        if not downloadPath or not stream or not stream.flvUrl:
            log.warning("either no downloadPath, stream, url")
            return None

        log.info("flv_url: %s", stream.flvUrl)

        url_handle = stream.download(
                cache_folder = "%s_%s_%s" % (os.path.basename(downloadPath), stream.ename, hash(stream.flvUrl)),
                pinfo = pinfo,
                hooks = dict(response = self.downloadProgressCallback,
                    finished_success = self.processSuccessCallback,
                    finished_error = self.processErrorCallback
                    ))

        if not url_handle:
            log.error('we got no urlhandle - hopefully you got already a more meaningfull error-msg :)')
            return None
        if url_handle.size < 4096: # smaller than 4mb
            log.error('flashvideo is too small %d - looks like the streamer don\'t want to send us the real video %s', url_handle.size, stream.flvUrl)
            return None

        if self.prepareStartDownload(url_handle, pinfo, downloadPath):
            url_handle.start()
        return url_handle

    # will be assigned to the url_handle as callback
    def downloadProgressCallback(self, url_handle):
        dl = self.current_downloads[url_handle.uid]
        start = dl['start']

        percent_str = calc_percent(url_handle.downloaded, url_handle.size)
        eta_str     = calc_eta(start, url_handle.size - url_handle.position, url_handle.downloaded - url_handle.position)
        speed_str   = calc_speed(start, url_handle.downloaded - url_handle.position)
        downloaded_str = format_bytes(url_handle.downloaded)
        self.logProgress(' [%s%%] %s/%s at %s ETA %s  %s' % (percent_str, downloaded_str, format_bytes(url_handle.size), speed_str,
            eta_str, dl['pinfo'].title), url_handle.uid)


    def processErrorCallback(self, url):
        uid = url.uid
        pinfo = self.current_downloads[uid]['pinfo']
        log.info('%d postprocessing download for %s', uid, pinfo.title)
        if not url.ended() and self.alternativeStreams[uid]:
            log.info("Because of downloading error - add %d alternative streams back to the queue", len(self.alternativeStreams[uid]))
            self.stopAndRemoveDownloads(*self.otherParts[uid])
            self.download_queue.append(self.alternativeStreams[uid])
        self.dl_postprocess(uid)

    def checkAllPartsAreFinished(self, uid):
        allEnded = True
        allUrlHandle = self.otherParts[uid][1]
        for url_handle in allUrlHandle:
            if not url_handle.ended():
                allEnded = False
                break
        return allEnded


    def processSuccessCallback(self, url):
        uid = url.uid
        pinfo = self.current_downloads[uid]['pinfo']
        log.info('%d postprocessing download for %s', uid, pinfo.title)
        downloadfile = self.getFinalPath(pinfo)
        log.info('moving from %s to %s', url.save_path, downloadfile)
        os.rename(url.save_path, downloadfile)

        # write the log
        downloadPath = self.getFinalPath(pinfo, False)
        with open(os.path.join(downloadPath, '.flashget_log'), 'a', encoding="utf-8") as f:
            f.write("success %s \n" % pinfo.title)
            if self.checkAllPartsAreFinished(uid):
                f.write("all success\n")
        self.dl_postprocess(uid)

    def dl_postprocess(self, uid):
        self.logProgress(' ', uid) # clear our old line
        del self.current_downloads[uid]
        self.print_current_downloads()
        self.download_limit += 1

    def downloadQueueProcessing(self):
        streams = self.download_queue.pop()

        streamNum = 0
        # basically we just process one stream here.. only if an error occurs in preprocessing we try the other streams
        # self.alternativeStreams is to pass the other streams to post_processing
        for infoList in streams:
            streamNum += 1
            allUrlHandle = []
            # cycle through all available streams for this one title (can consist of multiple files cd1,cd2,..)
            for data in infoList:
                pinfo = data['pinfo']
                downloadPath = data['downloadPath']
                stream = data['stream']
                if os.path.isfile(downloadPath):
                    log.info('already completed %s', downloadPath)
                    continue
                url_handle = self.processDownload(pinfo, downloadPath, stream)
                allUrlHandle.append(url_handle)
                if url_handle is None:
                    break
            # when we got all parts we don't need all the other streams
            if None in allUrlHandle:
                # one part could not be started - so stop and remove all other parts
                self.stopAndRemoveDownloads(allUrlHandle, infoList)
            else:
                for url_handle in allUrlHandle:
                    self.alternativeStreams[url_handle.uid] = streams[streamNum:]
                    self.otherParts[url_handle.uid] = (infoList, allUrlHandle)
                break

    def stopAndRemoveDownloads(self, allUrlHandle, infoList):
        for url_handle in allUrlHandle:
            if url_handle is not None:
                url_handle.end()
                url_handle.join()
        for data in infoList:
            downloadPath = data['downloadPath']
            if os.path.isfile(downloadPath):
                os.remove(downloadPath)

    # this will run as a thread and process all incoming files which com from the downloadqueue
    # it will only initialize and start the largedownloader
    # future watching should be done somewhere else (Downloader.run while loop currently)
    def run(self):
        while True:
            if len(self.download_queue) > 0:
                if self.download_limit > 0:
                    self.downloadQueueProcessing()
            elif len(self.current_downloads) == 0:
                break
            try:
                time.sleep(1)
            except:
                break

        log.info("Ending Downloader")
        def callback(dl):
            dl["url"].end()
            dl["url"].join()
        self.iterateCurrentDownloads(callback)
        log.info("Done with ending Downloader")

    def logProgress(self, text, dummy_uid):
        if text == ' ':
            return
        sys.stdout.write(text+u"\r")
        sys.stdout.flush()
