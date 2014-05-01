from tools.page import Page, log, Language
from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import textextract, textextractall
from lxml import html
import re

class EliteAnimes(Page):
    def __init__(self):
        self.name = 'Eliteanimes'
        self.url = 'http://www.eliteanimes.com'
        Page.__init__(self)

    def checkPage(self, url):
        if url.data.find('<title>How to Enable Cookies</title>') > 0:
            # reconnect and set cookie through it
            url.clear_connection()
            url.setCacheWriteOnly()
        else:
            imgUrl = textextract(url.data, 'src="/captcha/?rnd=', '"')
            if imgUrl:
                url.clear_connection()
                url.setCacheWriteOnly()
                imgUrl = textextract(url.data, 'src="/captcha/?rnd=', '"')
                if imgUrl:
                    log.error("as i said.. a captcha")
                    log.error("please visit http://www.eliteanimes.com/ and enter the captcha and you won't be bothered again")
                    # TODO crack this captcha and return a new url object
                    imgUrl = 'http://www.eliteanimes.com/captcha/?rnd='+imgUrl
                    url = UrlMgr(url=imgUrl, cache_writeonly=True)
                    import sys
                    sys.exit()
        return url

    def getAllPages(self, link):
        allPages = []
        import string
        for pageType in string.uppercase:
            url = UrlMgr(url='http://www.eliteanimes.com/anime/list/'+pageType+'/')
            url = self.checkPage(url)
            log.info("Get all pages from '%s'", pageType)

            root = html.fromstring(url.data)
            for row in root.iterfind(".//td[@class='xhead bold']"):
                mediaA = row.find("a")
                if mediaA == None:
                    continue
                mediaUrl = 'http://www.eliteanimes.com/'+mediaA.get("href")
                media = self.extract(mediaUrl)
                if media:
                    log.info("finished page '%s'", media.name)
                    allPages.append(media)
        return allPages

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = link.replace('details', 'stream')
        url = url
        url = self.checkPage(UrlMgr(url=url))
        url = self.checkPage(url)

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
            title = streamA.text.strip()
            part = media.createSub()
            part.num = "%03d"%num
            part.name = title
            alternative = part.createSub()
            alternative.subtitle = Language('German')
            alternative.language = Language('German')
            alternativePart = alternative.createSub()
            alternativePart.url = streamLink

        url = link.replace('stream', 'details')
        url = UrlMgr(url=url)
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

        return self.afterExtract(media)

# TODO improve regex
baseRegex = '^(http://)?(www\.)?eliteanimes\.com'
class SingleEliteAnimesExtension(EliteAnimes, Extension):
    eregex = baseRegex+'/.+$'
    ename = 'EliteAnimes_s'
    def get(self, link):
        return EliteAnimes.extract(self, link)

class AllEliteAnimesExtension(EliteAnimes, Extension):
    eregex = baseRegex+'$'
    ename = 'EliteAnimes_a'
    def get(self, link):
        return EliteAnimes.getAllPages(self, link)
