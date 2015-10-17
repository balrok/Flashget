from flashget.url import UrlMgr, LargeDownload
from flashget.helper import textextract
from flashget.stream import BaseStream
import logging
import urlparse

log = logging.getLogger(__name__)

# there exists multiple pages which only work slightly different
# since I first discovered nowvideo, I take this as "parent"-stream site
# the other is videoweed
# only the url is different and how the filekey is stored in the js
class NowvideoBasic(BaseStream):
    ename = 'NowvideoBasic'
    eregex = '(.*movshare.*)|(.*videoweed.*)|(.*nowvideo.*)'
    ePriority = 5 # they are very slow
    url = "http://nowvideo.sx or http://videoweed.es or movshare"
    # following attributes must be overwritten
    videoidExtract1 = ('video/', '')
    videoidExtract2 = ('file/', '')
    filekeyExtract1 = ('flashvars.filekey="', '"')
    filekeyExtract2 = ('var fkzd="', '"')

    def getId(self):
        id1 = textextract(self.flvUrl, *self.videoidExtract1)
        if id1 is None:
            return textextract(self.flvUrl, *self.videoidExtract2)
        return id1


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
        key = textextract(url.data, *self.filekeyExtract1)
        if key is None or len(key) < 1 or len(key) > 40:
            key = textextract(url.data, *self.filekeyExtract2)

        params = {
                'user': 'undefined',
                'numOfErrors': 0,
                'key': key,
                'pass': 'undefined',
                'cid': 'undefined',
                'file': textextract(url.data, 'flashvars.file="', '";'),
                'cid2': 'undefined',
                'cid3': 'undefined'
                }
        parsed_url = urlparse.urlparse(self.flvUrl)
        url = "%s://%s" % (parsed_url.scheme, parsed_url.netloc)
        apiUrl = url+"/api/player.api.php"

        url = UrlMgr(url=apiUrl, params=params, nocache=True)
        if url.data[:4] == 'url=':
            kwargs['url'] = textextract(url.data, 'url=', '&title')
        else:
            log.error("could not find downloadfile %s", url.data)
            if 'invalidate_cache' not in kwargs:
                log.info("retry without cache")
                kwargs['invalidate_cache'] = True
                return self.download(**kwargs)
            else:
                log.error("could still not find downloadfile %s", url.data)
                return None
        return LargeDownload(**kwargs)
