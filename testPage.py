import tools.pages as pages
import sys
import config
import logging
from tools.log import setLogHandler

config.log['ALL']['logwin'] = False
config.log['ALL']['logconsole'] = {True}
setLogHandler()
log = config.logger['main']

try:
    link = sys.argv[1]
except:
    print "usage: enter an url as commandline argument"
    sys.exit(1)

pageHandler = pages.getClass(link)
media = pageHandler.extract(link)

#for part in pageHandler.parts:
#    for stream in part['streams']:
#        pinfo = stream['pinfo']
#        if not pinfo.title or not pinfo.stream_url:
#            # this must be called before flv_url, else it won't work (a fix for this would cost more performance and more code)
#            continue
#        log.info('added "%s" to downloadqueue with "%s"' % (part['name'], stream['url']))

print media
