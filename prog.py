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

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C - Goodbye'
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def main():
    log = config.logger['main']

    urllist = []

    def get_link_from_input():
        input_queue = Queue.Queue() # blocking queue for input
        url_win = config.win_mgr.add_window(0.5, 0.2, 3, 0.4, 'Enter an URL:', False, input_queue)
        config.win_mgr.active_win = url_win
        txt = input_queue.get(True)
        config.link = txt
        config.win_mgr.del_window(url_win)
        return config.link

    link = config.link
    if not config.link:
        if config.txt_only:
            import tools.commandline as com
            com.usage()
        else:
            link = get_link_from_input()

    while True:
        # loop until user added supported link
        pageHandler = pages.getClass(link)
        if not pageHandler:
            link = get_link_from_input()
            continue
        if config.extract_all:
            allPages = pageHandler.getAllPages()
            from tools.db2 import persist
            persist(pageHandler, allPages)
            log.info("finished")
            sys.exit(0)

            from tools.db import session
            from tools.page import Media, Part, Alternative, AlternativePart, Tag, Page
            # delete all previous data of this page if exists
            if pageHandler.id:
                for t in (Media, Part, Alternative, AlternativePart):
                    session.query(t).filter(t.pageId==pageHandler.id).delete()
            for t in (Media, Part, Alternative, AlternativePart):
                session.query(t).filter(t.pageId==None).delete()
            session.query(Tag).filter(Tag.name==None).delete()
            session.merge(pageHandler)
            session.commit()
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
            queueData.append((media.name, altPartsPinfo, 0))
        download_queue.put(queueData)

    try:
        time.sleep(999999999)
    except:
        print "Ctrl-c received!"
        for i in threads:
            i.stop = True
            i.join()
        sys.exit(1)
