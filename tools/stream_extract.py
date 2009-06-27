import time

from url import UrlMgr, LargeDownload
from helper import textextract, textextractall
import defines as defs
import config


def2func = {}
url2defs = {}


def plain_call(x, args):
    return LargeDownload(args)


def void_call(x, args):
    return False
def void(x):
    return False
def2func[0] = void


def megavideo_call(x, args):
    diff = config.megavideo_wait - time.time()
    if diff > 0:
        args['log'].error('megavideo added us to the waitlist, will be released in %d:%d' % (diff / 60, diff % 60))
        # TODO append this pinfo to the end of the download_queue or find another way so that i don't need to restart
        # the program to get those flashfiles
        return False
    args['megavideo'] = True
    return LargeDownload(args)

hex2bin = {'0':'0000','1':'0001','2':'0010','3':'0011','4':'0100','5':'0101','6':'0110','7':'0111','8':'1000','9':'1001','a':'1010','b':'1011',
    'c':'1100','d':'1101','e':'1110','f':'1111'}
bin2hex = dict([(v, k) for (k, v) in hex2bin.iteritems()])
def megavideo(VideoInfo):
        # VideoInfo.stream_url should look like this:
        # http://www.megavideo.com/v/W5JVQYMX or http://www.megavideo.com/v/KES7QC7Ge1a8d728bd01bf9965b2918a458af1dd.6994310346.0
        # the first 8 chars after /v/ are interesting for us, they are the vId
        url = VideoInfo.stream_url
        log = VideoInfo.log

        pos1 = url.find('/v/')
        if pos1 < 0:
            VideoInfo.throw_error('no valid megavideo url %s' % url)
            return False
        pos1 += len('/v/')
        vId = url[pos1:pos1+8]
        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=%s' % vId, 'log': log})
        un = textextract(url.data, ' un="', '"')
        k1 = textextract(url.data, ' k1="', '"')
        k2 = textextract(url.data, ' k2="', '"')
        s  = textextract(url.data, ' s="', '"')
        if( not (un and k1 and k2 and s) ):
            VideoInfo.throw_error("couldnt extract un=%s, k1=%s, k2=%s, s=%s" % (un, k1, k2, s))
            if url.data.find('error="1"') >= 0:
                errormsg = textextract(url.data, 'errortext="', '"></ROW>')
                log.info('megavideo-error with msg: %s' % errormsg)
            return False
        log.info('extract un=%s, k1=%s, k2=%s, s=%s' % (un, k1, k2, s))

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
        return (flv_url, (megavideo_call, ''))
def2func[defs.Stream.MEGAVIDEO] = megavideo
url2defs['megavideo']           = defs.Stream.MEGAVIDEO


def eatlime(VideoInfo):
    url = VideoInfo.stream_url
    log = VideoInfo.log
    url_handle = UrlMgr({'url': url, 'log': log})
    if not url_handle.redirection:
        VideoInfo.throw_error('problem in getting the redirection')
        return False
    # tmp = http://www.eatlime.com/UI/Flash/player_v5.swf?token=999567af2d78883d27d3d6747e7e5e50&type=video&streamer=lighttpd&plugins=topBar,SS,custLoad_plugin2,YuMe_post&file=http://www.eatlime.com/playVideo_3C965A26-11D8-2EE7-91AF-6E8533456F0A/token_999567af2d78883d27d3d6747e7e5e50&duration=1421&zone_id=0&entry_id=0&video_id=195019&video_guid=3C965A26-11D8-2EE7-91AF-6E8533456F0A&fullscreen=true&controlbar=bottom&stretching=uniform&image=http://www.eatlime.com/splash_images/3C965A26-11D8-2EE7-91AF-6E8533456F0A_img.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&displayclick=play&linktarget=_self&link=http://www.eatlime.com/video/HS01/3C965A26-11D8-2EE7-91AF-6E8533456F0A&title=HS01&description=&categories=Sports&keywords=HS01&yume_start_time=1&yume_preroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_preroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_branding_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_branding_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_midroll_playlist=http%3A%2F%2Fpl.yumenetworks.com%2Fdynamic_midroll_playlist.fmil%3Fdomain%3D146rbGgRtDu%26width%3D480%26height%3D360&yume_postroll_
    # http://www.eatlime.com/UI/Flash/eatlime_player.swf?bufferlength=0.1&plugins=videohelper,helloworld&token=6cfc90e3346653b8ab5348e9c19afbc2&streamer=&file=.flv&duration=&zone_id=0&entry_id=0&video_id=&video_guid=176E0E3F-992D-5CCB-1EDF-9B8E33EF91C4&image=.jpg&logo=http://www.eatlime.com/logo_player_overlay.png&linktarget=_self&link=http://www.eatlime.com/video/&title=&description=&categories=Sports&keywords=&video_title=&video_views=0+Views&video_rating=0&video_rate_url=http%3A%2F%2Fdev.eatlime.com%2Findex.php%3Farea%3DmiscCMDS%26cmd%3DaddRating%26media_id%3D%26rate%3D      
    flv_url = textextract(url_handle.redirection, 'file=', '&duration')
    if not flv_url:
        VideoInfo.throw_error('problem in urlextract from: %s' % url_handle.redirection)
        return False
    elif flv_url == '.flv':
        VideoInfo.throw_error('eatlime-videolink is down (dl-file is only .flv): %s' % url_handle.redirection)
        return False
    return (flv_url, (plain_call, ''))
def2func[defs.Stream.EATLIME] = eatlime
url2defs['eatlime']           = defs.Stream.EATLIME


def veoh(VideoInfo):
    url = VideoInfo.stream_url
    log = VideoInfo.log
    permalink = textextract(url, 'permalinkId=', '')
    if not permalink:
        VideoInfo.throw_error('Veoh: problem in extracting permalink')
        VideoInfo.throw_error(url)
        return False
    else:
        # permalink will be extracted until the first occurence of an ampersand (&) or until the end
        a = permalink.find('&')
        if a >= 0:
            permalink = permalink[:a]

    def veoh_try(cache_writeonly):
        # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
        # apikey is constant
        # but this file changes it's content every 24h <- thats why we need to disable the cache sometimes
        link = 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=%s&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36' % permalink
        url = UrlMgr({'url': link, 'log': log, 'cache_writeonly': cache_writeonly})

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
        url = UrlMgr({'url': flv_url, 'log': log})
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
        VideoInfo.throw_error(a[1])
        return False

    flv_url = a[0]
    return (flv_url, (plain_call, 0))
def2func[defs.Stream.VEOH] = veoh
url2defs['veoh.com']       = defs.Stream.VEOH
url2defs['truveoh.com']    = defs.Stream.VEOH


def sevenload(VideoInfo):
    url = VideoInfo.stream_url
    log = VideoInfo.log
    # source: http://de.sevenload.com/pl/uPJq7C8/490x317/swf,play
    # or http://datal3.sevenload.com/data76.sevenload.com/slcom/gk/qi/cksmnmd/xtldnnplemof.flv
    # which is already the full url
    # we need to go to http://flash.sevenload.com/player?itemId=uPJq7C8
    if url.find('slcom/') == -1:
        id = textextract(url, 'pl/', '/')
        log.info(url)
        url = UrlMgr({'url': 'http://flash.sevenload.com/player?itemId=%s' % id, 'log': log})
        if not url.data:
            VideoInfo.throw_error('seven_load: failed to fetch xml')
            return False
        #<location seeking="yes">http://data52.sevenload.com/slcom/qt/jw/echlkg/xztlpgdgghgc.flv</location>
        flv_url = textextract(url.data, '<location seeking="yes">', '</location>')
    else: # we already got the flashurl - but can't check for errors here - in errorcase it will throw a 404 at downloading
        flv_url = url
    return (flv_url, (plain_call, 0))
def2func[defs.Stream.SEVENLOAD] = sevenload
url2defs['sevenload']           = defs.Stream.SEVENLOAD


def hdweb_call(x, args):
    args['http_version'] = '1.0' # else it will start a chunkdownload
    return LargeDownload(args)

def hdweb(VideoInfo): # note: when requesting the flashlink, we need to performa a http1.0 request, else their server will send us chunked encoding
    #url = VideoInfo.stream_url
    url = 'http://hdweb.ru/getvideo'
    post = VideoInfo.stream_post
    log = VideoInfo.log
    if not post:
        VideoInfo.throw_error('no post information for hdweb, something went wrong')
        return False

    log.info('hdweb using url: %s POST: %s' % (url, post))
    url = UrlMgr({'url': url, 'post': post, 'log': log})

    if not url.data:
        VideoInfo.throw_error('hdweb: failed to get data')
        return False
    # xmlresult:
    #  3   <id>6985</id>
    #  4   <title>Kanon 2006 1 [GenX]</title>
    #  5   <ldurl>http://79.173.104.28/04ab97cbe651bdbf000dc471ddf514c01ade2d44cd3fcdef25c4e1fd8221bb7f</ldurl>
    #  6   <hdurl>http://79.173.104.28/5768614b05aa7da5f93cb391ddec5c488b62f86b86171fc58ee022a6c6f77550</hdurl>
    if config.flash_quality == defs.Quality.HIGH:
        flv_url = textextract(url.data, 'hdurl>', '</hdurl')
    else:
        flv_url = textextract(url.data, 'ldurl>', '</ldurl')
    #title = textextract(url.data, 'title>', '</title')
    return (flv_url, (hdweb_call, 0))
def2func[defs.Stream.HDWEB] = hdweb
url2defs['hdweb']           = defs.Stream.HDWEB


def plain(VideoInfo):
    return (VideoInfo.stream_url, (plain_call, 0))
def2func[defs.Stream.PLAIN] = plain
url2defs['.flv']            = defs.Stream.PLAIN
url2defs['.mp4']            = defs.Stream.PLAIN
url2defs['youtube']         = defs.Stream.PLAIN


def imeem(VideoInfo):
    url = VideoInfo.stream_url
    log = VideoInfo.log
    tmp = ['pl', 'v']
    id = None
    for i in tmp:
        id = textextract(url, '/%s/' % i, '/')
        if id:
            break

    API_KEY = 'c61e4e06-3604-421c-bc9d-8cc557c5676c'
    SECRET  = 'f7aa4811-b018-435b-8355-51366087e073'
    JSON_ROOT_URL = 'http://www.api.imeem.com/api/json/'
    API_VERSION = '1.0'

    def generate_sig(method, args = {}):
        import hashlib
        keys = args.keys()
        keys.sort()
        t = [method]
        for a in keys:
            t.append('%s=%s' % (a, args[a]))
        t.append(SECRET)
        return hashlib.md5(''.join(t)).hexdigest()

    def sendGetRequest(method="", args={}):
       args["apiKey"]  = API_KEY
       args["version"] = API_VERSION
       sig = generate_sig(method, args)
       args["sig"] = sig
       query_string = []
       for i in args:
           query_string.append('%s=%s' % (i, args[i]))
       query_string = '&'.join(query_string)

       url = '%s%s?%s' % (JSON_ROOT_URL, method, query_string)
       url_handle = UrlMgr({'url': url, 'log': log, 'cache_writeonly': True})
       return url_handle.data

    def mediaGetStreamInfo(key):
        import urllib
        key = urllib.quote(key)
        method = 'mediaGetStreamInfo'
        data = {'forceSample': 'false', 'isEmbed': 'false', 'isFeatured': 'false', 'key': key, 'methodVersion': '2', 'referrer': 'web', 'supportsHD': 'false'}

        #result = {"statusCode":"0","statusDescription":"Success","statusDetails":"","playMode":0,"isVideo":True,"ep":"8d5MASLSHBsHF22fvJ7lyF8JfYBdWlNdq+AjnpeSAkdmJHYI+R6Bj4Z+0aX0y5+N9yh+1xISgtg4CETFeOczC3XC/hIr+K9YoxvL1AA2Alv7Yx/hxZKUt3du9wRXSW2gHLiXVSi5Sp80zTOb7ohHeA\u003d\u003d","h":"srv0105-01.sjc3.imeem.com","p":"/g/v/30472442b39d2d1f0099979dd2cf460f.flv","v":1}
        result = sendGetRequest(method, data)
        p  = textextract(result, '"p":"', '"')
        ep = textextract(result, '"ep":"', '"')
        v  = textextract(result, '"v":', '}')
        h  = textextract(result, '"h":"', '"')
        return {'p': p, 'ep': ep, 'v': v, 'h': h}

    urls = mediaGetStreamInfo(id)

    salt = '92874029'
    M = '{"p":"%s","ep":"%s","v":"%s","s":"%s"}' % (urls['p'], urls['ep'], urls['v'], salt)
    swf_key = 'I:NTnd7;+)WK?[:@S2ov'
    import imeem_crypt as crypt
    x = crypt.encrypt(M)
    url = 'http://%s/G/3/%s.flv' % (urls['h'], x)
    return (url, (plain_call, 0))
def2func[defs.Stream.IMEEM] = imeem
url2defs['imeem']           = defs.Stream.IMEEM


def zeec(VideoInfo):
    url = VideoInfo.stream_url
    log = VideoInfo.log
    url = UrlMgr({'url': url, 'log': log})
    link = textextract(url.data, 'var xml = \'', '\';')
    # now we get a xml-file with much information (reminds me a bit to the voeh-xml)
    url = UrlMgr({'url': link, 'log': log})
    # 72       <property name="src"
    # 73                 value="http://ugc04.zeec.de/v/flv1/0x0/9229/99229_yq54tkgU4OVUgDEsxJFUEKMeKoe9YZFA.flv"/>
    # 74       <property name="hd_src"
    # 75                 value="http://ugc02.zeec.de/v/ipod/640x480/9229/99229_yq54tkgU4OVUgDEsxJFUEKMeKoe9YZFA.mp4"/>
    if config.flash_quality == defs.Quality.HIGH:
        x = url.data.find('name="hd_src"')
    else:
        x = url.data.find('name="src"')
    flv_url, x = textextract(url.data, 'value="', '"', x)
    return (flv_url, (plain_call, 0))
def2func[defs.Stream.ZEEC] = zeec
url2defs['zeec']           = defs.Stream.ZEEC


def xvid_call(x, args):
    args['referer'] = x
    args['reconnect_wait'] = 2 # xvid downloads (very) often close the connection, thats why this is handled a bit special here
    args['retries'] = 30 # after one minute, we can assume that they won't send us anything
    return LargeDownload(args)
def xvid(VideoInfo):
    # 1. http://hdivx.to/?Module=Details&HashID=FILE4A344C620E2CB
    # 2. http://hdivx.to/Get/?System=Play&Hash=FILE4A344C620E2CB
    # redirects to http://divx0.hdivx.to/00002000/062499466a985489952d7e3737805328
    # it's important that we send the referer in the last link too
    url = VideoInfo.stream_url
    log = VideoInfo.log
    if url.find('HashID') != -1:
        hash = textextract(url, 'HashID=', '')
        host = url[:url.find('/', 10)]
        link2 = host + '/' + 'Get/?System=Play&Hash=' + hash
        url = UrlMgr({'url': link2, 'log': log})
        flv_url = url.get_redirection()
    else:
        link2 = url
        url_handle = UrlMgr({'url': url, 'log': log})
        x = url_handle.data.find('object classid')
        flv_url, j = textextract(url_handle.data, 'param name="src" value="', '"', x)
    return (flv_url, (xvid_call, link2))
def2func[defs.Stream.XVID] = xvid
url2defs['hdivx.to'] = url2defs['archiv.to'] = url2defs['divxhost.to'] = url2defs['festplatte.to']  = defs.Stream.XVID
url2defs['freeload.to'] = defs.Stream.XVID
url2defs['filebase.to'] = defs.Stream.XVID
url2defs['clickandload.net'] = defs.Stream.XVID
# url2defs['duckload.com'] xvid, but first we need to fill in a captcha :-/


def ccf_call(x, args):
    args['log'].warning(repr(args))
    return LargeDownload(args)

def ccf_decrypt(ciphertext):
    # this code could only be written through the already existing implementation in jdownloader
    from Crypto.Cipher import AES
    key = 'so5sxNsPKfNSDDZHayr32520'
    cipher = []
    # transform the ciphertext, which is written with hex-ints into a string (needed for aes-module)
    for i in xrange(0, len(ciphertext), 2):
        cipher.append(chr(int(ciphertext[i:i+2], 16)))
    cipher = ''.join(cipher)

    aes = AES.new(key)
    AES.key_size = 6
    ret = []
    # just decrypts the blocks (size=16) from the cipher
    ciphlen = len(cipher)
    for q in xrange(0, ciphlen, 16):
        ret.append(aes.decrypt(cipher[q:q+16]))

    # now search in the last ret for unneeded symbols (this is in the aes-design that a string gets filled up with unneeded chars if its to short)
    lastret = len(ret) - 1
    x = ret[lastret].find('\x00')
    if x != -1:
        ret[lastret] = ret[lastret][:x]
    # and join our chunks
    return ''.join(ret)

def ccf(VideoInfo):
    # this code could only be written through the already existing implementation in jdownloader
    # big thanks to the team
    url = VideoInfo.stream_url
    log = VideoInfo.log

    x = url.rfind('/')
    folder = url[x+1:]

    url_handle = UrlMgr({'url': 'http://crypt-it.com/c/' + folder, 'log': log})
    info = url_handle.data
    packagename = textextract(info, 'class="folder">', '</')
    password = textextract(info, '<b>Password:</b> ', '\t')

    bs = '\x00\x00\x00\x00\x00\x01\x00\x11cryptit2.getFiles\x00\x02/1\x00\x00\x00\x11\n\x00\x00\x00\x02\x02\x00\x06'
    b2s = '\x02\x00'
    pw = '' # TODO implement support for passwords
    if len(pw) == 0:
        pw_len = '\x00'
    post = bs + folder + b2s + pw_len + pw;
    url_handle = UrlMgr({'url': 'http://crypt-it.com/engine/', 'post': post, 'content_type': 'application/x-amf', 'log': log})
    ccf = url_handle.data

    info = textextractall(ccf, 'id', 'clicks') # notice: we wont get the information about the last click (but uninterasting anyway)
    log.info('package "%s" with password "%s"' % (packagename, password))
    flv_urls = []
    for file in info:
        # '\x02\x00\x071168089\x00\x06folder\x02\x00\x068CDJD8\x00\x04file\x02\x00,E01_-_600_Milliarden_Double_Dollar.part1.rar\x00\x03url\x02\x00\xc019cc85         884959252328c86b465ca02e8fb3ca80571666496e3849c6d288313c84251cc80432ad0477a0496fe2eb040d7236cf60aa3f9418d6fa6ffe65b698746bc6239a128629a1faf99ae54d71d5986182685f953dc66'
        url = textextract(file, 'url\x02\x00\xc0', '\x00')
        name = textextract(file, 'file\x92\00,', '\x00')
        url = ccf_decrypt(url)
        flv_urls.append(url)
        log.info(url)
    return (flv_urls, (ccf_call, ''))

url2defs['crypt-it.com'] = defs.Stream.CCF
def2func[defs.Stream.CCF] = ccf
