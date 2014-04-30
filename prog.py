# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import time

from tools.helper import is_array
import config
from tools.downloader import Downloader
from tools.stream import VideoInfo, flashExt
from tools.page import pages

import sys
import logging


log = logging.getLogger(__name__)

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
            log.error('No handler for %s', link)
            sys.exit(1)
    else:
        pageHandler = pageHandler()
        log.info("use pagehandler: %s", pageHandler.name)
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

    downloadThread = Downloader()

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
                    log.info('added "%s" to downloadqueue with "%s"', pinfo.title, pinfo.url)
                    altPartsPinfo.append(pinfo)
                if altPartsPinfo != []:
                    queueData.append((media.name, altPartsPinfo))
            downloadThread.download_queue.put(queueData)
    elif streamHandler:
        name = "tmp"
        title = "tmp"
        if config.dl_name:
            name = config.dl_name
        if config.dl_title:
            title = config.dl_title
        pinfo = VideoInfo(link)
        pinfo.name = name
        pinfo.title = title
        downloadThread.download_queue.put([(name, [pinfo])])

    downloadThread.run()

