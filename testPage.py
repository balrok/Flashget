from tools.pages import *

from tools import page
import sys
import config
import logging


for i in config.logger:
    log = config.logger[i]
    # log on console
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)

try:
    link = sys.argv[1]
except:
    print "usage: enter an url as commandline argument"
    sys.exit(1)

a = page.getClass(link)
a.extract_url(link)
