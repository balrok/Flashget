# -*- coding: utf-8 -*-

import os
import time
import re
import sys
import math
import string
import tools.url as Url
from tools.url import UrlMgr
from tools.small_ids import SmallId

import config

from tools.logging import LogHandler

import threading, thread
import Queue

log = LogHandler('Main')


def normalize_title(str):
    str = str.replace('/', '_')
    # return unicode(str,'iso-8859-1')
    return str
    # return str.decode('iso-8859-1')


def textextract(data, startstr, endstr):
    pos1=data.find(startstr)
    if pos1 < 0:
        return
    pos1 += len(startstr)
    pos2 = data.find(endstr, pos1)
    if pos2 < 0:
        return
    return data[pos1:pos2]


def textextractall(data, startstr, endstr):
    startpos  = 0
    foundlist = []
    while True:
        pos1 = data.find(startstr, startpos)
        if pos1 < 0:
            return foundlist
        pos1 += len(startstr)
        pos2 = data.find(endstr, pos1)
        if pos2 < 0:
            return foundlist
        startpos = pos2 + len(endstr) + 1                         # TODO look if this is ok
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
        self.flv_url  = ''
        self.subdir   = ''
        PageInfo.num  += 1


class AnimeLoads(object):

    def throw_error(self, str):
        log.error(str + " " + self.pinfo.pageurl)
        self.error = True
        return

    def __init__(self, PageInfo, log_ = log):
        self.error = False
        self.pinfo = PageInfo
        self.log = log_
        url = UrlMgr({'url': self.pinfo.pageurl, 'log': self.log})
        #title
        if self.pinfo.title == '':
            title = textextract(url.data, '<span class="tag-0">','</span>')
            # TODO does not work with putfile - look for a way to get it from main-AnimeLoads url
            if not title:
                self.throw_error('couldnt extract title')
                return
            self.pinfo.title = normalize_title(title)
        #/title

        #subdir:
        self.pinfo.subdir = textextract(self.pinfo.pageurl, 'streams/','/')
        try:
            os.makedirs(os.path.join(config.flash_dir, self.pinfo.subdir))
        except:
            pass # TODO better errorhandling
        #/subdir

        #type
        link = textextract(url.data,'<param name="movie" value="','"')
        if link:
            if link.find('megavideo') > 0:
                self.type='MegaVideo'
                self.flv_url = link
            elif url.data.find('eatlime') > 0:
                self.type='EatLime'
                self.flv_url = link
            return

        link = textextract(url.data,'<embed src="', '"')
        if link:
            if link.find('veoh.com') > 0:
                self.type='Veoh'
                self.flv_url = link
                return
        self.throw_error('unknown videostream')
        return


class MegaVideo(object):

    def throw_error(self, str):
        log.error('MegaVideo: '+str+' '+self.url)
        return

    def __init__(self, url, log_ = log):
        self.url = url #http://www.megavideo.com/v/W5JVQYMX
        pos1=url.find('/v/')
        self.log = log_
        if pos1 < 0:
            self.throw_error('no valid megavideo url')
            return
        pos1 += len('/v/')
        vId = url[pos1:]
        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=' + vId, 'log': self.log})
        data = url.data
        un=textextract(data,' un="','"')
        k1=textextract(data,' k1="','"')
        k2=textextract(data,' k2="','"')
        s=textextract(data,' s="','"')
        if( not ( un and k1 and k2 and s) ):
            self.throw_error("couldnt extract un=%s, k1=%s, k2=%s, s=%s"%(un, k1, k2, s))
            return
        hex2bin={'0':'0000','1':'0001','2':'0010','3':'0011','4':'0100','5':'0101','6':'0110','7':'0111','8':'1000','9':'1001','a':'1010','b':'1011',
            'c':'1100','d':'1101','e':'1110','f':'1111'}
        log.info("extract un=%s, k1=%s, k2=%s, s=%s"%(un, k1, k2, s))
        tmp=[]
        for i in un:
            tmp.append(hex2bin[i])
        bin_str = ''.join(tmp)
        bin = []
        for i in bin_str:
            bin.append(i)

        # 2. Generate switch and XOR keys
        k1 = int(k1)
        k2 = int(k2)
        key = []
        for i in xrange(0,384):
            k1 = (k1 * 11 + 77213) % 81371
            k2 = (k2 * 17 + 92717) % 192811
            key.append((k1 + k2) % 128)
        # 3. Switch bits positions
        for i in xrange(256, -1, -1):
            tmp = bin[key[i]];
            bin[key[i]] = bin[i % 128];
            bin[i % 128] = tmp;

        # 4. XOR entire binary string
        for i in xrange(0, 128):
            bin[i] = str(int(bin[i]) ^ int(key[i+256]) & 1 )

        # 5. Convert binary string back to hexadecimal
        bin2hex = dict([(v, k) for (k, v) in hex2bin.iteritems()])
        tmp = []
        bin = ''.join(bin)
        for i in xrange(0,128/4):
            tmp.append(bin2hex[bin[i * 4:(i + 1) * 4]])
        hex = ''.join(tmp)
        self.flv_url = 'http://www'+s+'.megavideo.com/files/'+hex+'/'
        self.size = int(textextract(data,'size="','"'))
        return


class EatLime(object):

    def throw_error(self, str):
        log.error('EatLime: ' + str + ' ' + self.url)
        return

    def __init__(self, url, log_ = log):
        self.size = 0
        self.url = url
        self.log = log_
        url_handle = UrlMgr({'url': url, 'log': self.log})
        if not url_handle.redirection:
            self.throw_error('problem in getting the redirection')
            return
        # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
        self.flv_url = textextract(url_handle.redirection, 'file=',"&duration")
        if not self.flv_url:
            self.log.info('---------')
            self.throw_error('problem in urlextract')
            self.log.info(tmp)
            self.log.info('---------')
            return
        return


class Veoh(object):

    def throw_error(self,str):
        log.error('Veoh: ' + str + ' ' + self.url)
        return

    def __init__(self, url, log_ = log):
        self.size = 0
        self.url = url
        self.log = log_
        permalink = textextract(self.url,'&permalinkId=', '&id=')
        if not permalink:
            self.throw_error('problem in extracting permalink')
            return
        # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
        # apikey is constant
        url = UrlMgr({'url': 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search' +
                            '&type=video&maxResults=1&permalink='+permalink+'&contentRatingId=3' +
                            '&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36', 'log': self.log})
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
    log = LogHandler('Main')
    # log.info(normalize_title('überschallwolke'))

    urllist = []

    if len(sys.argv) < 2:
        usage()
    else:
        if sys.argv[1].find('/streams/') < 0:
            # <a href="../streams/_hacksign/003.html"
            # user added video-overview-url
            url = UrlMgr({'url': sys.argv[1], 'log': log})
            if not url.data:
                usage()
            links = textextractall(url.data, '<a href="../streams/','"')
            if len(links) > 0:
                for i in links:
                    tmp = PageInfo('http://anime-loads.org/streams/' + str(i))
                    urllist.append(tmp)
                    log.info('added url: ' + str(tmp.num) + ' ' + tmp.pageurl)
        else:
            urllist.append(PageInfo(sys.argv[1]))

    if len(urllist)==0:
        log.error('no urls found')
        usage()

    download_queue = Queue.Queue(0)
    flashWorker = FlashWorker(download_queue)
    flashWorker.start()
    config.win_mgr.threads.append(flashWorker)
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
        download_queue.put(pinfo, True)
# /urlextract


class FlashWorker(threading.Thread):

    def __init__(self, queue, log_ = log):
        self.dl_queue = Queue.Queue()
        self.in_queue = queue
        self.dl_list = {}
        self.log = LogHandler('FlashWorker', log_)
        self.str = {}
        self.download_limit = Queue.Queue(config.dl_instances)
        threading.Thread.__init__(self)

        self.small_id = SmallId(self.log, 0)

        # self.mutex_dl_begin = thread.allocate_lock()

    def print_dl_list(self):
        self.log.info('dl-list changed:')
        # for i in xrange(0, len(self.dl_list)):
        #    self.log.info('%d : %s' % (i, self.dl_list[i]['pinfo'].title))

    def dl_preprocess(self):
        while True:
            pinfo = self.in_queue.get(True)
            self.in_queue.task_done()
            log.info(pinfo.title)

            downloadfile = os.path.join(config.flash_dir, pinfo.subdir, pinfo.title + '.flv')
            log.info('preprocessing download for' + downloadfile)
            url = Url.LargeDownload({'url': pinfo.flv_url, 'queue': self.dl_queue, 'log': self.log, 'cache_folder':
            os.path.join(pinfo.subdir, pinfo.title)})

            if url.size < 1024:
                self.log.error('flashvideo is to small - looks like the streamer don\'t want to send us the real video')
                continue
            if os.path.isfile(downloadfile):
                if os.path.getsize(downloadfile) == url.size:
                    self.log.info('already completed 1')
                    continue
                else:
                    self.log.info('not completed '+str(os.path.getsize(downloadfile))+':'+str(url.size))

            self.download_limit.put(1)
            url.id = self.small_id.new()

            data_len_str = format_bytes(url.size)
            start = time.time()
            tmp = {'start':start, 'url':url, 'data_len_str':data_len_str, 'pinfo':pinfo}
            self.dl_list[url.id] = tmp

            url.start()

            self.print_dl_list()

    def dl_postprocess(self, id):
        dl  = self.dl_list[id]
        url = dl['url']
        pinfo = dl['pinfo']
        downloadfile = os.path.join(config.flash_dir,pinfo.subdir,pinfo.title+".flv")
        log.info('postprocessing download for' + downloadfile)
        if url.state & Url.LargeDownload.STATE_FINISHED:
            os.rename(url.save_path, downloadfile)
        else:
            self.log.info('unhandled urlstate '+str(url.state)+' in postprocess')
            # error happened, but we will ignore it
            pass
        del self.dl_list[id]
        if id in self.str:
            del self.str[id]
        self.download_limit.get()
        self.download_limit.task_done()
        self.small_id.free(id)

    def run(self):
        threading.Thread(target=self.dl_preprocess).start()
        while True:
            # self.mutex_dl_begin.acquire()
            id  = self.dl_queue.get(True)
            # self.mutex_dl_begin.release()

            now = time.time()
            dl  = self.dl_list[id]
            url = dl['url']
            if(url.state == Url.LargeDownload.STATE_ALREADY_COMPLETED or url.state & Url.LargeDownload.STATE_FINISHED or url.state & Url.LargeDownload.STATE_ERROR):
                self.dl_postprocess(id)

            start = dl['start']
            data_len_str = dl['data_len_str']
            percent_str = calc_percent(url.downloaded, url.size)
            eta_str     = calc_eta(start, now, url.size - url.position, url.downloaded - url.position)
            speed_str   = calc_speed(start, now, url.downloaded - url.position)
            downloaded_str = format_bytes(url.downloaded)
            self.str[id] = ' [%s%%] %s/%s at %s ETA %s  %s' % (percent_str, downloaded_str, data_len_str, speed_str, eta_str, dl['pinfo'].title)
            config.win_mgr.progress.add_line(self.str[id], id)


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


def calc_percent(byte_counter, data_len):
    if data_len is None:
        return '---.-%'
    return '%5s' % ('%3.1f' % (float(byte_counter) / float(data_len) * 100.0))


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


def calc_speed(start, now, bytes):
    dif = now - start
    if bytes == 0 or dif < 0.001: # One millisecond
        return '%10s' % '---b/s'
    return '%10s' % ('%s/s' % format_bytes(float(bytes) / dif))
