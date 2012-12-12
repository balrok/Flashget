import time

from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract, textextractall
import config
from tools.extension import Extension

import logging

log = logging.getLogger('streams')


class BaseStream(object):
    def __init__(self):
        self.flvUrl = ''
    def get(self, VideoInfo, justId=False, isAvailable=False):
        raise Exception
    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)


class MegaVideo(Extension, BaseStream):
    ename = 'Megavideo'
    eregex = '.*megavideo.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        hex2bin = {'0':'0000','1':'0001','2':'0010','3':'0011','4':'0100','5':'0101','6':'0110','7':'0111','8':'1000','9':'1001','a':'1010','b':'1011',
            'c':'1100','d':'1101','e':'1110','f':'1111'}
        bin2hex = dict([(v, k) for (k, v) in hex2bin.iteritems()])
        # TODO: reconnect as in veoh.. or maybe in megavideo_call
        # VideoInfo.stream_url should look like this:
        # http://www.megavideo.com/v/W5JVQYMX or http://www.megavideo.com/v/KES7QC7Ge1a8d728bd01bf9965b2918a458af1dd.6994310346.0
        # the first 8 chars after /v/ are interesting for us, they are the vId
        url = VideoInfo.stream_url

        for i in ('/v/', '&v=', '?v='):
            pos1 = url.find(i)
            if pos1 >= 0:
                break
        else:
            log.error('no valid megavideo url %s' % url)
            return False
        pos1 += len('/v/')
        vId = url[pos1:pos1+8]
        if justId:
            return vId

        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=%s' % vId})
        if url.data.find('error="1"') >= 0:
            errormsg = textextract(url.data, 'errortext="', '"></ROW>')
            if errormsg.find('temporarily') > 0:
                log.info("retry temporarily not available video")
                # reconnect and look if it is now online
                url.setCacheWriteOnly()
                url.clear_connection()

        if url.data.find('error="1"') >= 0:
            errormsg = textextract(url.data, 'errortext="', '"></')
            log.info('megavideo-error with msg: %s' % errormsg)
            return False

        if isAvailable:
            return True

        def extractFlvUrl(url):
            un = textextract(url.data, ' un="', '"')
            k1 = textextract(url.data, ' k1="', '"')
            k2 = textextract(url.data, ' k2="', '"')
            s  = textextract(url.data, ' s="', '"')
            if( not (un and k1 and k2 and s) ):
                log.error(url.data)
                log.error("couldnt extract un,k1,k2,s from "+VideoInfo.url)
                return False

            bin = []
            for i in un:
                bin.extend(hex2bin[i])

            # 2. Generate switch and XOR keys
            k1 = int(k1)
            k2 = int(k2)
            key = []
            for i in xrange(0, 384):
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
                bin[i] = str(int(bin[i]) ^ int(key[i + 256]) & 1)

            # 5. Convert binary string back to hexadecimal
            tmp = []
            bin = ''.join(bin)
            for i in xrange(0, 128 / 4):
                tmp.append(bin2hex[bin[i * 4:(i + 1) * 4]])
            hex = ''.join(tmp)
            # size = int(textextract(url.data,'size="','"')) # i'm not 100% sure, if this size is right
            flv_url = 'http://www%s.megavideo.com/files/%s/' % (s, hex)
            return flv_url

        flv_url = extractFlvUrl(url)
        if not flv_url:
            return False
        # test if the url works
        testUrl = UrlMgr({'url':flv_url})
        if testUrl.pointer.head.status == 404 or testUrl.pointer.head.status == 403:
            testUrl.setCacheWriteOnly()
            testUrl.clear_connection()
            flv_url = extractFlvUrl(url)
            if not flv_url:
                return False
            testUrl = UrlMgr({'url':flv_url})
            if testUrl.pointer.head.status == 404 or testUrl.pointer.head.status == 403:
                log.error("Megavideo doesn't want to send us the video")
                return False
        testUrl.pointer.removeFromConns(True)

        self.flvUrl = flv_url
        return self.flvUrl

    def download(self, **kwargs):
        kwargs['url'] = self.flvUrl
        diff = config.megavideo_wait - time.time()
        if diff > 0:
            args['log'].error('megavideo added us to the waitlist, will be released in %02d:%02d' % (diff / 60, diff % 60))
            # TODO how to handle this case
            # the program to get those flashfiles
            # args['download_queue'].put((args['pinfo'].name, args['pinfo'], time.time()+diff))
            return False
        kwargs['megavideo'] = True
        return LargeDownload(**kwargs)


class Eatlime(Extension, BaseStream):
    ename = 'Eatlime'
    eregex = '.*eatlime.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            return "TODO implement"
        url = VideoInfo.stream_url
        url = url.rstrip()
        url_handle = UrlMgr({'url': url})
        if not url_handle.redirection:
            log.error('problem in getting the redirection')
            return False
        flv_url = textextract(url_handle.redirection, 'file=', '&duration')
        if not flv_url:
            log.error('problem in urlextract from: %s' % url_handle.redirection)
            return False
        elif flv_url == '.flv':
            log.error('eatlime-videolink is down (dl-file is only .flv): %s' % url_handle.redirection)
            return False
        self.flvUrl = flv_url
        return self.flvUrl


class VideoBB(Extension, BaseStream):
    ename = 'VideoBB / VideoZer'
    eregex = '(.*videobb.*)|(.*videozer.*)'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if VideoInfo.stream_url.find('/f/') > 0:
            VideoInfo.stream_url = VideoInfo.stream_url.replace('/f/', '/video/')
            VideoInfo.stream_url = VideoInfo.stream_url.replace('.swf', '')
        if VideoInfo.stream_url.find('/flash/') > 0:
            VideoInfo.stream_url = VideoInfo.stream_url.replace('/flash/', '/video/')
            VideoInfo.stream_url = VideoInfo.stream_url.replace('.swf', '')
        #embed url
        if VideoInfo.stream_url.find('/e/') > 0:
            VideoInfo.stream_url = VideoInfo.stream_url.replace('/e/', '/video/')
        if VideoInfo.stream_url.find('/embed/') > 0:
            VideoInfo.stream_url = VideoInfo.stream_url.replace('/embed/', '/video/')
        if justId:
            id = textextract(VideoInfo.stream_url, '/video/', '')
            if not id:
                id = textextract(VideoInfo.stream_url, '/v/', '')
            return id
        url = UrlMgr(url=VideoInfo.stream_url, cache_writeonly=True)
        if not url.data.find('setting=') > 0:
            log.error('videobb couldn\'t find setting in url.data of url: %s' % VideoInfo.stream_url)
            return False
        if isAvailable:
            return True
        settingLink = textextract(url.data, 'setting=', '"').decode('base64')
        url = UrlMgr(url=settingLink)
        for i in ['480p', '360p', '240p', 'HQ', 'LQ']:
            print url.data
            dlUrl = textextract(url.data, '"l":"'+i+'","u":"', '"')
            if dlUrl:
                dlUrl = dlUrl.decode('base64')
                break
        if not dlUrl:
            log.error("no stream in videobb found")
            log.error(url.data)
        self.flvUrl = dlUrl
        return self.flvUrl


class Myvideo(Extension, BaseStream):
    ename = 'Myvideo'
    eregex = '.*myvideo.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            id = textextract(VideoInfo.stream_url, '/watch/', '/')
            if not id:
                id = textextract(VideoInfo.stream_url, '/watch/', '')
            return id
        url = UrlMgr({'url': VideoInfo.stream_url})
        if isAvailable:
            if url.data.find('error_screen\'') > 0:
                return False
            return True
        # TODO implement downloading of macromedia-fcs protocol


class StageVU(Extension, BaseStream):
    ename = 'StageVU'
    eregex = '.*stagevu.*'
    # very easy has a downloadlink inside :)
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            return "TODO implement"
        VideoInfo.stream_url = VideoInfo.stream_url.replace('&amp;', '&')
        url = UrlMgr({'url': VideoInfo.stream_url})
        dlUrl = textextract(url.data, '<param name="src" value="', '"')
        if not dlUrl:
            log.error("no stream in stagevu found url: %s" % VideoInfo.stream_url)
            log.error(url.data)
        self.flvUrl = dlUrl
        return self.flvUrl


class Veoh(Extension, BaseStream):
    ename = 'Veoh'
    eregex = '.*veoh.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        url = VideoInfo.stream_url
        permalink = textextract(url, 'permalinkId=', '')
        if not permalink:
            url = UrlMgr(url=url, cookies=['confirmedAdult=true'])
            if not url.data.find("Sorry, we couldn't find the video you were looking for.") > 0:
                link = textextract(url.data, "location.href = '", "'")
                if link:
                    url = UrlMgr(url=link, cookies=['confirmedAdult=true'])
                from tools.stream import extract_stream
                stream = extract_stream(url.data)
                if stream and stream['url']:
                    permalink = textextract(stream['url'], 'permalinkId=', '')
            if not permalink:
                log.error('Veoh: problem in extracting permalink')
                return False
        else:
            # permalink will be extracted until the first occurence of an ampersand (&) or until the end
            a = permalink.find('&')
            if a >= 0:
                permalink = permalink[:a]
        if justId:
            return permalink
        if isAvailable:
            if permalink:
                return True
            return False

        def veoh_try(cache_writeonly):
            # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
            # apikey is constant
            # but this file changes it's content every 24h <- thats why we need to disable the cache sometimes
            link = 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=%s&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36' % permalink
            url = UrlMgr(url=link, cache_writeonly=cache_writeonly)

            if not url.data:
                return (False, 'Veoh: failed to get data')
            # from data we get the link:
            # http://content.veoh.com/flash/p/2/v832040cHGxXkCJ/002878c1815d34f2ae8c51f06d8f63e87ec179d0.fll?ct=3295b39637ac9bb01331e02fd7d237f67e3df7e112f7452a
            flv_url = textextract(url.data, 'fullPreviewHashPath="','"')
            # size   = int(textextract(data,'size="','"')) seems to be wrong 608206848 for a 69506379 video
            # but we could download previewPieceHashFile there is the size

            if not flv_url:
                if textextract(url.data, 'items="', '"') == '0':
                    return (False, 'Veoh: this video is down by veoh')
                return (False, 'Veoh: failed to get the url from data')
            url = UrlMgr({'url': flv_url})
            if url.pointer.head.status == 403:
                return (False, True) # mostly will mean that we need to disable cache
            flv_url = url.redirection
            # will look like this: http://veoh-099.vo.llnwd.net/Vpreviews/f/63b2ea3d2c397455842496f9525aa20bc7766318.flv?e=1244905032&ri=5000&rs=90&h=faa1660220996a5d92652b1774aad697
            return (flv_url, 0)

        a = veoh_try(False)
        if not a[0]:
            if a[1] == True: # only at this case we will retry
                a = veoh_try(True)
                if a[0]:
                    log.info('successfully restored veoh-download')
                else:
                    log.info('couldn\'t restore veoh download')
        if not a[0]:
            log.error(a[1])
            return False

        self.flvUrl = a[0]
        return self.flvUrl


class Sevenload(Extension, BaseStream):
    ename = 'Sevenload'
    eregex = '.*sevenload.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        url = VideoInfo.stream_url
        # source: http://de.sevenload.com/pl/uPJq7C8/490x317/swf,play
        # or http://datal3.sevenload.com/data76.sevenload.com/slcom/gk/qi/cksmnmd/xtldnnplemof.flv
        # which is already the full url
        # we need to go to http://flash.sevenload.com/player?itemId=uPJq7C8
        if url.find('slcom/') == -1:
            id = textextract(url, 'pl/', '/')
            if justId:
                return id
            log.info(url)
            url = UrlMgr({'url': 'http://flash.sevenload.com/player?itemId=%s' % id})
            if not url.data:
                log.error('seven_load: failed to fetch xml')
                return False
            #<location seeking="yes">http://data52.sevenload.com/slcom/qt/jw/echlkg/xztlpgdgghgc.flv</location>
            flv_url = textextract(url.data, '<location seeking="yes">', '</location>')
        else: # we already got the flashurl - but can't check for errors here - in errorcase it will throw a 404 at downloading
            if justId:
                return "TODO implement"
            flv_url = url
        self.flvUrl = flv_url
        return self.flvUrl

class Plain(Extension, BaseStream):
    ename = 'Plain Download'
    eregex = '(.*\.(flv|mp4))|(.*youtube.*)'
    elowestPriority = True
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            return ''
        if isAvailable:
            return True
        self.flvUrl = VideoInfo.stream_url
        return self.flvUrl


class Putlocker(Extension, BaseStream):
    ename = 'Putlocker'
    eregex = 'http://www.(putlocker|sockshare).com/file/[A-Z0-9]{16}#?$'
    cookieCache = []

    def doTheContinueAsNormalUser(self, link):
        url = UrlMgr(url=link, cache_writeonly=True, keepalive=False)
        for cookie in url.pointer.cookies: # refresh putlockerCookieCache
            phpsessid = textextract(cookie, 'PHPSESSID=', '; ')
            if phpsessid:
                phpsessid = 'PHPSESSID='+phpsessid
                Putlocker.cookieCache = [phpsessid]
                break
        posthash = textextract(url.data, '<input type="hidden" value="', '" name="hash">')
        if not posthash:
            log.error("putlocker couldn't find hash - so we are already logged in?")
            return url.data

        # just send
        UrlMgr(url= link, post='hash='+posthash+"&confirm=Continue+as+Free+User", cookies=Putlocker.cookieCache, keepalive=False, referer=link, nocache=True).data
        # now normal get and cache
        url = UrlMgr(url=link, cookies=Putlocker.cookieCache, cache_writeonly=True)
        return url.data

    def get(self, VideoInfo, justId=False, isAvailable=False):
        id = textextract(VideoInfo.stream_url, '/file/', '')
        if justId:
            return id

        if Putlocker.cookieCache != []:
            data = UrlMgr({'url': VideoInfo.stream_url, 'cookies':Putlocker.cookieCache}).data
        else:
            data = self.doTheContinueAsNormalUser(VideoInfo.stream_url)

        if isAvailable:
            return data.find("<div class='warning_message'>") == -1 # and data.find('playlist: \'') != -1

        getfile = textextract(data, 'playlist: \'', '\'')
        if not getfile:
            data = UrlMgr({'url': VideoInfo.stream_url, 'cookies':Putlocker.cookieCache, 'cache_writeonly':True}).data
            getfile = textextract(data, 'playlist: \'', '\'')
        if not getfile:
            log.error("No Getfile in putlocker video maybe just not available")
            return False

        def getDlUrl(getfile):
            url = UrlMgr({'url': 'http://www.putlocker.com'+getfile, 'cookies': Putlocker.cookieCache, 'cache_writeonly':True})
            url.clear_connection()
            dlUrl = textextract(url.data, '<media:content url="', '"')
            return dlUrl

        dlUrl = getDlUrl(getfile)

        if not dlUrl or dlUrl == 'http://images.putlocker.com/images/expired_link.gif':
            log.info("RETRY")
            dlUrl = getDlUrl(getfile)
        if not dlUrl or dlUrl == 'http://images.putlocker.com/images/expired_link.gif':
            log.error("putlocker not found")
            return None
        self.flvUrl = dlUrl
        return self.flvUrl


class Zeec(Extension, BaseStream):
    ename = 'Zeec'
    eregex = '.*zeec.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            return 'TODO implement'
        url = VideoInfo.stream_url
        url = UrlMgr({'url': url})
        link = textextract(url.data, 'var xml = \'', '\';')
        # now we get a xml-file with much information (reminds me a bit to the voeh-xml)
        url = UrlMgr({'url': link})
        # 72       <property name="src"
        # 73                 value="http://ugc04.zeec.de/v/flv1/0x0/9229/99229_yq54tkgU4OVUgDEsxJFUEKMeKoe9YZFA.flv"/>
        # 74       <property name="hd_src"
        # 75                 value="http://ugc02.zeec.de/v/ipod/640x480/9229/99229_yq54tkgU4OVUgDEsxJFUEKMeKoe9YZFA.mp4"/>
        x = url.data.find('name="hd_src"')
        flv_url, x = textextract(url.data, 'value="', '"', x)
        self.flvUrl = dlUrl
        return self.flvUrl


class XvidGeneric(Extension, BaseStream):
    ename = 'XvidGeneric'
    eregex = '.*(hdivx\.to|freeload\.to|clickandload\.net|upsharex\.com|skyload\.net).*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        if justId:
            return "TODO implement"
        # 1. http://hdivx.to/?Module=Details&HashID=FILE4A344C620E2CB
        # 2. http://hdivx.to/Get/?System=Play&Hash=FILE4A344C620E2CB
        # redirects to http://divx0.hdivx.to/00002000/062499466a985489952d7e3737805328
        # it's important that we send the referer in the last link too
        url = VideoInfo.stream_url
        if url.find('HashID') != -1:
            hash = textextract(url, 'HashID=', '')
            host = url[:url.find('/', 10)]
            link2 = host + '/' + 'Get/?System=Play&Hash=' + hash
            url = UrlMgr({'url': link2})
            flv_url = url.get_redirection()
        else:
            link2 = url
            url_handle = UrlMgr({'url': url})
            x = url_handle.data.find('object classid')
            flv_url = textextract(url_handle.data, 'param name="src" value="', '"')
        self.referer = link2
        self.flvUrl = flv_url
        return self.flvUrl

    def download(self, **kwargs):
        kwargs['url'] = self.flvUrl
        kwargs['referer'] = self.referer
        kwargs['reconnect_wait'] = 2 # xvid downloads (very) often close the connection, thats why this is handled a bit special here
        kwargs['retries'] = 30 # after one minute, we can assume that they won't send us anything
        return LargeDownload(**kwargs)


# ccf could only be written through jdownloader source, thanks :)
class CCF(Extension, BaseStream):
    ename = 'CCF'
    eregex = '.*crypt-it\.com.*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        from helper import get_aes
        import binascii
        if justId or isAvailable:
            return None

        url = VideoInfo.stream_url

        x = url.rfind('/')
        folder = url[x+1:]

        url_handle = UrlMgr({'url': 'http://crypt-it.com/c/' + folder})
        info = url_handle.data
        packagename = textextract(info, 'class="folder">', '</')
        pw = ''
        if packagename == 'Acces denied! Password required':
            pw = 'folder' # TODO create an user-input dialog when the folder has a password
            post = 'a=pw&pw='+pw
            url_handle = UrlMgr({'url': 'http://crypt-it.com/s/'+folder, 'post': post})
            info = url_handle.data

        packagename = textextract(info, 'class="folder">', '</')
        password = textextract(info, '<b>Password:</b> ', '\t')

        bs = '\x00\x00\x00\x00\x00\x01\x00\x11cryptit2.getFiles\x00\x02/1\x00\x00\x00\x11\n\x00\x00\x00\x02\x02\x00\x06'
        b2s = '\x02\x00'
        post = bs + folder + b2s + str(len(pw)) + pw
        url_handle = UrlMgr(url='http://crypt-it.com/engine/', post=post, content_type='application/x-amf')
        ccf = url_handle.data

        info = textextractall(ccf, 'id', 'clicks') # notice: we wont get the information about the last click (but uninteresting anyway)
        log.info('package "%s" with password "%s"' % (packagename, password))

        # initialize aes module
        aes = get_aes('so5sxNsPKfNSDDZHayr32520', log)

        flv_urls = []
        for file in info:
            # 4925379 folder EZP39M file Vampire_Hunter_D.part6.rar url 19cc85884959252328c86b465ca02e8f6ecb41983853a9caee54076bb147074119fe9000c477bc42859f47a639d6f4176f4f0a77a439aef221dde07f38be8afa size 88109 KB status 1 

            # name = textextract(file, 'file\x92\00,', '\x00')

            # first sign (we drop) is the length of the string
            url = textextract(file, 'url\x02\x00', '\x00')[1:]
            url = aes.decrypt(binascii.unhexlify(url))
            url = url.rstrip('\x00')

            flv_urls.append(url)
            log.info(url)
        self.flvUrl = flvUrls
        return self.flvUrl

class Dlc(Extension, BaseStream):
    ename = 'dlc'
    eregex = '.*\.dlc'
    elowestPriority = True
    def get(self, VideoInfo, justId=False, isAvailable=False):
        from helper import get_aes
        from Crypto.Cipher import AES
        import binascii

        url = VideoInfo.stream_url

        dest_type = config.dlc['dest_type']
        key       = config.dlc['key']
        iv        = config.dlc['iv']
        url_handle = UrlMgr({'url': url})
        data = url_handle.data

        hello_data = dlc_file[-88:]
        url = 'http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=%s&data=%s' % (dest_type, hello_data)
        url_handle = UrlMgr({'url': url})

        # result: "<rc>ytz16ih0Ud5xJW3Izgg72g==</rc>"
        key1 = url_handle.data[4:-5]
        key1 = key1.decode('base64')
        aes = AES.new(key, AES.MODE_CBC, iv)
        key2 = aes.decrypt(key1)

        aes = AES.new(key2, AES.MODE_CBC, iv)
        xml = dlc_file[:-88]
        xml = xml.decode('base64')
        xml = aes.decrypt(xml).decode('base64')

        url_list = textextractall(xml, '<url>', '</url>')
        links = []
        for i in url_list:
            url = i.decode('base64')
            links.append(url)
        log.info(repr(links))









# it looks like i need a cookie
#class Bitshare(Extension, BaseStream):
#    ename = 'Bitshare'
#    eregex = 'http://www.(bitshare).com/files/.*'
#    cookieCache = []
#
#    def get(self, VideoInfo, justId=False, isAvailable=False):
#        print "ASDSADSAD"
#        id = textextract(VideoInfo.stream_url, '/files/', '')
#        if justId:
#            return id




class Streamcloud(Extension, BaseStream):
    ename = 'Streamcloud'
    eregex = '.*streamcloud.*'
    # moved the code to the downloadpart since the links to the videos are only shortly available
    # also you can only download one
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        vId = textextract(link, 'streamcloud.eu/', '/')
        if justId:
            return vId
        self.flvUrl = link
        return self.flvUrl

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")

        link = self.flvUrl
        url = UrlMgr(url=link, nocache=True)
        url.data
        cookieCache = []
        for cookie in url.pointer.cookies: # refresh putlockerCookieCache
            afc = textextract(cookie, 'afc=', '; ')
            if afc:
                afc = 'afc='+afc
                cookieCache = [afc]
                break
        if cookieCache == []:
            log.error('no cookie found for %s' % link)
            return False
        url = UrlMgr(url=link, cookies=cookieCache, nocache=True, keepalive=False)
        self.flvUrl = textextract(url.data, 'file: "', '"')
        if not self.flvUrl:
            log.error('no flvUrl found for %s' % link)
            return False

        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)


class Divxstage(Extension, BaseStream):
    ename = 'divxstage'
    eregex = '.*divxstage.(eu|net).*'
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        vId = textextract(link, 'video/', '')
        if justId:
            return vId
        self.flvUrl = link
        return self.flvUrl

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        link = self.flvUrl
        vId = textextract(link, 'video/', '')
        url = UrlMgr(url=link, nocache=True, keepalive=False)
        filekey = textextract(url.data, 'flashvars.filekey="', '"')
        filekey = filekey.replace('.', '%2E').replace('-', '%2D')

        log.error("divxstage filekey:"+filekey)
        # call a php script to get actual file location
        params = 'codes=1&file='+vId+'&key='+filekey+'&pass=undefined&user=undefined'
        url = UrlMgr(url="http://www.divxstage.eu/api/player.api.php?"+params, nocache=True, keepalive=False);
        # url=http://s11.divxstage.eu/dl/2b0cc77e69d41fd81462e40406a633e0/50c88667/ffa75b62c2de66b491d404874af24780e5.flv&title=genXAnime.orgAIR01v294EBC1BD.avi%26asdasdas&site_url=http://www.divxstage.eu/video/evvdrozntwccu&seekparm=&enablelimit=0
        # needs only till .flv
        self.flvUrl = textextract(url.data, 'url=', '&')

        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)
        # https://github.com/monsieurvideo/get-flash-videos/blob/master/lib/FlashVideo/Site/Divxstage.pm [-]
        # http://www.divxstage.eu/video/ai5dy7djvw1i7 
        # http://www.divxstage.eu/api/player.api.php?key=78%2E53%2E26%2E148%2Dae5f248055fbb345ea25c0e668590561&user=undefined&pass=undefined&file=ai5dy7djvw1i7&codes=1
