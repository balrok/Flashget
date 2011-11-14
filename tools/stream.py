from tools.url import UrlMgr
from tools.helper import *
import tools.defines as defs
from stream_extract import *
import sys


def extract_stream(data):
    ''' extracts the streamlink from specified data '''
    data = data.replace("\n", "")
    url = ''
    post = textextract(data, 'value="domain=hdweb.ru&', '&mode') # TODO: i think we can extract this from the url
    if post:
        url = 'http://hdweb.ru'
    # stagevu
    if not url:
        url = textextract(data, 'src="http://stagevu.com', '"')
        if url:
            url = "http://stagevu.com"+url
    if not url:
        url = textextract(data, '<embed src="', '"')
    if not url:
        url = textextract(data, '<embed src=\'', '\'')
    if not url:
        url = textextract(data, '<param name="movie" value="','"')
    if not url:
        url = textextract(data, '<param value="','" name="movie"')
    if not url:
        url = textextract(data, '<param name=\'movie\' value=\'','\'')
    if not url:
        url = textextract(data, 'www.myvideo.de','"')
        if url:
            id = textextract(url, 'ID=', '&')
            if id:
                url = 'http://www.myvideo.de/watch/'+id
            else:
                url = None
    if not url:
        url = textextract(data, "so.addVariable('file','", "'")
    return {'url': url, 'post': post}


class VideoInfo(object):
    def __init__(self, url, log):
        self.log = log
        self.stream_post = None
        if isinstance(url, UrlMgr):
            self.url_handle = url
            self.url = url.url
        else:
            self.url = urldecode(url)
            self.url_handle = UrlMgr({'url': self.url})

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.url)

    def __getattr__(self, key):
        if key == 'subdir':
            return self.get_subdir()
        elif(key == 'stream_url'):
            return self.get_stream()
        elif(key == 'stream_type'):
            self.get_stream()
            return self.stream_type
        elif(key == 'stream_id'):
            self.get_stream()
            return self.stream_id
        elif(key == 'flv_url'):
            return self.get_flv()
        elif(key == 'flv_call'):
            self.get_flv()
            return self.flv_call
        elif(key == 'flv_available'):
            if not self.stream_type:
                return False
            self.flv_available = def2func[self.stream_type](self, False, True)
            return self.flv_available
        elif(key == 'flv_type'):
            if self.stream_type:
                self.flv_type = defs.Stream.str[self.stream_type]
            else:
                self.flv_type = None
            return self.flv_type

    def __str__(self):
        return self.name+" "+self.title

    def get_subdir(self):
        dir = self.name
        import os
        import config
        dir2 = os.path.join(config.flash_dir, dir)
        if os.path.isdir(dir2) is False:
            try:
                os.makedirs(dir2)
            except:
                self.log.error('couldn\'t create subdir in %s' % dir2)
                dir = ''
            open(dir2 + '/.flashget_log', 'a').write(' '.join(sys.argv) + '\n')
        self.subdir = dir
        return self.subdir

    def get_flv(self):
        ret = def2func[self.stream_type](self)
        if not ret:
            ret = (None, (None, None))
        self.flv_url, self.flv_call = ret
        return self.flv_url

    def get_title(self):
        self.log.error("TITLE must be downloaded from overviewpage")
        if not self.title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            self.log.info('couldnt extract title - will now use the hash from this url: %s' % self.title)
        else:
            self.title = normalize_title(self.title)
        return self.title

    def get_name(self):
        name = textextract(self.url, 'streams/','/')
        if not name:
            self.name = self.__hash__()
            self.log.info('couldnt extract name - will now use hash: %s' % self.name)
        else:
            self.name = normalize_title(name)
        return self.name

    def get_stream(self):
        x = self.url_handle.data.find('id="download"')
        stream = extract_stream(self.url_handle.data)
        # for some videos this happened and resulted in bad requests it's possible to implement this check generic, but currently it's only for animeloads
        if not stream or not stream['url']:
            stream = {'url':self.url_handle.url}

        def findStream(streamUrl):
            for i in url2defs:
                if streamUrl.find(i) > 0:
                    return url2defs[i]
            return None

        if 'post' in stream:
            self.stream_post = stream['post']
        streamType = findStream(stream['url'])
        self.stream_url = stream['url']
        if streamType is None:
            streamType = findStream(self.url_handle.url)
            self.stream_url = self.url_handle.url
        if streamType is None:
            self.log.error('couldn\'t find a supported streamlink in: %s, on: %s' % (self.stream_url, self.url_handle.url))
            self.stream_url = None
            self.stream_type = None
            self.stream_id = None
            return None
        self.stream_type = streamType
        self.stream_id = def2func[self.stream_type](self, True)
        return self.stream_url
