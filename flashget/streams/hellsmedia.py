from flashget.url import UrlMgr, LargeDownload
from flashget.helper import textextract
from flashget.stream import BaseStream
import logging

log = logging.getLogger(__name__)

class Hellsmedia(BaseStream):
    ename = 'Hellsmedia'
    # match all streamcloud links which don't end in .mp4 (those can be directly loaded)
    eregex = '.*hellsmedia.*$'
    url = "http://hellsmedia.com"
    ePriority = 20

    def getId(self):
        return textextract(self.flvUrl, 'hellsmedia.com/v/', '')

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")

        vId = self.getId()
        url = UrlMgr(url=self.flvUrl, nocache=True)
        if not url.data:
            log.error('could not download page for %s', self.flvUrl)
            return False
        tmpId = textextract(url.data, '<iframe class="player" src="http://hellsmedia.com/player/'+vId+"/", '/0"')
        url2 = UrlMgr("http://hellsmedia.com/js/v.js/"+vId+"/"+tmpId+"/0", nocache=True)
        downloadId = textextract(url2.data, "'playlistfile': 'http://hellsmedia.com/xml/v.xml/"+vId+"/", "/0")
        # print "http://hellsmedia.com/js/v.js/"+vId+"/"+tmpId+"/0"
        # print downloadId

        flvUrl = None
        if downloadId:
            flvUrl = "http://hellsmedia.com/flv/v.flv/"+vId+"/"+downloadId+"/0?start=0"
        # print flvUrl

        if not flvUrl:
            log.error('no flvUrl found for %s', self.flvUrl)
            return False

        kwargs['url'] = flvUrl
        log.info('Extracted following url for download: %s', flvUrl)
        return LargeDownload(**kwargs)

    @staticmethod
    def getTestData():
        return dict(link='XX://hellsmedia.com/v/zygwY1Z1q6',
             linkId='XX',
             className='Hellsmedia',
             size=93441644)
