#!/usr/bin/python
# -*- coding: utf-8 -*-

print(__file__)
import locale
import os
from . import log
log.dummy = 0

locale.setlocale(locale.LC_ALL, "")

from .helper import is_array

from .commandline import Commandline, get_log_line
cmd = Commandline()
config = cmd.parse()
logFile = os.path.expanduser(os.path.join('~', '.flashget', 'commandline.log'))
open(logFile, 'a').write(get_log_line() + '\n')

from .downloader import Downloader
from .stream import VideoInfo
from .page import getPageByLink

import sys
import logging
import os

log = logging.getLogger(__name__)

def getConfigFromCommandline():
    cmd = Commandline()
    config = cmd.parse()
    return config

def main(config=None):
    if config is None:
        config = getConfigFromCommandline()

    link = config.get('link', False)

    if not link:
        return cmd.usage()

    downloader = Downloader(config.get('dl_instances', 6))

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
                downloadPath = os.path.join(config.get('flash_dir', 'flashget.out'), pinfo.subdir, pinfo.title + ".flv")
                altPartsPinfo.append({'downloadPath': downloadPath, 'stream': pinfo.stream})
            if altPartsPinfo != []:
                queueData.append(altPartsPinfo)
        downloader.download_queue.append(queueData)

def processStream(pinfo, downloader):
    pinfo.name = config.get('dl_name', "tmp")
    pinfo.title = config.get('dl_title', "tmp")
    downloadPath = os.path.join(config.get('flash_dir', 'flashget.out'), pinfo.subdir, pinfo.title + ".flv")
    downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])


