#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import re
import sys
import math
import string
from tools.url import UrlMgr
from config import config
from tools.logging import LogHandler

log = LogHandler('Main')

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
    log.error("usage: ./get.py AnimeLoadslink")
    sys.exit(0)

class PageInfo(object):
    num = 0
    def __init__(self, pageurl):
        self.pageurl  = pageurl
        self.title    = ''
        self.filename = ''
        self.flv_url   = ''
        self.subdir   = ''
        PageInfo.num += 1

class AnimeLoads(object):
    def throw_error(self,str):
        log.error(str + " " + self.pinfo.pageurl)
        self.error = True
        return

    def __init__(self, PageInfo):
        self.error = False
        self.pinfo = PageInfo

        url  = UrlMgr({'url': self.pinfo.pageurl})

    #title
        if not self.pinfo.title:
            # <span class="tag-0">001: Rollenspiele</span>
            title = textextract(url.data, '<span class="tag-0">','</span>')
            # TODO does not work with putfile - look for a way to get it from main-AnimeLoads url
            if not title:
                self.throw_error('couldnt extract title')
                return
            self.pinfo.title=normalize_title(title)
    #/title

    #subdir:
        self.pinfo.subdir=textextract(self.pinfo.pageurl, 'streams/','/')
        try:
            os.makedirs(os.path.join(config.flash_dir,self.pinfo.subdir)) # create path
        except: #TODO better errorhandling here
            pass
    #/subdir

    #type
        link = textextract(url.data,'<param name="movie" value="','"')
        if link:
            if(link.find('megavideo')>0):
                self.type='MegaVideo'
                self.flv_url = link
            elif(url.find('eatlime')>0):
                self.type='EatLime'
                self.flv_url = link
            return

        link = textextract(url.data,'<embed src="','"')
        if link:
            self.type   = 'Veoh'
            self.flv_url = link
            return
        self.throw_error('unknown videostream')
        return

class MegaVideo(object):
    def throw_error(self,str):
        log.error('MegaVideo: '+str+' '+self.url)
        return

    def __init__(self,url):
        self.url=url #http://www.megavideo.com/v/W5JVQYMX
        pos1=url.find('/v/')
        if pos1<0:
            self.throw_error('no valid megavideo url')
            return
        pos1+=len('/v/')
        vId=url[pos1:]
        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=' + vId})
        data = url.data
        un=textextract(data,' un="','"')
        k1=textextract(data,' k1="','"')
        k2=textextract(data,' k2="','"')
        s=textextract(data,' s="','"')
        if( not ( un and k1 and k2 and s) ):
            self.throw_error("couldnt extract un=%s, k1=%s, k2=%s, s=%s"%(un,k1,k2,s))
            return
        hex2bin={'0':'0000','1':'0001','2':'0010','3':'0011','4':'0100','5':'0101','6':'0110','7':'0111','8':'1000','9':'1001','a':'1010','b':'1011',
            'c':'1100','d':'1101','e':'1110','f':'1111'}
        log.info("extract un=%s, k1=%s, k2=%s, s=%s"%(un,k1,k2,s))
        tmp=[]
        for i in un:
            tmp.append(hex2bin[i])
        bin_str=''.join(tmp)
        bin=[]
        for i in bin_str:
            bin.append(i)

        # 2. Generate switch and XOR keys
        k1=int(k1)
        k2=int(k2)
        key = []
        for i in xrange(0,384):
            k1 = (k1 * 11 + 77213) % 81371
            k2 = (k2 * 17 + 92717) % 192811
            key.append( ( (k1+k2) % 128 ) )
        # 3. Switch bits positions
        for i in xrange(256,-1,-1):
            tmp = bin[key[i]];
            bin[key[i]] = bin[(i%128)];
            bin[(i%128)] = tmp;

        # 4. XOR entire binary string
        for i in xrange(0,128):
            bin[i] = str(int(bin[i]) ^ int(key[i+256]) & 1 )

        # 5. Convert binary string back to hexadecimal
        bin2hex = dict([(v, k) for (k, v) in hex2bin.iteritems()])
        tmp=[]
        bin=''.join(bin)
        for i in xrange(0,128/4):
            tmp.append(bin2hex[bin[i*4:(i+1)*4]])
        hex=''.join(tmp)
        self.flv_url='http://www'+s+'.megavideo.com/files/'+hex+'/'
        self.size=int(textextract(data,'size="','"'))

        return


class EatLime(object):
    def throw_error(self,str):
        log.error('EatLime: '+str+' '+self.url)
        return

    def __init__(self,url):
        self.size = 0
        self.url = url
        url_handle = UrlMgr(url)
        if not url_handle.redirection:
            self.throw_error('problem in getting the redirection')
            return
        # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
        self.flv_url = textextract(url.redirection, 'file=',"&duration")
        if not self.flv_url:
            print '---------'
            self.throw_error('problem in urlextract')
            print tmp
            print '---------'
            return
        return

class Veoh(object):
    def throw_error(self,str):
        log.error('Veoh: ' + str + ' ' + self.url)
        return

    def __init__(self,url):
        self.size=0
        self.url=url
        permalink=textextract(self.url,'&permalinkId=','&id=')
        if not permalink:
            self.throw_error('problem in extracting permalink')
            return
        # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
        # apikey is constant
        url = UrlMgr({'url': 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search' +
                            '&type=video&maxResults=1&permalink='+permalink+'&contentRatingId=3' +
                            '&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36'})
        if not url.data:
            self.throw_error('failed to get data')
            return
        # from data we get the link:
        # http://content.veoh.com/flash/p/2/v832040cHGxXkCJ/002878c1815d34f2ae8c51f06d8f63e87ec179d0.fll?ct=3295b39637ac9bb01331e02fd7d237f67e3df7e112f7452a
        self.flv_url = textextract(url.data, 'fullPreviewHashPath="','"')
        # self.size   = int(textextract(data,'size="','"')) seems to be wrong 608206848 for a 69506379 video
        # if we get the redirection from this url, we can manipulate the amount of buffering and download a whole movie pretty
        # fast.. but i have no need for it - just want to remark this for future
        if not self.flv_url:
            if textextract(url.data, 'items="', '"') == '0':
                self.throw_error('this video is down by veoh')
            self.throw_error('failed to get the url from data')

def main():
    urllist=[]

    if len(sys.argv)<2:
        usage()
    else:
        if( sys.argv[1].find('/streams/') < 0):
            # <a href="../streams/_hacksign/003.html"
            # user added video-overview-url
            url = UrlMgr({'url': sys.argv[1]})
            if not url.data:
                usage()
            links=textextractall(url.data, '<a href="../streams/','"')
            if len(links)>0:
                for i in links:
                    tmp = PageInfo('http://anime-loads.org/streams/' + str(i))
                    urllist.append(tmp)
                    log.info('added url: ' + str(tmp.num) + ' ' + tmp.pageurl)
        else:
            urllist.append(PageInfo(sys.argv[1]))

    if len(urllist)==0:
        log.error('no urls found')
        usage()
    # example:
    # can be resolved to real url
    for pinfo in urllist:
        aObj = AnimeLoads(pinfo)
        if aObj.error:
            del aObj
            continue
# urlextract/
        if aObj.type == 'EatLime':
            tmp = EatLime(aObj.flv_url)
        elif aObj.type == 'Veoh':
            tmp = Veoh(aObj.flv_url)
        elif aObj.type == 'MegaVideo':
            tmp = MegaVideo(aObj.flv_url)
        else:
            log.warning("strange video-type - continue")
            continue

        pinfo.flv_url = tmp.flv_url
        size = tmp.size
        del tmp
        if not pinfo.flv_url:
            continue
# /urlextract


        # File downloader
        fd = FileDownloader({
            'filename': os.path.join(config.flash_dir,pinfo.subdir,pinfo.title+".flv"),
            'quiet': False,
            'size': size,
            })
        retcode = fd.download(pinfo.flv_url)

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

    def report_progress(self, percent_str, downloaded_str, data_len_str, speed_str, eta_str):
        """Report download progress."""
        self.to_stdout(u'\r[ %s%% ] %s of %s at %s ETA %s' %
                (percent_str, downloaded_str, data_len_str, speed_str, eta_str), skip_eol=True)
    def report_finish(self):
        """Report download finished."""
        self.to_stdout(u'')

    def download(self, link):

        filename = self._params['filename']
        log.info("downloading "+link+" to "+filename)

        data_len=0

        url = UrlMgr({'url': link})
        if self._params['size']:
            data_len=self._params['size']
        else:
            data_len = url.size

        existSize = 0
        if os.path.exists(filename):
            existSize = os.path.getsize(filename)
            if data_len==existSize:
                log.info("already downloaded")
                return

        # dl resume from http://mail.python.org/pipermail/python-list/2001-October/109914.html
        can_resume = False
        if(existSize > 0 and existSize < data_len):
            log.info("trying to resume")
            url.position = existSize
            if url.got_requested_position():
                log.info("can resume")
                stream = open(filename, 'ab')
                can_resume = True

        if not can_resume:
            log.info("couldnt resume")
            existSize = 0
            stream = open(filename, 'wb')

        data_len_str = self.format_bytes( data_len )
        byte_counter = 0
        block_size = 1024
        start = time.time()
        abort=0
        url.pointer # dummy call to avoid strange output ( so that pointer will get first downloaded before entering while-loop)
        while True:
            # Progress message
            percent_str = self.calc_percent(byte_counter + existSize, data_len)
            eta_str = self.calc_eta(start, time.time(), data_len-existSize, byte_counter)
            speed_str = self.calc_speed(start, time.time(), byte_counter)
            downloaded_str = self.format_bytes( byte_counter + existSize )
            self.report_progress(percent_str, downloaded_str, data_len_str, speed_str, eta_str)

            # Download and write
            before = time.time()
            data_block = url.pointer.read(block_size)
            after = time.time()
            if not data_block:
                log.info("received empty data_block %s %s %s" % (byte_counter, str(byte_counter+existSize), data_len))
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
            log.error('ERROR: unable to write video data: %s' % str(err))
            return -1

main()
