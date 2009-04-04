import re,os,urllib2,urllib
try:
    from keepalive import HTTPHandler
    keepalive_handler = HTTPHandler()
    opener = urllib2.build_opener(keepalive_handler)
    urllib2.install_opener(opener)
    print 'keepalive support active'
except:
    pass

try:
    import StringIO
    import gzip
    GZIP = 1
except ImportError:
    GZIP = 0

cache_dir='cache'

r_ascii = re.compile('([^a-zA-Z0-9])')
def replaceSpecial(s):
    return r_ascii.sub('_',s)

def get_urlpointer(url, post = {}):
    global GZIP
    print "downloading from:"+url
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
        print 'We failed to open "%s".' % url
        if hasattr(e, 'code'):
               print 'We failed with error code - %s.' % e.code
        elif hasattr(e, 'reason'):
            print "The error object has the following 'reason' attribute :"
            print e.reason
            print "This usually means the server doesn't exist,' is down, or we don't have an internet connection."
        sys.exit()
    return f

def get_urlredirection(url, post = {}):
    hash = replaceSpecial(url) #todo post should be hashed too
    if os.path.isfile(os.path.join(cache_dir,hash))==1:
        print "using redirectioncache: " + os.path.join(cache_dir,hash)
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
        print "using cache: " + os.path.join(cache_dir,hash)
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


