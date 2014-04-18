from tools.url import UrlMgr, LargeDownload
from tools.helper import urldecode, normalize_title, textextract
import logging
from tools.extension import ExtensionRegistrator
import tools.commandline as commandline

log = logging.getLogger('VideoInfo')


class BaseStream(object):
    url = "every url"
    def __init__(self):
        self.flvUrl = ''
    def get(self, VideoInfo, justId=False, isAvailable=False):
        raise Exception
    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)



flashExt = ExtensionRegistrator()
flashExt.loadFolder('tools/streams/')


def extract_stream(data):
    ''' extracts the streamlink from specified data '''
    data = data.replace("\n", "")
    url = ''
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
    return {'url': url}


# maintains lowlevel information about this file
# basically name, title and stream object
class VideoInfo(object):
    def __init__(self, url):
        if isinstance(url, UrlMgr):
            self.url_handle = url
            self.url = url.url
        else:
            self.url = urldecode(url)
            if 'megavideo' in self.url:
                self.url = self.url.replace('/v/', '/?v=')
            if 'videobb' in self.url:
                self.url = self.url.replace('/e/', '/video/')
            if 'videozer' in self.url:
                self.url = self.url.replace('/embed/', '/video/')
            self.url_handle = UrlMgr({'url': self.url})

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.url)

    def __getattr__(self, key):
        if key == 'subdir':
            return self.get_subdir()
        elif key == 'stream_url':
            return self.get_stream()
        elif key == 'stream':
            self.get_stream()
            return self.stream
        elif key == 'stream_id':
            self.get_stream()
            return self.stream_id
        elif key == 'flv_url':
            return self.get_flv()
        elif key == 'flv_available':
            if not self.stream:
                return False
            self.flv_available = self.stream.get(self, False, True)
            return self.flv_available
        elif key == 'flv_type':
            if self.stream:
                self.flv_type = self.stream.ename
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
                log.error('couldn\'t create subdir in %s', dir2)
                dir = ''
            open(dir2 + '/.flashget_log', 'a').write(commandline.get_log_line() + '\n')
        self.subdir = dir
        return self.subdir

    def get_flv(self):
        self.flv_url = self.stream.get(self)
        return self.flv_url

    def get_title(self):
        log.error("TITLE must be downloaded from overviewpage")
        if not self.title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            log.info('couldnt extract title - will now use the hash from this url: %s', self.title)
        else:
            self.title = normalize_title(self.title)
        return self.title

    def get_name(self):
        name = textextract(self.url, 'streams/','/')
        if not name:
            self.name = self.__hash__()
            log.info('couldnt extract name - will now use hash: %s', self.name)
        else:
            self.name = normalize_title(name)
        return self.name

    def get_stream(self):
        self.stream_url = self.url_handle.url

        def findStream(streamUrl):
            stream = flashExt.getExtensionByRegexStringMatch(streamUrl)
            if stream:
                stream = stream()
                return stream
            return None

        stream = findStream(self.url_handle.url)
        if stream is None:
            streamData = extract_stream(self.url_handle.data)
            if streamData and streamData['url']:
                stream = findStream(streamData['url'])
                self.stream_url = streamData['url']

        if stream is None:
            log.error('couldn\'t find a supported streamlink in: %s, on: %s', self.stream_url, self.url_handle.url)
            self.stream_url = None
            self.stream = None
            self.stream_id = None
            return None
        self.stream = stream
        self.stream_id = stream.get(self, True)
        return self.stream_url
