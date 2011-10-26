# -*- coding: utf-8 -*-

from url import UrlMgr
from helper import *
import defines as defs
import config
from stream_extract import *
import helper
import sys
from lxml import html
from lxml import etree
import re


class VideoInfo(object):

    def init__(self, url, log):
        self.url = helper.urldecode(url)
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
            open(dir2 + '/.flashget_log', 'a').write(' '.join(sys.argv) + '\n')
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
            if config.dl_title:
                return config.dl_title
            return self.get_title__(self.get_title())
        elif(key == 'name'):
            if config.dl_name:
                return config.dl_name
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
        url = 'http://hdweb.ru'
    if not url:
        url = textextract(data, '<embed src="', '"')
    if not url:
        url = textextract(data, '<embed src=\'', '\'')
    if not url:
        url = textextract(data, '<param name="movie" value="','"')
    if not url:
        url = textextract(data, '<param name=\'movie\' value=\'','\'')
    return {'url': url, 'post': post}


class PlainStream(VideoInfo):
    homepage_type = defs.Homepage.Plain
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        return 'no title'

    def get_name(self):
        return 'no name'

    def get_subdir(self):
        return 'plain'

    def get_stream(self):
        return {'url': self.url}


class YouTubeStream(VideoInfo):
    homepage_type = defs.Homepage.YOUTUBE
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        # <title>YouTube - Georg Kreisler - Taubenvergiften</title>
        return textextract(self.url_handle.data, 'title>YouTube - ', '</title').decode('utf-8')

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


class AnimeLoadsStream(VideoInfo):
    homepage_type = defs.Homepage.ANIMELOADS
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        self.log.error("TITLE must be downloaded from overviewpage")
        return ''

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
        config.win_mgr.append_title(pinfo.name.encode('utf-8'))
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
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

        try:
            self.tmpName = glob_name = textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>')
        except:
            self.log.error('couldn\'t extract name, dumping content...')
            self.log.error(url.data)
            import sys
            sys.exit(1)

        root = html.fromstring(url.data)
        listTable = root.get_element_by_id('partlist')
        if listTable == None:
            pass # throw error
        self.tmp = []
        links = []
        for row in listTable.iterfind(".//tr[@class='link']"):
            data = {}
            curCol = 0
            for column in row.iterfind("td"):
                curCol += 1
                if curCol == 1:
                    data['num'] = column.text
                if curCol == 2:
                    data['name'] = column.text
                #if curCol == 3: not used cause we have it also per stream
                #    data['audio'] = re.findall("lang/(..)\.png", etree.tostring(column))
                #if curCol == 4:
                #    data['sub'] = re.findall("lang/(..)\.png", etree.tostring(column))
                if curCol == 5: # download links
                    pass
                if curCol == 6: # stream links
                    dlTable = column.find(".//table[@class='dltable']")
                    if dlTable == None:
                        print ERROR
                        continue
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        streamData = {}
                        streamCurCol = 0
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            if streamCurCol == 1:
                                streamColumnString = etree.tostring(streamColumn)
                                streamData['hoster'] = re.search("hoster/(.*?)\.png", streamColumnString)
                                if streamData['hoster']:
                                    streamData['hoster'] = streamData['hoster'].group(1)
                                streamData['redirectUrl'] = re.search("a href=\"(.*?)\"", streamColumnString)
                                if streamData['redirectUrl']:
                                    streamData['redirectUrl'] = streamData['redirectUrl'].group(1)
                                    redirectUrl = UrlMgr({'url': streamData['redirectUrl'], 'log': self.log, 'cookies': self.cookies})
                                    realUrl = re.search("http-equiv=\"refresh\" content=\".;URL=(.*?)\"", redirectUrl.data)
                                    if realUrl:
                                        streamData['url'] = realUrl.group(1)
                                        links.append(realUrl.group(1))
                                    else:
                                        streamData['url'] = ''
                                        links.append('')
                            if streamCurCol == 2:
                                streamData['audio'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 3:
                                streamData['sub'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                    data['stream'] = streamData
            self.tmp.append(data)
        i, list = self.add_streams(links)
        if list:
            container = VideoContainer(glob_name)
            container.list = list
            self.video_container.append(container)
            return container
        return None

    def links_handle(self, i, links):
        return self.tmp[i]['stream']['url']

    def name_handle(self, i, pinfo):
        pinfo.name = self.tmpName
        pinfo.title = self.tmp[i]['num'] +" "+self.tmp[i]['name']


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


class Plain(Pages):
    stream_extract = PlainStream
    def __init__(self, log):
        self.pages_init__(log)

    def extract_url(self, url, type = Pages.TYPE_SINGLE):
        links = [url]
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            self.video_container.append(container)
            container.list = list
            return container
        return None

    def name_handle(self, i, pinfo):
        pinfo.title = 'no title'
    def links_handle(self, i, links):
        return links[i]
