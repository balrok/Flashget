from tools.extension import Extension
from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract
from tools.stream import BaseStream
import logging

log = logging.getLogger(__name__)

# there exists multiple pages which only work slightly different
# since I first discovered nowvideo, I take this as "parent"-stream site
# the other is videoweed
# only the url is different and how the filekey is stored in the js
class NowvideoBasic(Extension, BaseStream):
    ename = 'NowvideoBasic'
    eregex = 'dontusexyzqwert'
    url = "http://nowvideo.sx or http://videoweed.es"
    # following attributes must be overwritten
    videoidExtract = ('video/', '')
    filekeyExtract = ('flashvars.filekey="', '"')

    # moved the code to the downloadpart since the links to the videos are only shortly available
    # also you can only download one
    ePriority = 5 # they are very slow
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        vId = textextract(link, *self.videoidExtract)
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
            log.info("File was removed")
            return None
        params = {
                'user': 'undefined',
                'numOfErrors': 0,
                'key': textextract(url.data, *self.filekeyExtract),
                'pass':'undefined',
                'cid':'undefined',
                'file': textextract(url.data, 'flashvars.file="', '";'),
                'cid2':'undefined',
                'cid3':'undefined'
                }
        apiUrl = self.url+"/api/player.api.php"
        url = UrlMgr(url=apiUrl, params=params, nocache=True)
        if url.data[:4] == 'url=':
            self.flvUrl = textextract(url.data, 'url=', '&title')
        else:
            log.error("could not find downloadfile %s", url.data)
            if 'invalidate_cache' not in kwargs:
                log.info("retry without cache")
                kwargs['invalidate_cache'] = True
                return self.download(**kwargs)
            else:
                log.error("could still not find downloadfile %s", url.data)
                return None
        kwargs['url'] = self.flvUrl
        return LargeDownload(**kwargs)

class Nowvideo(NowvideoBasic):
    ename = 'Nowvideo'
    eregex = '.*nowvideo.*$'
    url = "http://nowvideo.sx"

    videoidExtract = ('video/', '')
    filekeyExtract = ('var fkzd="', '"')

class Videoweed(NowvideoBasic):
    ename = 'Videoweed'
    eregex = '.*videoweed.*$'
    url = "http://videoweed.es"

    videoidExtract = ('file/', '')
    filekeyExtract = ('flashvars.filekey="', '"')

class Movshare(NowvideoBasic):
    ename = 'Movshare'
    eregex = '.*movshare.*$'
    url = "http://movshare.net"

    videoidExtract = ('video/', '')
    filekeyExtract = ('flashvars.filekey="', '"')
