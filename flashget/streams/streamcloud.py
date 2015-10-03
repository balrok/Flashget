from flashget.url import UrlMgr, LargeDownload
from flashget.helper import textextract
from flashget.stream import BaseStream
import logging

log = logging.getLogger(__name__)


class Streamcloud(BaseStream):
    ename = 'Streamcloud'
    # match all streamcloud links which don't end in .mp4 (those can be directly loaded)
    eregex = '.*streamcloud.*(?<!\.mp4)$'
    url = "http://streamcloud.eu"
    ePriority = 20

    def getId(self):
        return textextract(self.flvUrl, 'streamcloud.eu/', '/')

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")

        vId = self.getId()
        url = UrlMgr(url=self.flvUrl, nocache=True)
        if not url.data:
            log.error('could not download page for %s', self.flvUrl)
            return False
        log.info("Streamcloud wants us to wait 10 seconds - we wait 11 :)")
        if not self.sleep(11):
            return False
        post = {
            'id': vId,
            'imhuman': 'Watch video now',
            'op': 'download1',
            'usr_login': '',
            'fname': textextract(self.flvUrl, 'streamcloud.eu/'+vId+'/', ''),
            'referer': '',
            'hash': ''
        }
        url = UrlMgr(url=self.flvUrl, nocache=True, keepalive=False, post=post)
        flvUrl = textextract(url.data, 'file: "', '"')
        if not flvUrl:
            log.error('no flvUrl found for %s', self.flvUrl)
            return False

        kwargs['url'] = flvUrl
        log.info('Extracted following url for download: %s', flvUrl)
        return LargeDownload(**kwargs)

    @staticmethod
    def getTestData():
        import os
        if 'TRAVIS' in os.environ:
            raise Exception
        return dict(link='XX',
             linkId='XX',
             className='Streamcloud',
             size=136181347)
