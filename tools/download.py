import re
import os
import urllib2
import urllib
from tools.logging import logging

log = logging('download')

try:
    from keepalive import HTTPHandler
except:
    pass
else:
    keepalive_handler = HTTPHandler()
    opener = urllib2.build_opener(keepalive_handler)
    urllib2.install_opener(opener)
    log.info('keepalive support active')

GZIP = 0
try:
    import StringIO
    import gzip
else:
    GZIP = 1
    log.info('gzip support active')

class download(Object):
    def __init__(self,args):
        m_cache_dir = arg['cachedir']

    @staticmethod
    def replaceSpecial(s):
        return re.sub('[^a-zA-Z0-9]','_',s)

    def get_urlpointer(url, post = {}):
        log.info( "downloading from:"+url
        try:
            req = urllib2.Request(url)
            if GZIP:
                req.add_header('Accept-Encoding', 'gzip')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-us,en;q=0.5')
            req.add_header('Accept-Charset', 'utf-8,ISO-8859-1;q=0.7,*;q=0.7')
            #req.add_header('Keep-Alive', '300')
            #req.add_header('Connection', 'keep-alive')
            data = urllib.urlencode(post)
            f = urllib2.urlopen(req,data)
        except IOError, e:
            log.error('We failed to open "%s".' % url)
            if hasattr(e, 'code'):
                   log.error('We failed with error code - %s.' % e.code)
            elif hasattr(e, 'reason'):
                log.error("The error object has the following 'reason' attribute :")
                log.error(e.reason)
                log.error("This usually means the server doesn't exist,' is down, or we don't have an internet connection.")
            sys.exit()
        return f

    def get_urlredirection(url, post = {}):
        hash = replaceSpecial(url) #todo post should be hashed too
        if os.path.isfile(os.path.join(cache_dir,hash))==1:
            log.info("using redirectioncache: " + os.path.join(cache_dir,hash))
            f=open(os.path.join(cache_dir,hash),"r")
            data=f.readlines()
            f.close()
            return ''.join(data)

        redirection = get_urlpointer(url,post).geturl()
        if os.path.isfile(os.path.join(cache_dir,hash))==0:
            f=open(os.path.join(cache_dir,hash),"w")
            f.writelines(redirection)
            f.close()
        return redirection

    def get_data(url, post = {}):
        hash = replaceSpecial(url) #todo post should be hashed too
        if os.path.isfile(os.path.join(cache_dir,hash))==1:
            log.info("using cache: " + os.path.join(cache_dir,hash))
            f=open(os.path.join(cache_dir,hash),"r")
            data=f.readlines()
            f.close()
            return ''.join(data)
        f=get_urlpointer(url, post)
        data=f.read()
        if f.headers.get('Content-Encoding') == 'gzip':
            compressedstream = StringIO.StringIO(data)
            gzipper = gzip.GzipFile(fileobj=compressedstream)
            data = gzipper.read()
        if os.path.isfile(os.path.join(cache_dir,hash))==0:
            f=open(os.path.join(cache_dir,hash),"w")
            f.writelines(data)
            f.close()
        return data
