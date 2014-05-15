# -*- coding: utf-8 -*-
# YOU NEED TO COPY THIS FILE TO config.py so that the program uses those values here
from __future__ import print_function
import os


config = {}

def loadConfig():
    global config

    # caches are only used temporarily - if a download fails, sometimes it can help to delete
    # all cachedata - the only negative point in deleting all cachedata is, that the program may be a bit slower on next start
    cache_dir = 'cache'             # here we write normal html-downloads
    cache_dir_for_flv = 'cache2'    # here we write flashdownloads

    flash_dir = 'flash' # all finished flashdownloads go in this directory and will be deleted from the cachedir


    dl_instances = 6  # how many parallel downloads you will start

    # VALUES below this aren't interesting for you

    # dl_* can be changed through config and use those values then as default
    dl_title = 'tmp'
    dl_name = 'tmp'

    link = None # you can set a default url as starturl.. but commandline-option will overwrite this var

    dir_list = {'cache_dir': cache_dir, 'flash_dir':flash_dir}
    error = 0
    for i in dir_list:
        path = dir_list[i]
        if os.path.isdir(path) is False:
            os.makedirs(path)
        if not os.access(path, os.W_OK):
            print(i + 'needs a writeable path, but your %s isn\'t writeable please edit config.py' % path)
            error = 1
    if error == 1:
        import sys
        sys.exit(1)

    extractStart = 0 # how many media files should be skipped when using extract all
    extractAmount = 999999 # how many media files should be extracted when using extract all

    cachePort = 0 #9123
    preferHypertable=False
    preferFileCache = False

    config = {
        'cache_dir': cache_dir,
        'cache_dir_for_flv': cache_dir_for_flv,
        'flash_dir': flash_dir,
        'dl_instances': dl_instances,
        'dl_title': dl_title,
        'dl_name': dl_name,
        'link': link,
        'extractStart': extractStart,
        'extractAmount': extractAmount,
        'cachePort': cachePort,
        'preferHypertable': preferHypertable,
        'preferFileCache': preferFileCache,
            }
    return config
