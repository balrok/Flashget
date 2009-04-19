from tools.url import UrlMgr
from tools.helper import normalize_title, textextract

# H for homepage
TYPE_H_ANIMELOADS = 1
TYPE_H_ANIMEKIWI  = 2

# S for stream
TYPE_S_VEOH       = 1
TYPE_S_EATLIME    = 2
TYPE_S_MEGAVIDEO  = 3


class ClassError(object):
    def __getattr__(self,key):
        if key == 'error':
            self.error  = False
            return self.error

    def throw_error(self, str):
        self.log.error(str + " " + self.url)
        self.error = True
        self.error_msg = (str + " " + self.url)
        return


class VideoInfo(ClassError):
    def init__(self, url, log):
        self.url = url
        self.log = log
        self.url_handle = UrlMgr({'url': self.url, 'log': self.log})

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h' + str(hash(self.url))

    def get_title__(self, title):
        if not title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            self.log.info('couldnt extract title - will now use the hash from this url: ' + self.title)
        else:
            self.title = normalize_title(title)

    def get_subdir__(self, dir):
        dir2 = os.path.join(config.flash_dir, dir)
        try:
            os.makedirs(dir2)
        except:
            self.throw_error('couldn\'t create subdir in' + dir2)
            dir = ''
        self.subdir = dir
        return self.subdir

    def get_stream__(self, link):
        self.flv_url = link
        if link:
            if link.find('veoh.com') > 0:
                self.stream_type = TYPE_S_VEOH
            elif link.find('megavideo') > 0:
                self.stream_type = TYPE_S_MEGAVIDEO
            elif link.find('eatlime') > 0:
                self.stream_type = TYPE_S_EATLIME
            else:
                self.throw_error('couldn\'t find a supported streamlink from:' + link)
        else:
            self.throw_error('couldn\'t find a streamlink inside this url')
        return self.flv_url

    def __getattr__(self, key):
        if key == 'title':
            return self.get_title__(self.get_title())
        elif key == 'subdir':
            return self.get_subdir__(self.get_subdir())
        elif(key == 'stream_type' or key == 'flv_url'):
            return self.get_stream__(self.get_stream())


class AnimeKiwi(VideoInfo):
    def __init__(self, url, log):
        self.homepage_type = TYPE_H_ANIMEKIWI
        self.init__(url, log) # call baseclass init

    def get_title(self):
        return textextract(self.url_handle.data, '<title>',' |')

    def get_subdir(self):
        return textextract(self.url, 'watch/','-episode').replace('-','_')

    def get_stream(self):
        return textextract(self.url_handle.data,'<param name="movie" value="','"')


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
        return link


class MegaVideo(ClassError):
    def __init__(self, url, log):
        self.url = url #http://www.megavideo.com/v/W5JVQYMX or http://www.megavideo.com/v/KES7QC7Ge1a8d728bd01bf9965b2918a458af1dd.6994310346.0
                       # the first 8 chars after /v/

        self.log = log
        pos1 = url.find('/v/')
        if pos1 < 0:
            self.throw_error('no valid megavideo url')
            return
        pos1 += len('/v/')
        vId = url[pos1:pos1+8]
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
        self.log.info("extract un=%s, k1=%s, k2=%s, s=%s"%(un, k1, k2, s))
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


class EatLime(ClassError):
    def __init__(self, url, log):
        self.size = 0
        self.url = url
        self.log = log
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


class Veoh(ClassError):
    def __init__(self, url, log):
        self.size = 0
        self.url = url
        self.log = log
        permalink = textextract(self.url, '&permalinkId=', '&id=')
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


