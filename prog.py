# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import time
try:
    import queue
except ImportError:
    import Queue as queue

from tools.helper import is_array
import config
from tools.downloader import Downloader
from tools.stream import VideoInfo, flashExt
from tools.page import pages

import signal
import sys


log = config.logger['main']

def signal_handler(signal, frame):
    log.info('You pressed Ctrl+C - Goodbye')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def main():
    link = config.link
    media = None
    streamHandler = None

    if not link:
        import tools.commandline as com
        com.usage()

    pageHandler = pages.getExtensionByRegexStringMatch(link)
    if not pageHandler:
        streamHandler = flashExt.getExtensionByRegexStringMatch(link)
        if not streamHandler:
            log.error("No handler for %s" % link)
            sys.exit(1)
    else:
        pageHandler = pageHandler()
        log.error(pageHandler)
        media = pageHandler.get(link) # returns array of medias (extractAll) or just one media (download)
        if is_array(media):
            allPages = media
            from tools.db2 import persist
            persist(pageHandler, allPages)
            log.info("finished")
            sys.exit(0)
        if not media:
            log.error('Could not extract')
            return

    download_queue = queue.Queue()
    threads = []
    t = Downloader(download_queue)
    threads.append(t)
    t.start()

    if media:
        for part in media.getSubs():
            queueData = []
            for alt in part.getSubs():
                altPartsPinfo = []
                for altPart in alt.getSubs():
                    pinfo = altPart.pinfo
                    if not pinfo or not pinfo.title or not pinfo.stream_url:
                        # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
                        continue
                    log.info('added "%s" to downloadqueue with "%s"' % (pinfo.title, pinfo.url))
                    altPartsPinfo.append(pinfo)
                if altPartsPinfo != []:
                    queueData.append((media.name, altPartsPinfo, 0))
            download_queue.put(queueData)

    if streamHandler:
        name = "tmp"
        title = "tmp"
        if config.dl_name:
            name = config.dl_name
        if config.dl_title:
            title = config.dl_title
        pinfo = VideoInfo(link)
        pinfo.name = name
        pinfo.title = title
        download_queue.put([(name, [pinfo], 0)])

    try:
        time.sleep(999999999)
    except:
        log.info("Ctrl-c received!")
        for i in threads:
            i.stop = True
            i.join()
        sys.exit(0)
