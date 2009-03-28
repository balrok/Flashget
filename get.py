#!/usr/bin/python
# -*- coding: utf-8 -*-
referer = 0 #no need to touch this
# Python Imports
import urllib2,urllib,os,time,re,sys,md5,httplib,socket,math,string
try:
    import StringIO
    import gzip
    GZIP = 1
    #print "gzip support active"
except ImportError:
    #print "no gzip support available"
    GZIP = 0

cache_dir='cache'

def normalize_title(str):
    str = str.replace('/','_')
    str = str[:string.rfind(str,' Video')]
    return str

def main():
    flash_dir='flash/'
    urllist=[]

    #<a href='/watch/4363803/Sky_Girls_12_1_3' 
    #http://www.myvideo.de/watch/4341108/Gundam_SEED_20_2_3
    #for the webpage only the id is important, the string behind this is ignored..
    linkextr = re.compile(r"href='/watch/([0-9]*)/(.*?)'.*?",re.U)
    for i in xrange(10,35):
        lastid='0' #cause my regex doesn't work so well :-/
        data = get_url("http://www.myvideo.de/news.php?lpage="+str(i)+"&rubrik=gorjp&searchMember=426979&searchWord=&searchOrder=3&searchFilter=16")
        a = linkextr.finditer(data)
        if(not a):
            continue
        for match in a:
            if(match.group(1)==lastid):
                continue
            else:
                if match.group(2).find('Code')>=0:
                    lastid=match.group(1)
                    urllist.append("http://www.myvideo.de/watch/"+match.group(1))

    if len(sys.argv)<2:
        if len(urllist)==0:
            print "usage: ./get.py myvideourl"
            sys.exit(1)
    else:
        urllist.append(sys.argv[1])

    #example:
    #http://myvideo-450.vo.llnwd.net/d2/movie2/de/thumbs/3502450_1.jpg
    #http://myvideo-450.vo.llnwd.net/d2/movie2/de/3502450.flv
    urlextr  = re.compile(r".*<link rel='image_src' href='(http://.*?)/thumbs(.*?)_[0-9]*.jpg",re.U) #find/replace is faster
    titleextr= re.compile(r".*<title>(.*?)</title>",re.U)
    for url in urllist:
        data=get_url(url)
        '''titleextract/'''
        pos1=data.find("<title>")+len("<title>")
        pos2=data.find("</title>",pos1)
        title = data[pos1:pos2]
        '''/titleextract'''

        '''urlextract/'''
        pos1=data.find("<link rel='image_src' href='")+len("<link rel='image_src' href='")
        pos2=data.find("_",pos1)
        url=data[pos1:pos2].replace('/thumbs','')+".flv"
        '''/urlextract'''
        if url:
            if not title:
                print "couldnt extract title"
                sys.exit(1)

            # File downloader
            fd = FileDownloader({
                'filename': os.path.join(flash_dir,normalize_title(title)+".flv"),
                'quiet': False,
                })
            retcode = fd.download(url)
            continue
        else:
            print "problem in urlextract"
            sys.exit(1)

def get_url(url, post = {}):
    global GZIP
    print "downloading from:"+url
    hash = md5.new(url).hexdigest() #todo post should be hashed too
    if os.path.isfile(os.path.join(cache_dir,hash))==1:
        print "using cache"
        f=open(os.path.join(cache_dir,hash),"r")
        data=f.readlines()
        f.close()
        return ''.join(data)
    #time.sleep(10)
    try:
        req = urllib2.Request(url)
        if GZIP:
            req.add_header('Accept-Encoding', 'gzip')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-us,en;q=0.5')
        req.add_header('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')
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
    data = f.read()
    if f.headers.get('Content-Encoding') == 'gzip':
        compressedstream = StringIO.StringIO(data)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        data = gzipper.read()
    if os.path.isfile(os.path.join(cache_dir,hash))==0:
        f=open(os.path.join(cache_dir,hash),"w")
        f.writelines(data)
        f.close()
    return data

class FileDownloader(object):

    _params = None

    def __init__(self, params):
        """Create a FileDownloader object with the given options."""
        self._params = params
    @staticmethod
    def format_bytes(bytes):
        if bytes is None:
            return 'N/A'
        if bytes == 0:
            exponent = 0
        else:
            exponent = long(math.log(float(bytes), 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(bytes) / float(1024**exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def calc_percent(byte_counter, data_len):
        if data_len is None:
            return '---.-%'
        return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

    @staticmethod
    def calc_eta(start, now, total, current):
        if total is None:
            return '--:--'
        dif = now - start
        if current == 0 or dif < 0.001: # One millisecond
            return '--:--'
        rate = float(current) / dif
        eta = long((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        if eta_mins > 99:
            return '--:--'
        return '%02d:%02d' % (eta_mins, eta_secs)

    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001: # One millisecond
            return '%10s' % '---b/s'
        return '%10s' % ('%s/s' % FileDownloader.format_bytes(float(bytes) / dif))

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
        if elapsed_time < 0.001:
            return int(new_max)
        rate = bytes / elapsed_time
        if rate > new_max:
            return int(new_max)
        if rate < new_min:
            return int(new_min)
        return int(rate)

    def to_stdout(self, message, skip_eol=False):
        """Print message to stdout if not in quiet mode."""
        print u'%s%s' % (message, [u'\n', u''][skip_eol]),
        sys.stdout.flush()

    def to_stderr(self, message):
        """Print message to stderr."""
        print >>sys.stderr, message

    def trouble(self, message=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message. If it
        doesn't raise, it returns an error code suitable to be returned
        later as a program exit code to indicate error.
        """
        if message is not None:
            self.to_stderr(message)
            print message
        return 1

    def report_progress(self, percent_str, data_len_str, speed_str, eta_str):
        """Report download progress."""
        self.to_stdout(u'\r[download] %s of %s at %s ETA %s' %
                (percent_str, data_len_str, speed_str, eta_str), skip_eol=True)
    def report_finish(self):
        """Report download finished."""
        self.to_stdout(u'')

    def download(self, url):
        """Download a given list of URLs."""
        retcode = 0

        suitable_found = False
        filename = self._params['filename']
        print "downloading "+url+" to "+filename
        self._do_download(filename,url)

    def _do_download(self, filename, url):
        request = urllib2.Request(url)
        data = urllib2.urlopen(request)
        data_len = data.info().get('Content-length', None)
        filesize=0
        if os.path.isfile(filename)==1:
            filesize = os.path.getsize(filename)
        if int(data_len)==int(filesize):
            print "already downloaded"
            return
        try:
            stream = open(filename, 'wb')
        except (OSError, IOError), err:
            retcode = self.trouble('ERROR: unable to open for writing: %s' % str(err))
            return retcode
        data_len_str = self.format_bytes(data_len)
        byte_counter = 0
        block_size = 1024
        start = time.time()
        while True:
            # Progress message
            percent_str = self.calc_percent(byte_counter, data_len)
            eta_str = self.calc_eta(start, time.time(), data_len, byte_counter)
            speed_str = self.calc_speed(start, time.time(), byte_counter)
            self.report_progress(percent_str, data_len_str, speed_str, eta_str)

            # Download and write
            before = time.time()
            data_block = data.read(block_size)
            after = time.time()
            data_block_len = len(data_block)
            if data_block_len == 0:
                break
            byte_counter += data_block_len
            stream.write(data_block)
            block_size = self.best_block_size(after - before, data_block_len)

        self.report_finish()
        if data_len is not None and str(byte_counter) != data_len:
            raise ValueError('Content too short: %s/%s bytes' % (byte_counter, data_len))
        try:
            stream.close()
        except (OSError, IOError), err:
            retcode = self.trouble('ERROR: unable to write video data: %s' % str(err))
            return retcode

main()
