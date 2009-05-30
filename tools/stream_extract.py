from tools.url import UrlMgr
from tools.helper import textextract
import tools.defines as defs


def2func = {}
url2defs = {}


hex2bin={'0':'0000','1':'0001','2':'0010','3':'0011','4':'0100','5':'0101','6':'0110','7':'0111','8':'1000','9':'1001','a':'1010','b':'1011',
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
            VideoInfo.throw_error('no valid megavideo url')
            return False
        pos1 += len('/v/')
        vId = url[pos1:pos1+8]
        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=%s' % vId, 'log': log})
        un =textextract(url.data,' un="','"')
        k1 =textextract(url.data,' k1="','"')
        k2 =textextract(url.data,' k2="','"')
        s  =textextract(url.data,' s="','"')
        if( not ( un and k1 and k2 and s) ):
            VideoInfo.throw_error("couldnt extract un=%s, k1=%s, k2=%s, s=%s" % (un, k1, k2, s))
            return False
        log.info('extract un=%s, k1=%s, k2=%s, s=%s' % (un, k1, k2, s))
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
            bin[i] = str(int(bin[i]) ^ int(key[i + 256]) & 1)

        # 5. Convert binary string back to hexadecimal
        tmp = []
        bin = ''.join(bin)
        for i in xrange(0,128/4):
            tmp.append(bin2hex[bin[i * 4:(i + 1) * 4]])
        hex = ''.join(tmp)
        size = 0
        #size = int(textextract(url.data,'size="','"')) # i think this size is wrong
        flv_url = 'http://www%s.megavideo.com/files/%s/' % (s, hex)
        return (flv_url, size)
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
    flv_url = textextract(url_handle.redirection, 'file=',"&duration")
    if not flv_url:
        VideoInfo.throw_error('problem in urlextract from: %s' % url_handle.redirection)
        return False
    elif flv_url == '.flv':
        VideoInfo.throw_error('eatlime-videolink is down (dl-file is only .flv): %s' % url_handle.redirection)
        return False
    size = 0
    return (flv_url, size)
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

    # we need this file: http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=v832040cHGxXkCJ&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36
    # apikey is constant
    url = UrlMgr({'url':
    'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search&type=video&maxResults=1&permalink=%s&contentRatingId=3&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36' % permalink, 'log': log})
    if not url.data:
        VideoInfo.throw_error('Veoh: failed to get data')
        return False
    # from data we get the link:
    # http://content.veoh.com/flash/p/2/v832040cHGxXkCJ/002878c1815d34f2ae8c51f06d8f63e87ec179d0.fll?ct=3295b39637ac9bb01331e02fd7d237f67e3df7e112f7452a
    flv_url = textextract(url.data, 'fullPreviewHashPath="','"')
    # size   = int(textextract(data,'size="','"')) seems to be wrong 608206848 for a 69506379 video

    # if we get the redirection from this url, i think we can manipulate the amount of buffering, but currently i don't need this
    if not flv_url:
        if textextract(url.data, 'items="', '"') == '0':
            VideoInfo.throw_error('Veoh: this video is down by veoh')
        VideoInfo.throw_error('Veoh: failed to get the url from data')
        return False
    size = 0
    return (flv_url, size)
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
    size = 0
    return (flv_url, size)
def2func[defs.Stream.SEVENLOAD] = sevenload
url2defs['sevenload']           = defs.Stream.SEVENLOAD


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
    flv_url = textextract(url.data, 'ldurl>', '</ldurl')
    size = 0
    #title = textextract(url.data, 'title>', '</title')
    return (flv_url, size)
def2func[defs.Stream.HDWEB] = hdweb
url2defs['hdweb']           = defs.Stream.HDWEB


def plain(VideoInfo):
    return (VideoInfo.stream_url, 0)
def2func[defs.Stream.PLAIN] = plain
url2defs['.flv']           = defs.Stream.PLAIN
url2defs['.mp4']           = defs.Stream.PLAIN
url2defs['youtube']           = defs.Stream.PLAIN


def imeem(VideoInfo):
    global c
    url = VideoInfo.stream_url
    log = VideoInfo.log
    id = textextract(url, '/pl/', '/')

    API_KEY="c61e4e06-3604-421c-bc9d-8cc557c5676c"
    SECRET="f7aa4811-b018-435b-8355-51366087e073"
    JSON_ROOT_URL="http://www.api.imeem.com/api/json/"
    API_VERSION="1.0"

    def generate_sig(method="", args={}):
        import hashlib
        keys = args.keys()
        keys.sort()
        t = []
        for a in keys:
            t.append('%s=%s' % (a, args[a]))
        stringToHash = ''.join(t)
        sig = hashlib.md5(method + stringToHash + SECRET).hexdigest()
        return sig

    def sendGetRequest(method="", args={}):
       args["apiKey"]  = API_KEY
       args["version"] = API_VERSION
       sig = generate_sig(method, args)
       args["sig"] = sig
       import urllib2
       query_string = '&'.join('%s=%s' % (k, (urllib2.quote(v) for k, v in args.items())))
       url = '%s%s?%s' % (JSON_ROOT_URL, method, query_string)
       u = urllib2.urlopen(urllib2.Request(url))
       return u.read()

    def mediaGetStreamInfo(key):
        method = 'mediaGetStreamInfo'
        data={'forceSample': 'false', 'isEmbed': 'false', 'isFeatured': 'false', 'key': key, 'methodVersion': '2', 'referrer': 'web', 'supportsHD': 'false'}
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
    import tools.imeem_crypt as crypt
    x = crypt.encrypt(M)
    url = 'http://%s/G/3/%s.flv' % (urls['h'], x)
    return (url, 0)
def2func[defs.Stream.IMEEM] = imeem
url2defs['imeem']           = defs.Stream.IMEEM


#def you_tube(VideoInfo):  == plain()
    # we will follow a referer and then the result can look like this.. but i see no need, to follow the referer inside this function
    # http://v17.lscache1.googlevideo.com/videoplayback?ip=0.0.0.0&sparams=id%2Cexpire%2Cip%2Cipbits%2Citag&itag=34&ipbits=0&sver=3&expire=1243432800&key=yt1&signature=A79908F6E2FA589EFAFF4D7C207373C58FEE1B6B.0105A15AFAA2C2E9930E9C53BC3BD715EB67204A&id=38eaac7cfaec1515
#    url = VideoInfo.stream_url
#    return (url, 0)
