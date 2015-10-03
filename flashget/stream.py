import time
import logging

from .url import LargeDownload
from .helper import textextract
from .config import config
from yapsy.IPlugin import IPlugin

log = logging.getLogger(__name__)


class BaseStream(IPlugin):
    url = "every url"
    score = 1

    def __init__(self):
        pass

    def setLink(self, link):
        self.flvUrl = link

    def getId(self):
        return textextract(self.link, '/', '')

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)
    # you can overwrite this
    def sleep(self, timeout):
        sleep_handler = config.get('sleep_handler', None)
        if sleep_handler is None:
            log.debug("sleeping %d seconds", timeout)
            time.sleep(timeout)
            return True
        else:
            return sleep_handler(self, timeout)
    @staticmethod
    def getTestData():
        raise Exception

    def getScore(self):
        return self.score
    def __str__(self):
        ret = self.__class__.__name__
        try:
            ret += ": " + self.getId()
        except:
            try:
                ret += ": " + self.flvUrl
            except:
                pass
        return ret


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


