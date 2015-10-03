from flashget.url import LargeDownload
from flashget.stream import BaseStream
import logging

log = logging.getLogger(__name__)
from flashget.compatible.urlresolver.curlresolver import resolve


class Urlresolver(BaseStream):
    ename = 'Urlresolver'
    # match all streamcloud links which don't end in .mp4 (those can be directly loaded)
    eregex = '.*'
    url = "everything urlresolver can do"
    ePriority = -1

    def getId(self):
        return 0

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")

        flvUrl = resolve(self.flvUrl)

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
        return dict(link='X',
             linkId='X',
             className='X',
             size=1234)
