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

r_iso = re.compile('([\x80-\xFF])')
def iso2utf(s):
   def conv(m):
         c = m.group(0)
         return ('\xC2'+c, '\xC3'+chr(ord(c) - 64))[ord(c) > 0xBF]
   return r_iso.sub(conv, s)

def normalize_title(str):
    str = str.replace('/','_')
    str = str[:string.rfind(str,' Video')]
    return unicode(str,'iso-8859-1')

def main():
    flash_dir='flash/'
    urllist=[]

    for i in xrange(7,9):
        urllist.append("http://anime-loads.org/streams/_hacksign/00"+str(i)+".html")

    if len(sys.argv)<2:
        if len(urllist)==0:
            print "usage: ./get.py animeloadslink"
            sys.exit(1)
    else:
        urllist.append(sys.argv[1])

    # example:
    # <param name="movie" value="http://www.eatlime.com/player/0/3C965A26-11D8-2EE7-91AF-6E8533456F0A"></param>
    # <span class="tag-0">001: Rollenspiele</span>
    # http://files18.eatlime.com/3C965A26-11D8-2EE7-91AF-6E8533456F0A_p.flv?token=999567af2d78883d27d3d6747e7e5e50&start=0
    # http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
    # from last one: http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50
    # can be resolved to real url
    for url in urllist:
        data=get_data(url)
        '''titleextract/'''
        pos1=data.find('<span class="tag-0">')+len('<span class="tag-0">')
        pos2=data.find("</span>",pos1)
        title = data[pos1:pos2+1]
        if not title:
            print "couldnt extract title"
            sys.exit(1)
        else:
            title=normalize_title(title)
            print title
        '''/titleextract'''

        '''urlextract/'''
        # try it with eatlime first
        pos1=data.find('<param name="movie" value="')+len('<param name="movie" value="')
        pos2=data.find('"',pos1)
        url=data[pos1:pos2]
        '''/urlextract'''
        if not url:
            print "problem in urlextract 1"
            sys.exit(1)
        tmp = get_urlpointer(url).geturl()
        # lash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&pl
        pos1=tmp.find('file=')+len('file=')
        pos2=tmp.find("&duration",pos1)
        url = tmp[pos1:pos2]
        print "found "+url
        print tmp
        if not url:
            print "problem in urlextract 2"
            sys.exit(1)
        url = get_urlpointer(url).geturl()
        if not url:
            print "problem in urlextract 2"
            sys.exit(1)
        # File downloader
        fd = FileDownloader({
            'filename': os.path.join(flash_dir,title+".flv"),
            'quiet': False,
            })
        retcode = fd.download(url)

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
    return f


def get_data(url, post = {}):
    global GZIP
    print "downloading from:"+url
    hash = md5.new(url).hexdigest() #todo post should be hashed too
    if os.path.isfile(os.path.join(cache_dir,hash))==1:
        print "using cache: " + os.path.join(cache_dir,hash)
        f=open(os.path.join(cache_dir,hash),"r")
        data=f.readlines()
        f.close()
        return ''.join(data)
    #time.sleep(10)
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
