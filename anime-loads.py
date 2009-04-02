#!/usr/bin/python
# -*- coding: utf-8 -*-
referer = 0 #no need to touch this
# Python Imports
import urllib2,urllib,os,time,re,sys,httplib,socket,math,string
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
flash_dir='flash/'

r_ascii = re.compile('([^a-zA-Z0-9])')
def replaceSpecial(s):
    return r_ascii.sub('_',s)


r_iso = re.compile('([\x80-\xFF])')
def iso2utf(s):
   def conv(m):
         c = m.group(0)
         return ('\xC2'+c, '\xC3'+chr(ord(c) - 64))[ord(c) > 0xBF]
   return r_iso.sub(conv, s)

def normalize_title(str):
    str = str.replace('/','_')
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

class pageinfo(object):
    def __init__(self,pageurl):
        self.pageurl = pageurl
        self.title = ''
        self.filename = ''
        self.flvurl = ''
        self.subdir = ''

class animeloads(object):
    def throw_error(self,str):
        print str+" "+pageinfo.pageurl
        self.error=True
        return

    def __init__(self,pageinfo):
        self.error=False
        self.pinfo=pageinfo

        data=data=get_data(pageinfo.pageurl)

    #title
        # <span class="tag-0">001: Rollenspiele</span>
        title = textextract(data,'<span class="tag-0">','</span>')
        if not title:
            self.throw_error('couldnt extract title')
            return
        self.pinfo.title=normalize_title(title)
    #/title

    #subdir:
        pageinfo.subdir=textextract(pageinfo.pageurl,'streams/','/')
        try:
            os.makedirs(os.path.join(flash_dir,pageinfo.subdir)) # create path
        except: #TODO better errorhandling here
            pass
    #/subdir

    #type
        url=textextract(data,'<param name="movie" value="','"')
        if url:
            if(url.find('megavideo')>0):
                self.type='megavideo'
                self.flvurl=url
            elif(url.find('eatlime')>0):
                self.type='eatlime'
                self.flvurl=url
            return

        url = textextract(data,'<embed src="','"')
        if url:
            self.type='veoh'
            self.flvurl=url
            return
        self.throw_error('unknown videostream')
        return

class megavideo(object):
    def throw_error(self,str):
        print 'megavideo: '+str+' '+self.url
        return

    def __init__(self,url):
        self.url=url #http://www.megavideo.com/v/W5JVQYMX
        pos1=url.find('/v/')
        if pos1<0:
            throw_error('no valid megavideo url')
            return
        pos1+=len('/v/')
        vId=url[pos1:]
        data=get_data('http://www.megavideo.com/xml/videolink.php?v='+vId)

        tmp = get_urlredirection(self.url)
        if not tmp:
            self.throw_error('problem in getting the redirection')
            return
        # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
        self.flvurl = textextract(tmp,'file=',"&duration")
        if not self.flvurl:
            print '---------'
            self.throw_error('problem in urlextract')
            print tmp
            print '---------'
            return
        return


class eatlime(object):
    def throw_error(self,str):
        print 'eatlime: '+str+' '+self.url
        return

    def __init__(self,url):
        self.url=url
        tmp = get_urlredirection(self.url)
        if not tmp:
            self.throw_error('problem in getting the redirection')
            return
        # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
        self.flvurl = textextract(tmp,'file=',"&duration")
        if not self.flvurl:
            print '---------'
            self.throw_error('problem in urlextract')
            print tmp
            print '---------'
            return
        return

class veoh(object):
    def throw_error(self,str):
        print 'veoh: '+str+' '+self.url
        return

    def __init__(self,url):
        self.url=url
        permalink=textextract(self.url,'&permalinkId=','&id=')
        if not permalink:
            self.throw_error('problem in extracting permalink')
            return
        # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
        # apikey is constant
        data = get_data('http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink='+permalink+'&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36')
        if not data:
            self.throw_error('failed to get data')
            return
        # from data we get the link:
        # http://content.veoh.com/flash/p/2/v832040cHGxXkCJ/002878c1815d34f2ae8c51f06d8f63e87ec179d0.fll?ct=3295b39637ac9bb01331e02fd7d237f67e3df7e112f7452a
        self.flvurl = textextract(data,'fullPreviewHashPath="','"')
        # if we get the redirection from this url, we can manipulate the amount of buffering and download a whole movie pretty
        # fast.. but i have no need for it - just want to remark this for future
        if not self.flvurl:
            self.throw_error('failed to get the url from data')
            print data

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
                    urllist.append(pageinfo('http://anime-loads.org/streams/'+str(i)))
        else:
            urllist.append(pageinfo(sys.argv[1]))

    if len(urllist)==0:
        print 'no urls found'
        usage()
    # example:
    # can be resolved to real url
    for pinfo in urllist:
        aObj = animeloads(pinfo)
        if aObj.error:
            del aObj
            continue
# urlextract/
        if aObj.type=='eatlime':
            tmp=eatlime(aObj.flvurl)
        elif aObj.type=='veoh':
            tmp = veoh(aObj.flvurl)
        elif aObj.type=='megavideo':
            tmp = megavideo(aObj.flvurl)
        else:
            continue

        pinfo.flvurl=tmp.flvurl
        del tmp
        if not pinfo.flvurl:
            continue
# /urlextract


        # File downloader
        fd = FileDownloader({
            'filename': os.path.join(flash_dir,pinfo.subdir,pinfo.title+".flv"),
            'quiet': False,
            })
        retcode = fd.download(pinfo.flvurl)

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
    global GZIP
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
        return '%5s' % ('%3.1f' % (float(byte_counter) / float(data_len) * 100.0))

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

    def report_progress(self, percent_str, downloaded_str, data_len_str, speed_str, eta_str):
        """Report download progress."""
        self.to_stdout(u'\r[ %s%% ] %s of %s at %s ETA %s' %
                (percent_str, downloaded_str, data_len_str, speed_str, eta_str), skip_eol=True)
    def report_finish(self):
        """Report download finished."""
        self.to_stdout(u'')

    def download(self, url):
        """Download a given list of URLs."""

        filename = self._params['filename']
        print "downloading "+url+" to "+filename

        hash = replaceSpecial(url)
        data_len=0
        if os.path.isfile(os.path.join(cache_dir,hash))==1:
            print "using filesizecache: " + os.path.join(cache_dir,hash)
            f=open(os.path.join(cache_dir,hash),"r")
            data_len=int(f.readlines()[0])
            f.close()
        if data_len<1:
            print "no filesizecache"
            request = urllib2.Request(url)
            try:
                data = urllib2.urlopen(request)
            except IOError, e:
                print "seems to be, that this video isn't availabe"
                return

            data_len = int( data.info().get('Content-length', None) )

            if os.path.isfile(os.path.join(cache_dir,hash))==0:
                f=open(os.path.join(cache_dir,hash),"w")
                f.writelines(str(data_len))
                f.close()

        existSize = 0
        if os.path.exists(filename):
            existSize = os.path.getsize(filename)
            if data_len==existSize:
                print "already downloaded"
                return

        # dl resume from http://mail.python.org/pipermail/python-list/2001-October/109914.html
        if existSize > 0:
            print "resuming download "+str(existSize)+" "+str(data_len)
            resume_request = urllib2.Request(url)
            resume_request.add_header('Range', 'bytes=%d-' % (existSize, ))
            try:
                data_tmp = urllib2.urlopen(resume_request)
                check=data_tmp.info().get('Content-Range', None)
                if( not check ):
                    raise IOError
                if( str(existSize) != textextract(check,'bytes ', '-')):
                    print 'server sent us wrong range back requested %s and received %s' % (existSize, check)
                    raise IOError
                # everything was succesfull
                data=data_tmp
                stream = open(filename, 'ab')
            except IOError, e:
                print "server refuses to let us resume so just start from beginninge"
                stream = open(filename, 'wb')
        else:
            stream = open(filename, 'wb')
        if not data:
            request = urllib2.Request(url)
            try:
                data = urllib2.urlopen(request)
            except IOError, e:
                print "seems to be, that this video isn't availabe"
                return



        data_len_str = self.format_bytes( data_len )
        byte_counter = 0
        block_size = 1024
        start = time.time()
        abort=0
        while True:
            # Progress message
            percent_str = self.calc_percent(byte_counter + existSize, data_len)
            eta_str = self.calc_eta(start, time.time(), data_len-existSize, byte_counter)
            speed_str = self.calc_speed(start, time.time(), byte_counter)
            downloaded_str = self.format_bytes( byte_counter + existSize )
            self.report_progress(percent_str, downloaded_str, data_len_str, speed_str, eta_str)

            # Download and write
            before = time.time()
            data_block = data.read(block_size)
            after = time.time()
            if not data_block:
                print "received empty data_block %s %s" % (byte_counter, data_len)
                abort+=1
                time.sleep(10)
                if abort == 2:
                    break
                continue
            abort=0
            data_block_len = len(data_block)
            stream.write(data_block)

            byte_counter += data_block_len
            if byte_counter+existSize == data_len:
                break
            block_size = self.best_block_size(after - before, data_block_len)

        self.report_finish()
        if data_len is not None and byte_counter+existSize != data_len:
            raise ValueError('Content too short: %s/%s bytes' % (byte_counter+existSize, data_len))
        try:
            stream.close()
        except (OSError, IOError), err:
            retcode = self.trouble('ERROR: unable to write video data: %s' % str(err))
            return retcode

main()
