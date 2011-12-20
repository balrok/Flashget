# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import time
import Queue

from tools.helper import *
import config
import tools.pages as pages
from tools.downloader import Downloader

log = config.logger['main']

import signal
import sys
from tools.extension import ExtensionRegistrator

pages = ExtensionRegistrator()
pages.loadFolder('tools/pages/')


def signal_handler(signal, frame):
    log.info('You pressed Ctrl+C - Goodbye')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def main():
    link = config.link
    if not link:
        if config.txt_only:
            import tools.commandline as com
            com.usage()
        else:
            log.error("No link provided")
            sys.exit(1)

    while True:
        # loop until user added supported link
        pageHandler = pages.getExtensionByRegexStringMatch(link)
        if not pageHandler:
            log.error("No handler for %s" % link)
            sys.exit(1)
        pageHandler = pageHandler()
        if config.extract_all:
            allPages = pageHandler.getAllPages()
            from tools.db2 import persist
            persist(pageHandler, allPages)
            log.info("finished")
            sys.exit(0)
        media = pageHandler.extract(link)
        if not media:
            log.error('no urls found')
            return
        break

    download_queue = Queue.Queue()
    threads = []
    t = Downloader(download_queue)
    threads.append(t)
    t.start()


    for part in media.getSubs():
        queueData = []
        for alt in part.getSubs():
            altPartsPinfo = []
            for altPart in alt.getSubs():
                pinfo = altPart.pinfo
                if not pinfo.title or not pinfo.stream_url:
                    # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
                    continue
                log.info('added "%s" to downloadqueue with "%s"' % (pinfo.title, pinfo.url))
                altPartsPinfo.append(pinfo)
            if altPartsPinfo != []:
                queueData.append((media.name, altPartsPinfo, 0))
        download_queue.put(queueData)

    try:
        time.sleep(999999999)
    except:
        log.info("Ctrl-c received!")
        for i in threads:
            i.stop = True
            i.join()
        sys.exit(1)
