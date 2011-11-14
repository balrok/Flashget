# -*- coding: utf-8 -*-
# YOU NEED TO COPY THIS FILE TO config.py so that the program uses those values here
import os
from tools.defines import Quality

# caches are only used temporarily - if a download fails, sometimes it can help to delete
# all cachedata - the only negative point in deleting all cachedata is, that the program may be a bit slower on next start
cache_dir = 'cache'             # here we write normal html-downloads
cache_dir_for_flv = 'cache2'    # here we write flashdownloads

flash_dir = 'flash' # all finished flashdownloads go in this directory and will be deleted from the cachedir
flash_quality = Quality.HIGH # sometimes the videopages offer different qualities - don't change the quality in the middle of a download - the resulting movie will be broken then



import logging
LOG_FILENAME = 'output.log'
logging.basicConfig(filename=LOG_FILENAME, filemode='w',level=logging.DEBUG)
logger = {}

for i in ['main', 'downloader', 'urlDownload', 'urlCache', 'page', 'stream_extract', 'sqlalchemy']:
    logger[i] = logging.getLogger(i)

log = {
    'ALL': { # defines stuff for all sections
        'logwin': {
            'level': logging.INFO
        },
        'logconsole':{
            'level': logging.INFO
        },
        # don't remove default format and level
        'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        'level': logging.DEBUG
    },
    'urlDownload': {
        'level': logging.ERROR
    },
    'urlCache': {
        'level': logging.WARNING
    }
}


dl_instances = 6  # how many parallel downloads you will start

# keepalive is used for http-requests where we can reuse an already opened connection to a server, which results in speed-improvements
# but this feature is currently only experimental and will sometimes block your whole program or maybe some other strange errors
keepalive = True
dns_reset = 60 * 60 * 8 # we cache dns->ip and after this time we will refresh our cacheentry


dlc = {}
dlc['dest_type'] = 'jdownload'
dlc['key'] = 'blablabla'
dlc['iv'] = 'muhmuh'

# VALUES below this aren't interesting for you

# dl_* can be changed through config and use those values then as default
dl_title = None
dl_name = None
extract_all = False

win_mgr = None
megavideo_wait = 0
link = None # you can set a default url as starturl.. but commandline-option will overwrite this var

dir_list = {'cache_dir': cache_dir, 'flash_dir':flash_dir}
error = 0
for i in dir_list:
    path = dir_list[i]
    if os.path.isdir(path) is False:
        os.makedirs(path)
    if not os.access(path, os.W_OK):
        print i + 'needs a writeable path, but your %s isn\'t writeable please edit config.py' % path
        error = 1
if error == 1:
    import sys
    sys.exit(1)

txt_only = False
extractStart = 0 # how many media files should be skipped when using extract all
extractAmount = 999999 # how many media files should be extracted when using extract all

cachePort = 0
