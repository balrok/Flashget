from tools.extension import Extension
from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract
from tools.stream import BaseStream
import logging

log = logging.getLogger(__name__)


class Nowvideo(Extension, BaseStream):
    ename = 'Nowvideo'
    eregex = '.*nowvideo.*$'
    url = "http://nowvideo.sx"
    # moved the code to the downloadpart since the links to the videos are only shortly available
    # also you can only download one
    ePriority = 5 # they are very slow
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        vId = textextract(link, 'video/', '')
        if justId:
            return vId
        self.flvUrl = link
        return self.flvUrl

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        if 'invalidate_cache' in kwargs:
            url = UrlMgr(url=self.flvUrl, nocache=True)
        else:
            url = UrlMgr(url=self.flvUrl)
        if url.data.find("This file no longer exists on our servers.") > 0:
            log.info("Nowvideo - file was removed")
            return None
        key = textextract(url.data, 'var fkzd="', '";')
        fileKey = textextract(url.data, 'flashvars.file="', '";')
        cid = "undefined" # textextract(url.data, 'flashvars.cid="', '";')
        cid2 = "undefined" # textextract(url.data, 'flashvars.cid2="', '";')
        params = {
                'user': 'undefined',
                'numOfErrors': 0,
                'key': key,
                'pass':'undefined',
                'cid':cid,
                'file':fileKey,
                'cid2':cid2,
                'cid3':'undefined'
                }
        url = UrlMgr(url='http://www.nowvideo.sx/api/player.api.php', params=params, nocache=True)
        self.flvUrl = url.request.url
        if url.data[:4] == 'url=':
            self.flvUrl = textextract(url.data, 'url=', '&title')
        else:
            log.error("could not find downloadfile retry without cache %s", url.data)
            if 'invalidate_cache' not in kwargs:
                kwargs['invalidate_cache'] = True
                return self.download(**kwargs)
            log.error("could not find downloadfile %s", url.data)
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)
