import sys
import config
import logging
from tools.stream import VideoInfo
from tools.stream_extract import *
from tools.streams.animeloads import AnimeLoadsStream
from tools.log import setLogHandler


config.log['ALL']['logwin'] = False
config.log['ALL']['logconsole'] = {True}
setLogHandler()

try:
    link = sys.argv[1]
except:
    print "usage: enter an url as commandline argument"
    sys.exit(1)

log = config.logger['main']
info = AnimeLoadsStream(link, log)
print info.stream_url
print info.flv_url
