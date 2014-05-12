import time
import os
from tools.url import UrlMgr, LargeDownload
from tools.helper import urldecode, normalize_title, textextract
import logging
from tools.extension import ExtensionRegistrator

log = logging.getLogger(__name__)


class BaseStream(object):
    url = "every url"
    def __init__(self):
        self.flvUrl = ''
    def get(self, VideoInfo, justId=False):
        link = VideoInfo.stream_url
        if justId:
            return textextract(link, '/', '')
        raise Exception
    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)
    # you can overwrite this
    def sleep(self, timeout):
        log.debug("sleeping %d seconds", timeout)
        time.sleep(timeout)
        return True


flashExt = ExtensionRegistrator()
def getStreamClassByLink(link):
    if not flashExt.loaded:
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'streams')
        flashExt.loadFolder(path)
    return flashExt.getExtensionByRegexStringMatch(link)


def extract_stream(data):
    ''' extracts the streamlink from specified data '''
    raise Exception("This method wasn't maintained for a long time and might be buggy")
    # data = data.replace("\n", "")
    # url = ''
    # # stagevu
    # if not url:
    #     url = textextract(data, 'src="http://stagevu.com', '"')
    #     if url:
    #         url = "http://stagevu.com"+url
    # if not url:
    #     url = textextract(data, '<embed src="', '"')
    # if not url:
    #     url = textextract(data, '<embed src=\'', '\'')
    # if not url:
    #     url = textextract(data, '<param name="movie" value="','"')
    # if not url:
    #     url = textextract(data, '<param value="','" name="movie"')
    # if not url:
    #     url = textextract(data, '<param name=\'movie\' value=\'','\'')
    # if not url:
    #     url = textextract(data, 'www.myvideo.de','"')
    #     if url:
    #         id = textextract(url, 'ID=', '&')
    #         if id:
    #             url = 'http://www.myvideo.de/watch/'+id
    #         else:
    #             url = None
    # if not url:
    #     url = textextract(data, "so.addVariable('file','", "'")
    # return {'url': url}


# maintains lowlevel information about this file
# basically name, title and stream object
class VideoInfo(object):
    def __init__(self, url):
        if isinstance(url, UrlMgr):
            self.stream_url = url.url
        else:
            self.stream_url = urldecode(url)

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.stream_url)

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
        elif key == 'flv_type':
            if self.stream:
                self.flv_type = self.stream.ename
            else:
                self.flv_type = None
            return self.flv_type

    def __repr__(self):
        return "%s: %s .-. %s" % (self.__class__.__name__, self.flv_type, self.title)

    def get_subdir(self):
        self.subdir = self.name
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

    def get_stream(self):
        stream = getStreamClassByLink(self.stream_url)
        if stream:
            stream = stream()

        # this would open the page and look for common flash embedding to find a link for the download
        # I think this code doesn't belong here and should go to each individual page extractor (only if needed - most won't need this)
        # if stream is None:
        #     streamData = extract_stream(UrlMgr(url=self.stream_url).data)
        #     if streamData and streamData['url']:
        #         stream = findStream(streamData['url'])
        #         self.stream_url = streamData['url']

        if stream is None:
            log.warning('couldn\'t find a supported streamlink in: %s', self.stream_url)
            self.stream_url = None
            self.stream = None
            self.stream_id = None
            return None
        self.stream = stream
        self.stream_id = stream.get(self, True)
        return self.stream_url
