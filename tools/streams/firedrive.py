from tools.extension import Extension
from tools.url import UrlMgr, LargeDownload
from tools.helper import textextract
from tools.stream import BaseStream
import logging

log = logging.getLogger(__name__)


class FireDrive(Extension, BaseStream):
    ename = 'FireDrive'
    eregex = '.*(putlocker|sockshare|firedrive).com.*$'
    url = "http://firedrive.com http://putlocker.com http://sockshare.com"
    ePriority = 1

    def __init__(self, link):
        self.flvUrl = link
        self.flvUrl = self.flvUrl.replace("putlocker", "firedrive").replace("sockshare", "firedrive")
        self.flvUrl = self.flvUrl.replace('/embed/', '/file/')

    def getId(self):
        return textextract(self.flvUrl, '.com/file/', '')

    def download(self, **kwargs):
        if not self.flvUrl:
            raise Exception("No flv url - can't start download")
        url = UrlMgr(url=self.flvUrl, nocache=True)
        if url.data.find("This file doesn't exist, or has been removed.") > 0:
            log.info("FireDrive - file was removed")
            return None
        confirm = textextract(url.data, 'name="confirm" value="', '"')
        if confirm is None:
            log.warning("FireDrive - could not find confirm link")
            return None
        url = UrlMgr(url=self.flvUrl, post={'confirm':confirm}, nocache=True)
        link = textextract(url.data, "file: 'http://dl.", "',")
        if link is None:
            log.error("Firedrive could not find link")
            return None
        kwargs['url'] = 'http://dl.'+link
        return LargeDownload(**kwargs)
