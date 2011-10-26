from tools.pages.animeloads import *
from tools.pages.youtube import *
from tools.pages.plain import *
import sys
import config
import logging


log = config.logger['main']
# log on console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)

try:
    link = sys.argv[1].lower()
except:
    print "usage: enter an url as commandline argument"
    sys.exit(1)

if link.find('anime-loads') >= 0:
    a = AnimeLoads(log)
elif link.find('youtube') >= 0:
    a = YouTube(log)
else:
    a = Plain(log)
a.extract_url(link)
