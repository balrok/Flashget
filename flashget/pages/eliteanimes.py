from flashget.page import Page, log, Language
from flashget.extension import Extension
from flashget.url import UrlMgr
from flashget.helper import textextract, textextractall
from lxml import html
import re

class EliteAnimes(Page, Extension):
    eregex = '^(http://)?(www\.)?eliteanimes\.com/.+$'
    ename = 'EliteAnimes_s'

    name = 'Eliteanimes'
    url = 'http://www.eliteanimes.com'

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

    def get(self):
        link = self.link
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
