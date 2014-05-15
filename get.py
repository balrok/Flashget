#!/usr/bin/python
# -*- coding: utf-8 -*-

import locale
import flashget.commandline as commandline
import flashget.log
flashget.log.dummy = 0

locale.setlocale(locale.LC_ALL, "")

commandline.parse()
open('.flashget_log', 'a').write(commandline.get_log_line() + '\n')

from flashget.helper import is_array
import config
from flashget.downloader import Downloader
from flashget.stream import VideoInfo
from flashget.page import getPageByLink

import sys
import logging
import os


log = logging.getLogger(__name__)

def main():
    link = config.link

    if not link:
        import flashget.commandline as com
        com.usage()

    downloader = Downloader(config.dl_instances)

    # a link can be either a download-page or a stream
    pageHandler = getPageByLink(link)
    if not pageHandler:
        pinfo = VideoInfo(link)
        if not pinfo.stream:
            log.error('No handler for %s', link)
            sys.exit(1)
        processStream(pinfo, downloader)
    else:
        processPage(pageHandler, link, downloader)
    # now the downloading starts
    downloader.run()


def processMultiPage(pageHandler, media):
    from flashget.db2 import persist
    persist(pageHandler, media)
    log.info("finished")
    sys.exit(0)

def processPage(pageHandler, link, downloader):
    log.info("use pagehandler: %s", pageHandler.name)
    media = pageHandler.get(link) # returns array of medias (extractAll) or just one media (download)
    if not media:
        log.error('Could not extract')
        return False
    if is_array(media):
        return processMultiPage(pageHandler, media)
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
                downloadPath = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
                altPartsPinfo.append({'downloadPath': downloadPath, 'stream': pinfo.stream})
            if altPartsPinfo != []:
                queueData.append(altPartsPinfo)
        downloader.download_queue.append(queueData)

def processStream(pinfo, downloader):
    pinfo.name = "tmp"
    pinfo.title = "tmp"
    if config.dl_name:
        pinfo.name = config.dl_name
    if config.dl_title:
        pinfo.title = config.dl_title
    downloadPath = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
    downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])

main()
