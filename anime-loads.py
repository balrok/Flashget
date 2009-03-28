#!/usr/bin/python
# -*- coding: utf-8 -*-
referer = 0 #no need to touch this
# Python Imports
import urllib2,urllib,os,time,re,sys,md5,httplib,socket,math,string
try:
    import StringIO
    import gzip
    GZIP = 1
except ImportError:
    GZIP = 0

cache_dir='cache'
flash_dir='flash/'

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

def textextract(data,startstr,endstr):
    pos1=data.find(startstr)
    if pos1<0:
        return
    pos1+=len(startstr)
    pos2=data.find(endstr,pos1)
    if pos2<0:
        return
    return data[pos1:pos2]

def textextractall(data,startstr,endstr):
    startpos    =0
    foundlist   =[]
    while 1:
        pos1=data.find(startstr,startpos)
        if pos1<0:
            return foundlist
        pos1+=len(startstr)
        pos2=data.find(endstr,pos1)
        if pos2<0:
            return foundlist
        startpos=pos2+len(endstr)+1                         # TODO look if this is ok
        foundlist.append(data[pos1:pos2])

def usage():
    print "usage: ./get.py animeloadslink"
    sys.exit(0)

def main():
    urllist=[]

    if len(sys.argv)<2:
        usage()
    else:
        if( sys.argv[1].find('/streams/') < 0):
            # <a href="../streams/_hacksign/003.html"
            # user added video-overview-url
            data=get_data(sys.argv[1])
            if not data:
                usage()
            links=textextractall(data,'<a href="../streams/','"')
            if len(links)>0:
                for i in links:
                    urllist.append('http://anime-loads.org/streams/'+i)
        else:
            urllist.append(sys.argv[1])

    if len(urllist)==0:
        print 'no urls found'
        usage()
    # example:
    # can be resolved to real url
    for url in urllist:
        flashsubdir=textextract(url,'streams/','/')
        try:
            os.makedirs(os.path.join(flash_dir,flashsubdir))
        except:
            pass
        data=get_data(url)
        '''titleextract/'''
        # <span class="tag-0">001: Rollenspiele</span>
        title = textextract(data,'<span class="tag-0">','</span>')
        if not title:
            print "couldnt extract title"
            sys.exit(1)
        else:
            title=normalize_title(title)
        '''/titleextract'''

# urlextract/
    # eatlime
        # <param name="movie" value="http://www.eatlime.com/player/0/3C965A26-11D8-2EE7-91AF-6E8533456F0A"></param>
        url=textextract(data,'<param name="movie" value="','"')
        if url:
            print "eatlime video"
            print url
            tmp = get_urlpointer(url).geturl() # redirection
            # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
            url1 = textextract(tmp,'file=',"&duration")
            if not url1:
                print "-----------"
                print tmp
                print "problem in urlextract 1"
                sys.exit(1)
            # url= http://files18.eatlime.com/3C965A26-11D8-2EE7-91AF-6E8533456F0A_p.flv?token=999567af2d78883d27d3d6747e7e5e50&start=0
            url = get_urlpointer(url1).geturl() # redirection
            if not url:
                print "-----------"
                print url1
                print "problem in urlextract 2"
                sys.exit(1)
            # possible result : http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50
        else:
    # veoh
            # 5697781E-1C60-663B-FFD8-9B49D2B56D36
            # <embed src="http://www.veoh.com/videodetails2.swf?player=videodetailsembedded&type=v&permalinkId=v832040cHGxXkCJ&id=10914100"
            url = textextract(data,'<embed src="','"')
            if url:
                permalink=textextract(url,'&permalinkId=','&id=')
                if not permalink:
                    print '------'
                    print url
                    print 'problem in extracting permalink'
                    sys.exit(1)
                # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
                # apikey is constant
                url = 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink='+permalink+'&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36'
                data = get_data(url)
                if not data:
                    print '-----'
                    print url
                    print 'failed to get data'
                    sys.exit(1)
                # from data we get the link:
                # http://content.veoh.com/flash/p/2/v832040cHGxXkCJ/002878c1815d34f2ae8c51f06d8f63e87ec179d0.fll?ct=3295b39637ac9bb01331e02fd7d237f67e3df7e112f7452a
                url = textextract(data,'fullPreviewHashPath="','"')
                # if we get the redirection from this url, we can manipulate the amount of buffering and download a whole movie pretty
                # fast.. but i have no need for it - just want to remark this for future
                if not url:
                    print '-------'
                    print data
                    print 'failed to get url'
# /urlextract


        # File downloader
        fd = FileDownloader({
            'filename': os.path.join(flash_dir,flashsubdir,title+".flv"),
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
