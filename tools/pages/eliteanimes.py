from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys
from time import clock

class EliteAnimes(Page):
    def __init__(self):
        Page.__init__(self)
        self.name = 'Eliteanimes'
        self.url = 'http://www.eliteanimes.com'

        # TODO cache this
        url = UrlMgr({'url': 'http://www.eliteanimes.com', 'cache_writeonly':True})
        for cookie in url.pointer.cookies:
            if cookie.find('cDRGN') >= 0:
                self.cookies = ['cDRGN'+textextract(cookie, 'cDRGN', ';')]
                break
        else:
            self.log.error("no cookie -> this means mostly a captcha")
            self.log.error(url.data)
            imgUrl = textextract(url.data, 'src="/captcha/?rnd=', '"')
            if imgUrl:
                self.log.error("as i said.. a captcha")
                imgUrl = 'http://www.eliteanimes.com/captcha/?rnd='+imgUrl
                url = UrlMgr({'url': imgUrl, 'cache_writeonly':True})
            import sys
            sys.exit()

    def checkPage(self, url):
        imgUrl = textextract(url.data, 'src="/captcha/?rnd=', '"')
        if imgUrl:
            self.log.error("as i said.. a captcha")
            self.log.error("please visit http://www.eliteanimes.com/ and enter the captcha and you won't be bothered again")
            # TODO crack this captcha and return a new url object
            imgUrl = 'http://www.eliteanimes.com/captcha/?rnd='+imgUrl
            url = UrlMgr({'url': imgUrl, 'cache_writeonly':True})
            import sys
            sys.exit()
        return url

    def getAllPages(self):
        allPages = []
        import string
        start = clock()
        for pageType in string.uppercase:
            url = UrlMgr({'url': 'http://www.eliteanimes.com/anime/list/'+pageType+'/', 'log': self.log, 'cookies':self.cookies})
            url = self.checkPage(url)
            self.log.info("Get all pages from '"+pageType)

            root = html.fromstring(url.data)
            for row in root.iterfind(".//td[@class='xhead bold']"):
                mediaA = row.find("a")
                if mediaA == None:
                    continue
                mediaUrl = 'http://www.eliteanimes.com/'+mediaA.get("href")
                media = self.extract(mediaUrl)
                if media:
                    media.addTag(self.name)
                    self.log.info("finished page '"+media.name+"'")
                    allPages.append(media)
        return allPages

    def extract(self, link):
        url = link.replace('details', 'stream')
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})
        url = self.checkPage(url)

        start = clock()
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

        url = link.replace('stream', 'details')
        log.error(url)
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})
        url = self.checkPage(url)
        # extract image and tags
        imgUrl = textextract(url.data, 'src="Bilder', '"')
        if imgUrl:
            media.img = 'http://www.eliteanimes.com/Bilder'+imgUrl


        def getDetailContent(data, name):
            content = textextract(url.data, '<td class="atitle2" valign="top">'+name+'</td>', '</tr>')
            if not content:
                return None
            content = textextract(content, '<td class="acontent2">', '</td>')
            if content.find('Noch nichts eingetragen'):
                return None

        year = getDetailContent(url.data, 'Jahr')
        if year:
            try:
                media.year = int(year[:4])
            except:
                media.year = int(year[7:11])
        else:
            self.log.warning("No year")

        for name in ("Zielgruppe", "Setting", "Genre"):
            content = getDetailContent(url.data, name)
            if content:
                media.addTags(textextractall(content, '"><strong> ', ' </strong>'))

        return media

urlPart = 'eliteanimes.com' # this part will be matched in __init__ to create following class
classRef = EliteAnimes
