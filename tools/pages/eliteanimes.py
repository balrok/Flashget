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
        self.name = 'Eliteanimes'
        self.url = 'http://www.eliteanimes.com'
        Page.__init__(self)

        # TODO cache this
        url = UrlMgr({'url': 'http://www.eliteanimes.com', 'cache_writeonly':False, 'encoding':'Latin-1'})
        url.data
        for cookie in url.pointer.cookies:
            if cookie.find('cDRGN') >= 0:
                self.cookies = ['cDRGN'+textextract(cookie, 'cDRGN', ';')]
                break
        else:
            self.log.error("no cookie -> this means mostly a captcha")
            checkPage(url)

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
        url = unicode(url).encode('Latin-1')
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies, 'encoding':'Latin-1'})
        url = self.checkPage(url)

        start = clock()
        name = textextract(url.data, '<title>Anime Stream ', ' - German Sub / German Dub Animestreams</title>')
        media = Page.getMedia(self, name, link)
        if not media:
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
            if alternativePart.pinfo:
                alternativePart.pinfo.url_handle.cookies = self.cookies

        url = link.replace('stream', 'details')
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies, 'encoding':'Latin-1'})
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
            if content.find('Noch nichts eingetragen') > 0:
                return None
            return content

        year = getDetailContent(url.data, 'Jahr')
        if year:
            tmp = re.search(".*([0-9][0-9][0-9][0-9]).*", year)
            if tmp:
                media.year = int(tmp.group(1))

        for name in ("Zielgruppe", "Setting", "Genre"):
            content = getDetailContent(url.data, name)
            if content:
                tags = textextractall(content, '"><strong> ', ' </strong>')
                media.addTags(tags)

        return media

urlPart = 'eliteanimes.com' # this part will be matched in __init__ to create following class
classRef = EliteAnimes
