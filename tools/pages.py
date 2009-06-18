# -*- coding: utf-8 -*-

from tools.url import UrlMgr
from tools.helper import *
import tools.defines as defs
import config
from tools.stream_extract import *


class VideoInfo(object):

    def init__(self, url, log):
        self.url = url
        self.log = log
        self.stream_post = None
        self.url_handle = UrlMgr({'url': self.url, 'log': self.log})

    def throw_error(self, str):
        self.log.error('%s %s' % (str, self.url))
        return

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.url)

    def get_name__(self, name):
        if not name:
            self.name = self.__hash__()
            self.log.info('couldnt extract name - will now use hash: %s' % self.name)
        else:
            self.name = normalize_title(name)
        return self.name

    def get_title__(self, title):
        if not title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            self.log.info('couldnt extract title - will now use the hash from this url: %s' % self.title)
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
                self.throw_error('couldn\'t create subdir in %s' % dir2)
                dir = ''
        self.subdir = dir
        return self.subdir

    def get_stream__(self, args):
        self.stream_url = args['url']
        if 'post' in args:
            self.stream_post = args['post']
        self.stream_type = defs.Stream.NONE
        if not self.stream_url:
            self.throw_error('couldn\'t find a streamlink inside this url')
            return None
        for i in url2defs:
            if self.stream_url.find(i) > 0:
                self.stream_type = url2defs[i]
                break
        else:
            self.throw_error('couldn\'t find a supported streamlink in: %s' % self.stream_url)
        return self.stream_url

    def get_flv__(self):
        ret = def2func[self.stream_type](self)
        if not ret:
            ret = (None, (None, None))
        self.flv_url, self.flv_call = ret
        return self.flv_url

    def __getattr__(self, key):
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
        elif(key == 'flv_call'):
            self.get_flv__()
            return self.flv_call


def extract_stream(data):
    ''' extracts the streamlink from specified data '''
    url = ''
    post = textextract(data, 'value="domain=hdweb.ru&', '&mode') # TODO: i think we can extract this from the url
    if post:
        return {'url': 'http://hdweb.ru', 'post': post}
    url = textextract(data, '<embed src="', '"')
    if url:
        return {'url': url}
    url = textextract(data, '<embed src=\'', '\'')
    if url:
        return {'url': url}
    url = textextract(data, '<param name="movie" value="','"')
    if url:
        return {'url': url}
    url = textextract(data, '<param name=\'movie\' value=\'','\'')
    if url:
        return {'url': url}
    return {'url': url}


class KinoToStream(VideoInfo):
    homepage_type = defs.Homepage.KINOTO
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init
        self.cookies = parent.cookies
        self.url_handle.cookies = self.cookies # append the cookies to the initialized urlhandle
        self.log.warning(url)

    def get_title(self):
        return textextract(self.url_handle.data, '<title>Kino.to - ', '</title>')

    def get_name(self):
        return 'kino.to'

    def get_subdir(self):
        return self.name

    def get_stream(self):
        # LoadModule('Entry', '34006', '')
        modparams = textextract(self.url_handle.data, 'LoadModule(\'Entry\', ', '\')')
        #open('asd','w').write(self.url_handle.data)
        if not modparams:
            self.throw_error('failed to get videoid')
            return {'url': None}
        param1, x = textextract(modparams, '', '\'', 1)
        param2 = modparams[x+4:]
        post = 'Request=LoadModule&Name=Entry&Param1=%s&Param2=%s&Data=KO' % (param1, param2)
        # 'Request=LoadModule&Name=Entry&Param1=XXX&Param2=XXX&Data=KO'
        url = 'http://kino.to/res/php/Ajax.php'
        url = UrlMgr({'url': url, 'post': post, 'log': self.log, 'cookies': self.cookies})
        # data has very much interesting information (descriptive text,rating...), but currently we will only extract the flv-link
        link = textextract(url.data, '"Window":"', '}}}')
        link = link.replace('\\', '')
        ret = extract_stream(link)
        if not ret['url']:
            link = textextract(url.data, '"PlayerURL":"', '"')
            link = link.replace('\\', '')
            ret['url'] = link
        return ret


class YouTubeStream(VideoInfo):
    homepage_type = defs.Homepage.YOUTUBE
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        # <title>YouTube - Georg Kreisler - Taubenvergiften</title>
        return textextract(self.url_handle.data, 'title>YouTube - ', '</title')

    def get_name(self):
        return 'youtube'

    def get_subdir(self):
        return self.name

    def get_stream(self):
        # var swfArgs = {"q": "georg%20kreisler", "fexp": "900026,900018", "enablecsi": "1", "vq": null, "sourceid": "ys", "video_id": "OOqsfPrsFRU", "l": 158, "sk": "9mEvI6FCZGm3kxjitpsWLfuA3pd2ny8fC", "fmt_map": "18/512000/9/0/115,34/0/9/0/115,5/0/7/0/0", "usef": 0, "t": "vjVQa1PpcFPD0-luSj0ipQrNGlifdaiKTqla87p4l6s=", "hl": "de", "plid": "AARq38-sU-qXE4Bx", "keywords": "Georg%2CKreisler%2CTaubenvergiften%2CSatire%2Cim%2CPark%2CMusic%2CPiano%2CKlavier%2CSchwarzer%2CHumor%2C%C3%96sterreich%2CLied%2CKabarett%2CKult", "cr": "DE"};
        # l seems to be the playlength
        swfargs = textextract(self.url_handle.data, 'var swfArgs', '};')
        # from youtube-dl: (mobj.group(1) is "t"
        # video_real_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&el=detailpage&ps=' % (video_id, mobj.group(1))
        video_id = textextract(swfargs, '"video_id": "', '"')
        t = textextract(swfargs, '"t": "', '"')
        url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&el=detailpage&ps=' % (video_id, t)
        return {'url':url}


class AnimeJunkiesStream(VideoInfo):
    homepage_type = defs.Homepage.ANIMEJUNKIES
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        return 'TITLE IS IMPLEMENTED SOMEWHERE ELSE'

    def get_name(self):
        return textextract(self.url_handle.data, 'full_oben Uberschrift">','</div>')

    def get_subdir(self):
        return self.name

    def get_stream(self):
        info = {}
        info['url'] = textextract(self.url_handle.data, 'junkies.org&file=', '&')
        if not info['url']:
            info = extract_stream(self.url_handle.data)
        if not info['url']:
            info['url'] = textextract(self.url_handle.data, '<script type="text/javascript" charset="utf-8" src="', '"')
        return info


class AnimeKiwiStream(VideoInfo):
    homepage_type = defs.Homepage.ANIMEKIWI
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        return textextract(self.url_handle.data, '<title>',' |')

    def get_subdir(self):
        return textextract(self.url, 'watch/','-episode').replace('-','_')

    def get_stream(self):
        return extract_stream(self.url_handle.data)


class AnimeLoadsStream(VideoInfo):
    homepage_type = defs.Homepage.ANIMELOADS
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        title = textextract(self.url_handle.data, '<span class="tag-0">','</span>')
        if not title: # putfile we could extract <title></title> but putfile is down
            if self.url_handle.data.find('putfile') >= 0:
                return 'Putfile-Video is down'
            else:
                self.log.error('couldn\'t extract video-title from %s - program will crash :)' % self.url_handle.url)
        return remove_html(title.decode('iso-8859-1'))

    def get_name(self):
        return textextract(self.url, 'streams/','/')

    def get_subdir(self):
        return self.name

    def get_stream(self):
        x = self.url_handle.data.find('id="download"')
        stream = extract_stream(self.url_handle.data[x+50:])
        # for some videos this happened and resulted in bad requests it's possible to implement this check generic, but currently it's only for animeloads
        if stream and stream['url']:
            if stream['url'].endswith('\r\n'):
                stream['url'] = stream['url'][:-2]
        else:
            if self.url_handle.data.find('putfile') >= 0:
                self.log.warning('this was a putfile-stream which doesnt work anymore')
        return stream


class VideoContainer(object):
    def __init__(self, name = ''):
        self.name = name # the name of the videocontainer (name of a serie, or name of a movie)
        self.list = []   # contains list of videos


class Pages(object):
    TYPE_UNK    = 0
    TYPE_MULTI  = 1
    TYPE_SINGLE = 2

    def pages_init__(self, log):
        self.video_container = []
        self.log = log
        self.tmp             = {}

    def name_handle(self, i, pinfo):
        ''' i == index in links-list, pinfo == pinfo from current url in links-list '''
        return

    def add_streams(self, links):
        list = []
        ll = len(links)
        if ll == 0:
            self.log.error('failed to extract the links')
            return (None, None)
        for i in xrange(0, ll):
            pinfo = self.stream_extract(self.links_handle(i, links), self)
            self.name_handle(i, pinfo)
            list.append(pinfo)
            self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
        config.win_mgr.append_title(defs.Homepage.str[pinfo.homepage_type])
        config.win_mgr.append_title(pinfo.name.encode('utf-8')) # TODO pinfo doesn't need name-information
        if ll == 1:
            config.win_mgr.append_title(pinfo.title.encode('utf-8'))
        return (pinfo.name, list)


class AnimeLoads(Pages):
    stream_extract = AnimeLoadsStream
    movie_types    = ['movies', 'ovas', 'asia', 'serien']

    def __init__(self, log):
        self.pages_init__(log)
        self.cookies = ['hentai=aktiviert']

    def extract_url(self, url, type = Pages.TYPE_UNK):
        if type == Pages.TYPE_UNK:
            if url.find('stream') < 0:
                type = Pages.TYPE_MULTI
            else:
                type = Pages.TYPE_SINGLE
        if type == Pages.TYPE_MULTI:
            url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

            self.tmp['name'] = glob_name = textextract(textextract(url.data, '<h1>','</h1>'), ' - ', '').decode('iso-8859-1')

            data = url.data[url.data.find('>001</th'):].split('\n') # data will start where the first interesting thing occurs
            links = []
            for line in data:
                if line.find('livestream1') < 0:
                    continue
                # <tr><td  width="20" ><a href="stream.php?id=18717" target="_blank"><img src="images/livestream1.png" width="20
                # <a href="../streams/
                link = textextract(line, '<a href="', '"')
                if not link:
                    continue
                if link.startswith('../'):
                    link = link[3:]
                links.append(link)
                skip = 14
        else:
            links = [url]
            glob_name = 'animeloads stream'
        self.tmp['type'] = type
        i, list = self.add_streams(links)
        self.tmp = {}
        if list:
            container = VideoContainer(glob_name)
            container.list = list
            self.video_container.append(container)
            return container
        return None

    def get_movie_list(self, type = None):
        if type:
            link = 'http://anime-loads.org/register.php?typ=%s&reg=%%' % type
            url = UrlMgr({'url': link, 'log': self.log})
            if not url.data:
                log.error('anime-loads down')
                sys.exit(1)
            stuff = textextractall(url.data, ' ><a href="page.php', '</')
            for i in xrange(0, len(stuff)):
                stuff[i] = remove_html(textextract(stuff[i], 'strong>', '').decode('utf-8'))
            return stuff
        else:
            ret = {}
            for i in self.movie_types:
                ret[i] = self.get_movie_list(i)
            return ret

    def links_handle(self, i, links):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            return 'http://anime-loads.org/%s' % links[i]
        return links[i]

    def name_handle(self, i, pinfo):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            pinfo.name = self.tmp['name']
        return


class AnimeKiwi(Pages):
    stream_extract = AnimeKiwiStream

    def __init__(self, log):
        self.pages_init__(log)

    def extract_url(self, url, type = Pages.TYPE_UNK):
        if type == Pages.TYPE_UNK:
            if url.find('watch') == -1:     # its a bit difficult to find out what the link means :-/
                type = Pages.TYPE_MULTI
            else:
                type = Pages.TYPE_SINGLE
        if type == Pages.TYPE_MULTI:
            # http://www.animekiwi.com/kanokon/
            url = UrlMgr({'url': url, 'log': self.log})
            links = textextractall(url.data, '<a href="/watch/','"') # <a href="/watch/kanokon-episode-12/" target="_blank">Kanokon Episode 12</a>
        else:
            links = [url]
        self.tmp['type'] = type
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            container.list = list[::-1] # cause they are in the wrong order
            # TODO sometimes they have two entries for each part (subbed / dubbed) -> make sure to download only one
            self.video_container.append(container)
            return container
        return None

    def links_handle(self, i, links):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            return 'http://animekiwi.com/watch/%d' % links[i]
        return links[i]


class AnimeJunkies(Pages):
    stream_extract = AnimeJunkiesStream

    def __init__(self, log):
        self.pages_init__(log)

    def extract_url(self, url, type = Pages.TYPE_UNK):
        if type == Pages.TYPE_UNK:
            if url.find('serie') >= 0:
                type = Pages.TYPE_MULTI
            else:
                type = Pages.TYPE_SINGLE
        if type == Pages.TYPE_MULTI:
            url = UrlMgr({'url': url, 'log': self.log})
            links = textextractall(url.data, '<a href="film.php?name=','"')
            self.tmp['titles'] = textextractall(url.data, 'lass="Stil3 Stil111"/><strong>\n\t       ', '</strong')
        else:
            links = [url]
        self.tmp['type'] = type
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            container.list = list
            self.video_container.append(container)
            return container
        return None

    def links_handle(self, i, links):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            return 'http://anime-junkies.org/film.php?name=%s' % links[i].replace(' ', '+')
        return links[i]

    def name_handle(self, i, pinfo):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            pinfo.title = '%03d: %s' % ((i+1), remove_html(self.tmp['titles'][i]).replace('/', '-'))
        return


class YouTube(Pages):
    stream_extract = YouTubeStream

    def __init__(self, log):
        self.pages_init__(log)

    def extract_url(self, url, type = Pages.TYPE_UNK):
        containername = ''
        if type == Pages.TYPE_UNK:
            if url.find('view_play_list') >= 0:
                # http://www.youtube.com/view_play_list?p=9E117FE1B8853013&search_query=georg+kreisler
                type = Pages.TYPE_MULTI
            else:
                type = Pages.TYPE_SINGLE
        if type == Pages.TYPE_MULTI:
            url = UrlMgr({'url': url, 'log': self.log})
            # alt="Georg Kreisler: Schlagt sie tot?"></a><div id="quicklist-icon-bmQbYP_VkCw" class="addtoQL90"
            # maybe we can get all this data in one action..
            links = textextractall(url.data, 'id="add-to-quicklist-', '"')
            self.tmp['names'] = textextractall(url.data, '" alt="', '"') # luckily this alt-tag only occurs for those icons :)
            containername = remove_html(self.tmp['names'][0].decode('utf-8'))
        else:
            links = [url]
        self.tmp['type'] = type
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            if containername:
                container.name = containername
            container.list = list
            self.video_container.append(container)
            return container
        return None


    def name_handle(self, i, pinfo):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            pinfo.title = remove_html(self.tmp['names'][i + 1].decode('utf-8'))

    def links_handle(self, i, links):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            return 'http://www.youtube.com/watch?v=%s' % links[i]
        else:
            return links[i]


class KinoTo(Pages):
    stream_extract = KinoToStream

    def __init__(self, log):
        self.pages_init__(log)
        # getting cookie
        self.log.info('connecting to kino.to')
        url = UrlMgr({'url': 'http://kino.to/', 'log': self.log})
        hash = textextract(url.data, 'sc(\'', '\'')
        # sitechrx=HASH;
        self.cookies = ['sitechrx=%s' % hash]
        self.log.debug('kino.to cookies %s' % repr(self.cookies))

    def extract_url(self, url, type = Pages.TYPE_UNK):
        if type == Pages.TYPE_UNK:
            if url.find('=Season') >= 0:
                # http://kino.to/?Goto=Season&PA=3618&PB=1
                type = Pages.TYPE_MULTI
            else:
                type = Pages.TYPE_SINGLE
        if type == Pages.TYPE_MULTI:
            PA = textextract(url, 'PA=', '&')
            PB = textextract(url, 'PB=', '')
            post = 'Request=LoadModule&Name=Season&Param1=%s&Param2=%s&Data=KO' % (PA, PB)
            self.tmp['stream_id'] = PA
            url = 'http://kino.to/res/php/Ajax.php'
            url = UrlMgr({'url': url, 'post': post, 'log': self.log, 'cookies': self.cookies})
            self.tmp['glob_name'], x = textextract(url.data, '"Title":"', '"', 100) # 100 is just, cause i'm sure that the title is not at the beginning
            x = url.data.find('Entrys":[{', x)
            links = []
            self.tmp['names'] = []
            '''"Entrys":[{"LinkID":"10042","LanguageID":"0001","Title":" Episode 03 Angelic Layer Folge 3 German Part
            3-3","HosterID":"008","HosterName":"SevenLoad","Date   ":"15.06.08
            00:18","Identfier":"Flash"},...'''
            # hostername in this information is sometimes wrong
            while True:
                extr = textextract(url.data, '"LinkID":"', '"', x)
                if not extr:
                    break
                x = extr[1] + 1
                links.append(extr[0])
                extr = textextract(url.data, '"Title":"', '"', x)
                self.tmp['names'].append(extr[0])
                x = extr[1] + 1
        else:
            links = [url]
        self.tmp['type'] = type
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            self.video_container.append(container)
            container.list = list
            return container
        return None

    def name_handle(self, i, pinfo):
        if self.tmp['type'] == Pages.TYPE_MULTI:
            pinfo.title = remove_html(self.tmp['names'][i].decode('utf-8'))
            pinfo.name  = self.tmp['glob_name'].decode('utf-8')
        pinfo.title = pinfo.title.decode('utf-8')

    def links_handle(self, i, links):
        if self.tmp['type'] == Pages.TYPE_SINGLE:
            return links[i]
        else:
            def urlencode(str):
                return str.replace(' ', '%20')
            return 'http://kino.to/Entry/%s/%s/%s.html' % (self.tmp['stream_id'], links[i], urlencode(self.tmp['names'][i]))
            #http://kino.to/Entry/3618/10042/%20Episode%2003%20Angelic%20Layer%20Folge%203%20German%20Part%203-3.html
            # ...................seasonid/linkid/urlencoded(name).html
