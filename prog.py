# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import time
import Queue

from tools.helper import *
import config
import tools.pages as pages
from tools.downloader import Downloader

log = config.logger['main']

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
        link = get_link_from_input()

    while True:
        # loop until user added supported link
        pageHandler = pages.getClass(link)
        if not pageHandler:
            link = get_link_from_input()
            continue
        media = pageHandler.extract(link)
        if not media:
            log.error('no urls found')
            return
        break

    download_queue = Queue.Queue()
    Downloader(download_queue).start()

    for part in media.parts:
        queueData = []
        for alt in part.alternatives:
            altPartsPinfo = []
            for altPart in alt.alternativeParts:
                pinfo = altPart.pinfo
                if not pinfo.title or not pinfo.stream_url:
                    # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
                    continue
                log.info('added "%s" to downloadqueue with "%s"' % (altPart.name, altPart.url))
                altPartsPinfo.append(pinfo)
            queueData.append((media.name, altPartsPinfo, 0))
        download_queue.put(queueData)

    while True:
        time.sleep(999999999)
