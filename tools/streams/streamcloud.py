from tools.extension import Extension
from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract
from tools.stream import BaseStream
import logging

log = logging.getLogger('streams')


class Streamcloud(Extension, BaseStream):
    ename = 'Streamcloud'
    # match all streamcloud links which don't end in .mp4 (those can be directly loaded)
    eregex = '.*streamcloud.*(?<!\.mp4)$'
    url = "http://streamcloud.eu"
    # moved the code to the downloadpart since the links to the videos are only shortly available
    # also you can only download one
    ePriority = 20
    def get(self, VideoInfo, justId=False, isAvailable=False):
        link = VideoInfo.stream_url
        vId = textextract(link, 'streamcloud.eu/', '/')
        if justId:
            return vId
        self.flvUrl = link
        return self.flvUrl

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")

        link = self.flvUrl
        vId = textextract(link, 'streamcloud.eu/', '/')
        url = UrlMgr(url=link, nocache=True)
        if not url.data:
            log.error('could not download page for %s', link)
            return False
        log.info("Streamcloud wants us to wait 10 seconds - we wait 11 :)")
        if not kwargs['sleep'](11):
            return False
        post = {
            'id':vId,
            'imhuman': 'Watch video now',
            'op': 'download1',
            'usr_login': '',
            'fname': textextract(link, 'streamcloud.eu/'+vId+'/', ''),
            'referer': '',
            'hash': ''
        }
        url = UrlMgr(url=link, nocache=True, keepalive=False, post=post)
        self.flvUrl = textextract(url.data, 'file: "', '"')
        if not self.flvUrl:
            log.error('no flvUrl found for %s', link)
            return False

        kwargs['url'] = self.flvUrl
        log.info('Extracted following url for download: %s', self.flvUrl)
        return LargeDownload(**kwargs)
