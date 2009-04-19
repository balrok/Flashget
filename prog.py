# -*- coding: utf-8 -*-

import os
import time
import re
import sys
import math
import string
import tools.url as Url
from tools.url import UrlMgr
from tools.small_ids import SmallId

import config

from tools.logging import LogHandler

import threading, thread
import Queue

log = LogHandler('Main')


def usage():
    log.error("usage: ./get.py AnimeLoadslink")
    sys.exit(0)


def main():
    import tools.video_get as video_get
    log = LogHandler('Main')

    urllist = []

    from tools.helper import textextractall
    if len(sys.argv) < 2:
        url = UrlMgr({'url': 'http://anime-loads.org/anime-serien-gesamt.html', 'log': log})
        if not url.data:
            log.error('anime-loads down')
            sys.exit(1)
        #<a href="anime-serien/_hacklegend.html">
        links = textextractall(url.data, 'td><a href="anime-serien/', '.html"')
        for i in links:
            config.win_mgr.list.add_line(i)
        time.sleep(100)
    else:
        if sys.argv[1].find('anime-loads') >= 0:
            type = video_get.TYPE_H_ANIMELOADS
            if sys.argv[1].find('/streams/') < 0:
                # <a href="../streams/_hacksign/003.html"
                # user added video-overview-url
                url = UrlMgr({'url': sys.argv[1], 'log': log})
                if not url.data:
                    usage()
                links = textextractall(url.data, '<a href="../streams/','"')
                if len(links) > 0:
                    for i in links:
                        tmp = video_get.VideoInfo('http://anime-loads.org/streams/' + str(i), type)
                        urllist.append(tmp)
                        log.info('added url: ' + str(tmp.num) + ' ' + tmp.pageurl)
            else:
                urllist.append(video_get.VideoInfo(sys.argv[1], type))
        elif sys.argv[1].find('animekiwi') >= 0:
            type = video_get.TYPE_H_ANIMEKIWI
            if sys.argv[1].find('watch') == -1:     # its a bit difficult to find out what the link means :-/
                # http://www.animekiwi.com/kanokon/
                url = UrlMgr({'url': sys.argv[1], 'log': log})
                if not url.data:
                    usage()
                #<a href="/watch/kanokon-episode-12/" target="_blank">Kanokon Episode 12</a>
                links = textextractall(url.data, '<a href="/watch/','"')
                if len(links) > 0:
                    for i in links:
                        tmp = video_get.VideoInfo('http://animekiwi.com/watch/' + str(i), type)
                        urllist.append(tmp)
                        log.info('added url: ' + str(tmp.num) + ' ' + tmp.pageurl)
                    urllist = urllist[::-1] # cause the page shows them in the wrong order ~_~

            else:
                urllist.append(video_get.VideoInfo(sys.argv[1], type))


    if len(urllist)==0:
        log.error('no urls found')
        usage()

    download_queue = Queue.Queue(0)
    flashWorker = FlashWorker(download_queue)
    flashWorker.start()
    config.win_mgr.threads.append(flashWorker)
    for pinfo in urllist:
        if pinfo.type == video_get.TYPE_H_ANIMELOADS:
            aObj = video_get.AnimeLoads(pinfo, log)
        elif pinfo.type == video_get.TYPE_H_ANIMEKIWI:
            aObj = video_get.AnimeKiwi(pinfo, log)
        else:
            continue

        if aObj.error:
            del aObj
            continue
# urlextract/
        if aObj.type == 'EatLime':
            tmp = video_get.EatLime(aObj.flv_url, log)
        elif aObj.type == 'Veoh':
            tmp = video_get.Veoh(aObj.flv_url, log)
        elif aObj.type == 'MegaVideo':
            tmp = video_get.MegaVideo(aObj.flv_url, log)
        else:
            log.warning("strange video-type - continue")
            continue

        pinfo.flv_url = tmp.flv_url
        size = tmp.size
        del tmp
        if not pinfo.flv_url:
            continue
        download_queue.put(pinfo, True)
# /urlextract


class FlashWorker(threading.Thread):

    def __init__(self, queue, log_ = log):
        self.dl_queue = Queue.Queue()
        self.in_queue = queue
        self.dl_list = {}
        self.log = LogHandler('FlashWorker', log_)
        self.str = {}
        self.download_limit = Queue.Queue(config.dl_instances)
        threading.Thread.__init__(self)

        self.small_id = SmallId(self.log, 0)

        self.mutex_dl_list = threading.Lock()

    def print_dl_list(self):
        self.mutex_dl_list.acquire()
        self.log.info('dl-list changed:')
        for i in xrange(0, len(self.dl_list)):
            self.log.info('%d : %s' % (i, self.dl_list[i]['pinfo'].title))
        self.mutex_dl_list.release()

    def dl_preprocess(self):
        while True:
            pinfo = self.in_queue.get(True)
            self.in_queue.task_done()
            log.info(pinfo.title)

            downloadfile = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + '.flv')
            log.info('preprocessing download for' + downloadfile)
            url = Url.LargeDownload({'url': pinfo.flv_url, 'queue': self.dl_queue, 'log': self.log, 'cache_folder':
            os.path.join(pinfo.subdir, pinfo.title)})

            if url.size < 1024:
                self.log.error('flashvideo is to small - looks like the streamer don\'t want to send us the real video')
                continue
            if os.path.isfile(downloadfile):
                if os.path.getsize(downloadfile) == url.size:
                    self.log.info('already completed 1')
                    continue
                else:
                    self.log.info('not completed '+str(os.path.getsize(downloadfile))+':'+str(url.size))

            self.download_limit.put(1)
            self.mutex_dl_list.acquire()
            url.id = self.small_id.new()

            data_len_str = format_bytes(url.size)
            start = time.time()
            tmp = {'start':start, 'url':url, 'data_len_str':data_len_str, 'pinfo':pinfo}
            self.dl_list[url.id] = tmp
            self.mutex_dl_list.release()

            url.start()

            self.print_dl_list()

    def dl_postprocess(self, id):
        dl  = self.dl_list[id]
        url = dl['url']
        pinfo = dl['pinfo']
        downloadfile = os.path.join(config.flash_dir,pinfo.subdir,pinfo.title+".flv")
        log.info('postprocessing download for' + downloadfile)
        if url.state & Url.LargeDownload.STATE_FINISHED:
            os.rename(url.save_path, downloadfile)
        else:
            self.log.info('unhandled urlstate '+str(url.state)+' in postprocess')
            # error happened, but we will ignore it
            pass
        self.mutex_dl_list.acquire()
        del self.dl_list[id]
        self.download_limit.get()
        self.download_limit.task_done()
        self.small_id.free(id)
        self.mutex_dl_list.release()

    def run(self):
        threading.Thread(target=self.dl_preprocess).start()
        while True:
            id  = self.dl_queue.get(True)

            now = time.time()
            dl  = self.dl_list[id]
            url = dl['url']
            if(url.state == Url.LargeDownload.STATE_ALREADY_COMPLETED or url.state & Url.LargeDownload.STATE_FINISHED or url.state & Url.LargeDownload.STATE_ERROR):
                self.dl_postprocess(id)

            start = dl['start']
            data_len_str = dl['data_len_str']
            percent_str = calc_percent(url.downloaded, url.size)
            eta_str     = calc_eta(start, now, url.size - url.position, url.downloaded - url.position)
            speed_str   = calc_speed(start, now, url.downloaded - url.position)
            downloaded_str = format_bytes(url.downloaded)
            config.win_mgr.progress.add_line(' [%s%%] %s/%s at %s ETA %s  %s' % (percent_str, downloaded_str, data_len_str, speed_str,
                                               eta_str, dl['pinfo'].title), id)


def format_bytes(bytes):
    if bytes is None:
        return 'N/A'
    if bytes == 0:
        exponent = 0
    else:
        exponent = long(math.log(float(bytes), 1024.0))
    suffix = 'bkMGTPEZY'[exponent]
    converted = float(bytes) / float(1024**exponent)
    return '%.2f%s' % (converted, suffix)


def calc_percent(byte_counter, data_len):
    if data_len is None:
        return '---.-%'
    return '%5s' % ('%3.1f' % (float(byte_counter) / float(data_len) * 100.0))


def calc_eta(start, now, total, current):
    if total is None:
        return '--:--'
    dif = now - start
    if current == 0 or dif < 0.001: # One millisecond
        return '--:--'
    rate = float(current) / dif
    eta = long((float(total) - float(current)) / rate)
    (eta_mins, eta_secs) = divmod(eta, 60)
    if eta_mins > 99:
        return '--:--'
    return '%02d:%02d' % (eta_mins, eta_secs)


def calc_speed(start, now, bytes):
    dif = now - start
    if bytes == 0 or dif < 0.001: # One millisecond
        return '%10s' % '---b/s'
    return '%10s' % ('%s/s' % format_bytes(float(bytes) / dif))
