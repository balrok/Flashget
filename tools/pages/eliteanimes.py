from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class EliteAnimes(Page):
    def __init__(self):
        self.pages_init__()
        self.name = 'eliteanimes'
        self.url = 'http://www.eliteanimes.com'

    def extract(self, url):
        detailPage = UrlMgr({'url': url, 'log': self.log, 'cache_writeonly':False})
        for cookie in detailPage.pointer.cookies:
            if cookie.find('cDRGN') >= 0:
                self.cookies = ['cDRGN'+textextract(cookie, 'cDRGN', ';')]

        url = url.replace('details', 'stream')
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

        root = html.fromstring(url.data)
        try:
            media = Media(textextract(url.data, '<title>Anime Stream ', ' - German Sub / German Dub Animestreams</title>'))
        except:
            self.log.error('couldn\'t extract name, wrong url or html has changed')
            return None

        root = html.fromstring(url.data)
        # each link to a video contains episode..
        num = 0
        for streamA in root.xpath(".//a[contains(@href,'/episode/')]"):
            num += 1
            streamLink = 'http://www.eliteanimes.com/'+streamA.get('href')
            title = streamA.text
            part = media.createSub()
            part.num = "%03d"%num
            part.name = title
            alternativePart = part.createSub().createSub()
            alternativePart.url = streamLink
            self.setPinfo(alternativePart)
            alternativePart.pinfo.url_handle.cookies = self.cookies
        return media

urlPart = 'eliteanimes.com' # this part will be matched in __init__ to create following class
classRef = EliteAnimes
