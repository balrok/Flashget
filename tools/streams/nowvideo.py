from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import textextract
from tools.stream import BaseStream
import logging

log = logging.getLogger('streams')


class NowVideo(Extension, BaseStream):
    ename = 'NowVideo'
    eregex = '.*nowvideo.*$'
    url = "http://nowvideo.sx"
    # moved the code to the downloadpart since the links to the videos are only shortly available
    # also you can only download one
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        url = UrlMgr(url=link, nocache=True)
        key = textextract(url.data, 'var fkzd="', '";')
        fileKey = textextract(url.data, 'flashvars.file="', '";')
        cid = "undefined" #textextract(url.data, 'flashvars.cid="', '";')
        cid2 = "undefined" #textextract(url.data, 'flashvars.cid2="', '";')
        videoUrl = 'http://www.nowvideo.sx/api/player.api.php?user=undefined&numOfErrors=0&key=%s&pass=undefined&cid=%s&file=%s&cid2=%s&cid3=undefined'
        videoUrl = videoUrl % (key, cid, fileKey, cid2)
        url = UrlMgr(url=videoUrl, nocache=True)
        if url.data[:4] == 'url=':
            self.flvUrl = textextract(url.data, 'url=', '&title')
        else:
            log.error("could not find downloadfile "+url.data)
        return self.flvUrl
