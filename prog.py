# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import time
import sys
import threading
import Queue

from tools.url import UrlMgr, LargeDownload
from tools.helper import *
import tools.defines as defs
from tools.logging import LogHandler
import config

log = LogHandler('Main')


def usage():
    log.error("usage: ./get.py AnimeLoadslink")
    sys.exit(0)


def main():
    from tools.video_get import AnimeKiwi, AnimeLoads, AnimeJunkies, YouTube
    log = LogHandler('Main')

    urllist = []

    if len(sys.argv) < 2:
        url = UrlMgr({'url': 'http://anime-loads.org/anime-serien-gesamt.html', 'log': log})
        if not url.data:
            log.error('anime-loads down')
            sys.exit(1)
        stuff = textextractall(url.data, ' ><a href="anime-serien/', '</')
        for i in stuff:
            out = remove_html(textextract(i, 'strong>', '').decode('iso-8859-1'))
            config.win_mgr.main.add_line(out)
        time.sleep(1000)
    else:
        links = []
        names = []
        def name_handle(i, class_):
            return
        def get_urldata():
            url = UrlMgr({'url': sys.argv[1], 'log': log})
            if not url.data:
                usage()
            return url.data

        if sys.argv[1].find('anime-loads') >= 0:
            class_call = AnimeLoads
            if sys.argv[1].find('/streams/') < 0:
                links = textextractall(get_urldata(), '<a href="../streams/','"')
                def links_handle(i): return 'http://anime-loads.org/streams/%s' % links[i]

        elif sys.argv[1].find('animekiwi') >= 0:
            class_call = AnimeKiwi
            if sys.argv[1].find('watch') == -1:     # its a bit difficult to find out what the link means :-/
                # http://www.animekiwi.com/kanokon/
                links = textextractall(get_urldata(), '<a href="/watch/','"') # <a href="/watch/kanokon-episode-12/" target="_blank">Kanokon Episode 12</a>
                def links_handle(i): return 'http://animekiwi.com/watch/%d' % links[i]

        elif sys.argv[1].find('anime-junkies') >= 0:
            class_call = AnimeJunkies
            if sys.argv[1].find('serie') >= 0:
                data = get_urldata()
                links = textextractall(data, '<a href="film.php?name=','"')
                names = textextractall(data, 'lass="Stil3 Stil111"/><strong>\n\t       ', '</strong')
                def name_handle(i, class_):
                    name = '%03d: %s' % ((i+1), remove_html(names[i]))
                    class_.title = name.replace('/', '_')
                def links_handle(i): return 'http://anime-junkies.org/film.php?name=%s' % links[i].replace(' ', '+')

        elif sys.argv[1].find('youtube') >= 0:
            class_call = YouTube
            if sys.argv[1].find('view_play_list') >= 0:
                # http://www.youtube.com/view_play_list?p=9E117FE1B8853013&search_query=georg+kreisler
                data = get_urldata()
                # alt="Georg Kreisler: Schlagt sie tot?"></a><div id="quicklist-icon-bmQbYP_VkCw" class="addtoQL90"
                # maybe we can get all this data in one action..
                links = textextractall(data, 'id="add-to-quicklist-', '"')
                names = textextractall(data, '" alt="', '"') # luckily this alt-tag only occurs for those icons :)
                glob_name_uniq = remove_html(names[0].decode('utf-8'))
                def name_handle(i, class_):
                    class_.title = remove_html(names[i + 1].decode('utf-8'))
                    class_.name = glob_name_uniq
                def links_handle(i): return 'http://www.youtube.com/watch?v=%s' % links[i]

        if links != None:
            if len(links) == 0:
                log.error('failed to extract the links')
                usage()
                time.sleep(100)
            else:
                ll = len(links)
                for i in xrange(0, ll):
                    pinfo = class_call(links_handle(i), log)
                    name_handle(i, pinfo)
                    urllist.append(pinfo)
                    log.info('added url: %s -> %s' % (pinfo.name, pinfo.url))
                if pinfo.homepage_type == defs.Homepage.ANIMEKIWI:
                    urllist = urllist[::-1] # cause the page shows them in the wrong order ~_~
                    # TODO sometimes they have two entries for each part (subbed / dubbed) -> make sure to download only one
                config.win_mgr.append_title(defs.Homepage.str[pinfo.homepage_type])
                config.win_mgr.append_title(pinfo.name)
        else:
            pinfo = class_call(sys.argv[1], log)
            config.win_mgr.append_title(defs.Homepage.str[pinfo.homepage_type])
            config.win_mgr.append_title(pinfo.title)
            urllist.append(pinfo)


    if len(urllist)==0:
        log.error('no urls found')
        usage()

    download_queue = Queue.Queue(1)
    flashWorker = FlashWorker(download_queue)
    flashWorker.start()

    for pinfo in urllist:
        if not pinfo.title or not pinfo.stream_url:
            # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
            continue
        log.info('added "%s" to downloadqueue with "%s"' % (pinfo.title, pinfo.stream_url))
        download_queue.put(pinfo, True)


class FlashWorker(threading.Thread):

    def __init__(self, inqueue, log_ = log):
        self.dl_queue = Queue.Queue()
        self.in_queue = inqueue
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
            if i in self.dl_list:
                self.log.info('%d : %s' % (i, self.dl_list[i]['pinfo'].title))
        self.mutex_dl_list.release()

    def dl_preprocess(self):
        while True:
            pinfo = self.in_queue.get(True)
            self.in_queue.task_done()

            if not pinfo.subdir or not pinfo.title:
                log.bug('pinfo.subdir or pinfo.title in dl_preprocess missing flashfile: %s' % pinfo.flv_url)
                continue

            downloadfile = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
            log.info('preprocessing download for %s' % downloadfile)
            if os.path.isfile(downloadfile):
                self.log.info('already completed')
                continue

            if pinfo.stream_type == defs.Stream.MEGAVIDEO:
                diff = config.megavideo_wait - time.time()
                if diff > 0:
                    log.error('megavideo added us to the waitlist, will be released in %d:%d' % (diff / 60, diff % 60))
                    continue

            if not pinfo.flv_url:
                log.error('url has no flv_url and won\'t be used now %s' % pinfo.url)
                continue

            args = {'url': pinfo.flv_url, 'queue': self.dl_queue, 'log': self.log, 'cache_folder': os.path.join(pinfo.subdir, pinfo.title)}
            if pinfo.stream_type == defs.Stream.HDWEB:
                args['http_version'] = '1.0'
            url_handle = LargeDownload(args)

            if url_handle.size < 4096: # smaller than 4mb
                self.log.error('flashvideo is to small %d - looks like the streamer don\'t want to send us the real video %s' % (url_handle.size, pinfo.flv_url))
                continue

            self.download_limit.put(1)
            display_pos = self.small_id.new()

            data_len_str = format_bytes(url_handle.size)
            start = time.time()
            tmp   = {'start':start, 'url':url_handle, 'data_len_str':data_len_str, 'pinfo':pinfo, 'display_pos':display_pos,
                     'stream_str':defs.Stream.str[pinfo.stream_type]}
            self.mutex_dl_list.acquire()
            self.dl_list[url_handle.uid] = tmp
            self.mutex_dl_list.release()
            self.print_dl_list()
            url_handle.start()

    def dl_postprocess(self, uid):
        dl = self.dl_list[uid]
        url = dl['url']
        pinfo = dl['pinfo']
        display_pos = self.dl_list[uid]['display_pos']
        downloadfile = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
        log.info('%d postprocessing download for %s' % (uid, downloadfile))
        if url.state & LargeDownload.STATE_FINISHED:
            self.log.info('moving from %s to %s' % (url.save_path, downloadfile))
            os.rename(url.save_path, downloadfile)
        elif url.state != LargeDownload.STATE_ERROR: # a plain error won't be handled here
            self.log.error('unhandled urlstate %d in postprocess' % url.state)
        config.win_mgr.progress.add_line(' ', self.dl_list[uid]['display_pos']) # clear our old line
        self.mutex_dl_list.acquire()
        del self.dl_list[uid]
        self.mutex_dl_list.release()
        self.print_dl_list()
        self.small_id.free(display_pos)
        self.download_limit.get()
        self.download_limit.task_done()

    def process(self, uid):
        now = time.time()
        dl  = self.dl_list[uid]
        url = dl['url']
        display_pos = dl['display_pos']
        start = dl['start']
        data_len_str = dl['data_len_str']

        if(url.state == LargeDownload.STATE_ALREADY_COMPLETED or url.state & LargeDownload.STATE_FINISHED or url.state & LargeDownload.STATE_ERROR):
            self.dl_postprocess(uid)
            return

        percent_str = calc_percent(url.downloaded, url.size)
        eta_str     = calc_eta(start, now, url.size - url.position, url.downloaded - url.position)
        speed_str   = calc_speed(start, now, url.downloaded - url.position)
        downloaded_str = format_bytes(url.downloaded)
        config.win_mgr.progress.add_line(' [%s%%] %s/%s at %s ETA %s  %s |%s|' % (percent_str, downloaded_str, data_len_str, speed_str,
                                           eta_str, dl['pinfo'].title, dl['stream_str']), display_pos)

    def run(self):
        threading.Thread(target=self.dl_preprocess).start()
        while True:
            uid  = self.dl_queue.get(True)
            if uid in self.dl_list: # it is possible that the worker for dl_queue is faster than this thread and added the uid more than once
                self.process(uid)


def format_bytes(bytes):
    if bytes is None:
        return 'N/A'
    if bytes > (1024**2):
        bytes = float(bytes / (1024.0**2))
        suffix = 'Mb'
    elif bytes <= (1024**2):
        bytes = float(bytes / 1024.0)
        suffix = 'kb'
    return '%.2f%s' % (bytes, suffix)


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
