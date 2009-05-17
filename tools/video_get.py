from tools.url import UrlMgr
from tools.helper import normalize_title, textextract

TYPE_NONE         = 0
# H for homepage
TYPE_H_ANIMELOADS = 1
TYPE_H_ANIMEKIWI  = 2
TYPE_H_ANIMEJUNKIES = 3

# S for stream
TYPE_S_VEOH       = 1
TYPE_S_EATLIME    = 2
TYPE_S_MEGAVIDEO  = 3
TYPE_S_HDWEB      = 4
TYPE_S_SEVENLOAD  = 5
TYPE_S_MYSPACECDN = 6
TYPE_S_IMEEM      = 7


class VideoInfo(object):
    def init__(self, url, log):
        self.error = False
        self.url = url
        self.log = log
        self.url_handle = UrlMgr({'url': self.url, 'log': self.log})

    def throw_error(self, str):
        self.log.error(str + " " + self.url)
        self.error = True
        self.error_msg = (str + " " + self.url)
        return

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h' + str(hash(self.url))

    def get_name__(self, name):
        if not name:
            self.name = hash(self)
            self.log.info('couldnt extract name - will now use hash: ' + self.name)
        else:
            self.name = normalize_title(name)
        return self.name

    def get_title__(self, title):
        if not title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            self.log.info('couldnt extract title - will now use the hash from this url: ' + self.title)
        else:
            self.title = normalize_title(title)
        return self.title

    def get_subdir__(self, dir):
        import os
        import config
        dir2 = os.path.join(config.flash_dir, dir)
        if os.path.isdir(dir2) is False:
            try:
                os.makedirs(dir2)
            except:
                self.throw_error('couldn\'t create subdir in ' + dir2)
                dir = ''
        self.subdir = dir
        return self.subdir

    def get_stream__(self, args):
        self.stream_url = args['url']
        if 'post' in args:
            self.stream_post = args['post']
        else:
            self.stream_post = None
        self.stream_type = TYPE_NONE
        if self.stream_url:
            if self.stream_url.find('veoh.com') > 0 or self.stream_url.find('trueveo.com') > 0:
                self.stream_type = TYPE_S_VEOH
            elif self.stream_url.find('megavideo') > 0:
                self.stream_type = TYPE_S_MEGAVIDEO
            elif self.stream_url.find('eatlime') > 0:
                self.stream_type = TYPE_S_EATLIME
            elif self.stream_url.find('hdweb') > 0:
                self.stream_type = TYPE_S_HDWEB
            elif self.stream_url.find('sevenload') > 0:
                self.stream_type = TYPE_S_SEVENLOAD
            elif self.stream_url.find('myspacecdn') > 0:
                self.stream_type = TYPE_S_MYSPACECDN
            elif self.stream_url.find('imeem') > 0:
                self.stream_type = TYPE_S_IMEEM
            else:
                self.throw_error('couldn\'t find a supported streamlink from:' + self.stream_url)
        else:
            self.throw_error('couldn\'t find a streamlink inside this url')
        return self.stream_url

    def get_flv__(self):
        if self.stream_type == TYPE_S_EATLIME:
            tmp = eatlime(self)
        elif self.stream_type == TYPE_S_VEOH:
            tmp = veoh(self)
        elif self.stream_type == TYPE_S_MEGAVIDEO:
            tmp = megavideo(self)
        elif self.stream_type == TYPE_S_HDWEB:
            tmp = hdweb(self)
        elif self.stream_type == TYPE_S_SEVENLOAD:
            tmp = sevenload(self)
        elif self.stream_type == TYPE_S_MYSPACECDN:
            tmp = myspacecdn(self)
        elif self.stream_type == TYPE_S_IMEEM:
            tmp = imeem(self)

        if tmp:
            self.flv_url  = tmp[0]
            self.flv_size = tmp[1]
        else:
            # throw_error was already called in the functions above, so just set the variables here
            self.flv_url  = ''
            self.flv_size = 0
        return self.flv_url

    def __getattr__(self, key):
        if self.error:
            return None
        if key == 'title':
            return self.get_title__(self.get_title())
        elif(key == 'name'):
            return self.get_name__(self.get_name())
        elif key == 'subdir':
            return self.get_subdir__(self.get_subdir())
        elif(key == 'stream_url'):
            return self.get_stream__(self.get_stream())
        elif(key == 'stream_type'):
            self.get_stream__(self.get_stream())
            return self.stream_type
        elif(key == 'flv_url'):
            return self.get_flv__()
        elif(key == 'flv_size'):
            self.get_flv__()
            return self.size


class AnimeJunkies(VideoInfo):
    def __init__(self, url, log):
        self.homepage_type = TYPE_H_ANIMEJUNKIES
        self.init__(url, log) # call baseclass init

    def get_title(self):
        return 'TITLE IS IMPLEMENTED SOMEWHERE ELSE'

    def get_name(self):
        return textextract(self.url_handle.data, 'full_oben Uberschrift">','</div>')

    def get_subdir(self):
        return self.name

    def get_stream(self):
        url = textextract(self.url_handle.data, '<param name="movie" value="','"')
        post = textextract(self.url_handle.data, 'value="domain=hdweb.ru&', '&mode')
        if not url:
            url = textextract(self.url_handle.data, 'org&file=', '&')
            if not url:
                url = textextract(self.url_handle.data, '<embed src="', '"')
        return {'url':url, 'post':post}


class AnimeKiwi(VideoInfo):
    def __init__(self, url, log):
        self.homepage_type = TYPE_H_ANIMEKIWI
        self.init__(url, log) # call baseclass init

    def get_title(self):
        return textextract(self.url_handle.data, '<title>',' |')

    def get_subdir(self):
        return textextract(self.url, 'watch/','-episode').replace('-','_')

    def get_stream(self):
        return {'url': textextract(self.url_handle.data,'<param name="movie" value="','"')}


class AnimeLoads(VideoInfo):
    def __init__(self, url, log):
        self.homepage_type = TYPE_H_ANIMELOADS
        self.init__(url, log) # call baseclass init

    def get_title(self):
        return textextract(self.url_handle.data, '<span class="tag-0">','</span>')

    def get_subdir(self):
        return textextract(self.url, 'streams/','/')

    def get_stream(self):
        link = textextract(self.url_handle.data,'<param name="movie" value="','"')
        if not link:
            link = textextract(self.url_handle.data,'<embed src="', '"')
        return {'url': link}


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
        url = UrlMgr({'url': 'http://www.megavideo.com/xml/videolink.php?v=' + vId, 'log': log})
        un =textextract(url.data,' un="','"')
        k1 =textextract(url.data,' k1="','"')
        k2 =textextract(url.data,' k2="','"')
        s  =textextract(url.data,' s="','"')
        if( not ( un and k1 and k2 and s) ):
            VideoInfo.throw_error("couldnt extract un=%s, k1=%s, k2=%s, s=%s"%(un, k1, k2, s))
            return False
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
        tmp = []
        bin = ''.join(bin)
        for i in xrange(0,128/4):
            tmp.append(bin2hex[bin[i * 4:(i + 1) * 4]])
        hex = ''.join(tmp)
        size = 0
        #size = int(textextract(url.data,'size="','"')) # i think this size is wrong
        flv_url = 'http://www' + s + '.megavideo.com/files/' + hex + '/'
        return (flv_url, size)


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
        VideoInfo.throw_error('problem in urlextract from: ' + url_handle.redirection)
        return False
    elif flv_url == '.flv':
        VideoInfo.throw_error('eatlime-videolink is down (dl-file is only .flv): ' + url_handle.redirection)
        return False
    size = 0
    return (flv_url, size)


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
    url = UrlMgr({'url': 'http://www.veoh.com/rest/v2/execute.xml?method=veoh.search.search' +
                        '&type=video&maxResults=1&permalink=' + permalink + '&contentRatingId=3' +
                        '&apiKey=5697781E-1C60-663B-FFD8-9B49D2B56D36', 'log': log})
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
        url = UrlMgr({'url': 'http://flash.sevenload.com/player?itemId=' + id, 'log': log})
        if not url.data:
            VideoInfo.throw_error('seven_load: failed to fetch xml')
            return False
        #<location seeking="yes">http://data52.sevenload.com/slcom/qt/jw/echlkg/xztlpgdgghgc.flv</location>
        flv_url = textextract(url.data, '<location seeking="yes">', '</location>')
    else: # we already got the flashurl - but can't check for errors here - in errorcase it will throw a 404 at downloading
        flv_url = url
    size = 0
    return (flv_url, size)


def hdweb(VideoInfo): # note: when requesting the flashlink, we need to performa a http1.0 request, else their server will send us chunked encoding
    #url = VideoInfo.stream_url
    url = 'http://hdweb.ru/getvideo'
    post = VideoInfo.stream_post
    log = VideoInfo.log
    if not post:
        VideoInfo.throw_error('no post information for hdweb, something went wrong')
        return False

    log.info('hdweb using url:' + url + ' POST: ' + post)
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


def myspacecdn(VideoInfo):
    url = VideoInfo.stream_url
    return (url, 0)


c = None
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
            t.append(a + "=" + args[a])
        stringToHash = ''.join(t)
        sig = hashlib.md5(method + stringToHash + SECRET).hexdigest()
        return sig

    def sendGetRequest(method="", args={}):
       args["apiKey"]  = API_KEY
       args["version"] = API_VERSION
       sig = generate_sig(method, args)
       args["sig"] = sig
       import urllib2
       query_string = '&'.join(k + '=' + urllib2.quote(v) for k, v in args.items())
       url = JSON_ROOT_URL + method + "?" + query_string
       u = urllib2.urlopen(urllib2.Request(url))
       return u.read()

    def mediaGetStreamInfo(key):
        method = "mediaGetStreamInfo"
        data={"forceSample":"false", "isEmbed":"false", "isFeatured":"false", "key":key, "methodVersion":"2", "referrer":"web", "supportsHD":"false"}
        #result = {"statusCode":"0","statusDescription":"Success","statusDetails":"","playMode":0,"isVideo":True,"ep":"8d5MASLSHBsHF22fvJ7lyF8JfYBdWlNdq+AjnpeSAkdmJHYI+R6Bj4Z+0aX0y5+N9yh+1xISgtg4CETFeOczC3XC/hIr+K9YoxvL1AA2Alv7Yx/hxZKUt3du9wRXSW2gHLiXVSi5Sp80zTOb7ohHeA\u003d\u003d","h":"srv0105-01.sjc3.imeem.com","p":"/g/v/30472442b39d2d1f0099979dd2cf460f.flv","v":1}
        result = sendGetRequest(method, data)
        p  = textextract(result, '"p":"', '"')
        ep = textextract(result, '"ep":"', '"')
        v  = textextract(result, '"v":', '}')
        h  = textextract(result, '"h":"', '"')
        return {'p': p, 'ep': ep, 'v': v, 'h': h}

    import tools.imeem_crypt as crypt
    urls = mediaGetStreamInfo(id)

    salt = '92874029'
    if not c:
        c = crypt.Crypt(log)
    M = '{"p":"' + urls["p"] + '","ep":"' + urls["ep"] + '","v":"' + urls["v"] + '","s":"' + salt + '"}'
    swf_key = "I:NTnd7;+)WK?[:@S2ov"
    x = c.encrypt(M)
    url = 'http://' + urls['h'] + '/G/3/' + x + '.flv'
    return (url, 0)
