#!/usr/bin/python
# -*- coding: utf-8 -*-

import locale
import os
from . import log
log.dummy = 0

locale.setlocale(locale.LC_ALL, "")

from .commandline import Commandline, get_log_line
cmd = Commandline()
config = cmd.parse()
logFile = os.path.expanduser(os.path.join('~', '.flashget', 'commandline.log'))
open(logFile, 'a').write(get_log_line() + '\n')

from .downloader import Downloader
from .stream import VideoInfo
from .page import getPageByLink
from .helper import textextract, open

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

    links = config.get('links', [])

    if len(links) == 0:
        log.info("No links specified - will look if there are downloads which can be resumed")
        log.info("NOTICE: this feature isn't 100% bulletproof and it might download too much - please have a closer look for this")
        # continue existing downloads
        # this feature isn't 100% bulletproof:
        # for example when the commandline argument specified another name
        # or if multiple downloads were started and you moved the completed already
        flash_dir = config.get('flash_dir')
        flash_dir_content = os.listdir(flash_dir)
        log.info("Looking in path %s", flash_dir)
        for path in flash_dir_content:
            path = os.path.join(flash_dir, path)
            if not os.path.isdir(path):
                continue
            log.info("Looking in directory %s", path)
            logFile = os.path.join(path, '.flashget.log')
            if not os.path.exists(logFile):
                continue
            log.info("Found logfile %s", logFile)
            with open(logFile, 'r', encoding="utf-8") as f:
                lines = f.readlines()
                # this is already finished
                if lines[-1].startswith('success'):
                    continue
                linksString = 'http'+textextract(lines[0], 'http', '')
                linksString.rstrip()
                if linksString[-1] == "\n":
                    linksString = linksString[:-1]
                # get the linksString splitted at whitespaces - except when it was escaped
                # so split "abc def" but not "abc\\ def"
                linksString= linksString.replace('\\ ', '!WHITESPACE!')
                linksList = linksString.split(" ")
                linksList= [x.replace('!WHITESPACE!', ' ') for x in linksList]
                links.extend(linksList)

    if len(links) == 0:
        log.info("No downloads to resume - exiting")
        sys.exit()

    links = list(set(links))

    log.info("running the program with following links:")
    for link in links:
        log.info(link)
    downloader = Downloader(config.get('dl_instances', 6))

    for link in links:
        # a link can be either a download-page or a stream
        pageHandler = getPageByLink(link)
        if not pageHandler:
            pinfo = VideoInfo(link)
            if not pinfo.stream:
                log.error('No handler for %s', link)
                sys.exit(1)
            processStream(pinfo, downloader)
        else:
            processPage(pageHandler, downloader)
    # now the downloading starts
    downloader.run()

def processPage(pageHandler, downloader):
    log.info("use pagehandler: %s", pageHandler.name)
    media = pageHandler.get()
    if not media:
        log.error('Could not extract')
        return False
    for part in media.getSubs():
        queueData = []
        for alt in part.getSubs():
            altPartsPinfo = []
            for altPart in alt.getSubs():
                pinfo = altPart.pinfo
                if not pinfo or not pinfo.title or not pinfo.stream_url:
                    # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
                    continue
                log.info('added "%s" to downloadqueue with "%s"', pinfo.title, pinfo.stream_url)
                downloadPath = os.path.join(config.get('flash_dir'), pinfo.subdir, pinfo.title + ".flv")
                altPartsPinfo.append({'downloadPath': downloadPath, 'stream': pinfo.stream})
            if altPartsPinfo != []:
                queueData.append(altPartsPinfo)
        downloader.download_queue.append(queueData)

def processStream(pinfo, downloader):
    pinfo.name = config.get('dl_name', "tmp")
    pinfo.title = config.get('dl_title', "tmp")
    downloadPath = os.path.join(config.get('flash_dir'), pinfo.subdir, pinfo.title + ".flv")
    downloader.download_queue.append([[{'downloadPath': downloadPath, 'stream': pinfo.stream}]])
