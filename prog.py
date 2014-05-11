# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from tools.helper import is_array
import config
from tools.downloader import Downloader
from tools.stream import VideoInfo, flashExt
from tools.page import pages

import sys
import logging
import os


log = logging.getLogger(__name__)

def main():
    link = config.link
    streamHandler = None

    if not link:
        import tools.commandline as com
        com.usage()

    downloader = Downloader(config.dl_instances)

    # a link can be either a download-page or a stream
    pageHandler = pages.getExtensionByRegexStringMatch(link)
    if not pageHandler:
        streamHandler = flashExt.getExtensionByRegexStringMatch(link)
        if not streamHandler:
            log.error('No handler for %s', link)
            sys.exit(1)
        processStream(streamHandler, link, downloader)
    else:
        processPage(pageHandler, link, downloader)
    # now the downloading starts
    downloader.run()


def processMultiPage(pageHandler, media):
    from tools.db2 import persist
    persist(pageHandler, media)
    log.info("finished")
    sys.exit(0)

def processPage(pageHandler, link, downloader):
    pageHandler = pageHandler()
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
                pinfo.stream.get(pinfo) # call this, so flvUrl is set inside stream
                altPartsPinfo.append({'downloadPath': downloadPath, 'stream': pinfo.stream})
            if altPartsPinfo != []:
                queueData.append(altPartsPinfo)
        downloader.download_queue.append(queueData)

def processStream(streamHandler, link, downloader):
    name = "tmp"
    title = "tmp"
    if config.dl_name:
        name = config.dl_name
    if config.dl_title:
        title = config.dl_title
    pinfo = VideoInfo(link)
    pinfo.name = name
    pinfo.title = title
    downloadPath = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + ".flv")
    pinfo.stream.get(pinfo) # call this, so flvUrl is set inside stream
    downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])
