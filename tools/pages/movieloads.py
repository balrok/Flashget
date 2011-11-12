from tools.page import *
from tools.stream import extract_stream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class MovieLoads(Page):
    def __init__(self):
        self.name = 'movie-loads'
        self.url = 'http://www.movie-loads.net'
        Page.__init__(self)

    def getAllPages(self):
        allPages = []
        url = UrlMgr({'url': 'http://www.movie-loads.net/?movies', 'log': self.log})
        root = html.fromstring(url.data)
        lastPageContainer = root.get_element_by_id('navi_sub2')
        # get the last a link in this container
        lastPageA = lastPageContainer.findall(".//a")[-1]
        lastPage = textextract(lastPageA.get('href'), 'page=', '')
        self.log.info("Get all movies from "+lastPage+" pages.")
        for pageNum in range(1, int(lastPage)+1):
            self.log.info("page "+str(pageNum))
            url = UrlMgr({'url': 'http://www.movie-loads.net/?movies&page='+str(pageNum), 'log': self.log})
            root = html.fromstring(url.data)
            for movie in root.iterfind(".//div[@class='movie']"):
                mediaId = textextract(movie.find(".//a").get('href'), 'media=', '')
                mediaUrl = 'http://www.movie-loads.net/?media='+mediaId
                media = self.extract(mediaUrl)
                if media == None:
                    self.log.warning("couln't extract media")
                    continue
                media.img = 'http://www.movie-loads.net/cover/tn/'+mediaId+'.jpg'
                self.log.info("finished page '"+media.name+"'")
                allPages.append(media)
        return allPages

    def extract(self, link):
        url = UrlMgr({'url': link, 'log': self.log})

        name = unicode(textextract(url.data, '<title>',' - Movie-Loads.NET</title>'), 'utf-8')
        media = Page.getMedia(self, name, link)
        if not media:
            return None


        root = html.fromstring(url.data)
        part = media.createSub()
        part.name = media.name
        if root.find(".//div[@class='boxstream']") is None:
            self.log.error('No stream download found')
            return None


        def getDetailContent(data, name):
            content = textextract(data, '<td><span>'+name+':</span></td>', '</tr>')
            if not content:
                return None
            content = textextract(content, '<td>', '</td>')
            return content

        year = getDetailContent(url.data, 'Year')
        if year:
            tmp = re.search(".*([0-9][0-9][0-9][0-9]).*", year)
            if tmp:
                media.year = int(tmp.group(1))

        content = getDetailContent(url.data, 'Genre')
        if content:
            tags = textextractall(content, '>', '</a>')
            media.addTags(tags)
        content = getDetailContent(url.data, 'FSK')
        if content:
            media.addTag(content)
        media.addTag(self.name)



        for box in root.iterfind(".//div[@class='boxstream']"):
            curCol = 0

            for streamBlock in box.iterfind(".//a[@rel='#overlay']"):
                alternative = part.createSub()
                alternative.name = unicode(box.find("h2").text_content())

                tmp = re.search("language/(.*?)\.gif", etree.tostring(streamBlock))
                if tmp:
                    alternative.language = Language(tmp.group(1))
                else:
                    alternative.language = Language('German')
                tmp = re.findall("img/stream_(.*?)\.png", etree.tostring(streamBlock))
                if len(tmp) > 0:
                    alternative.hoster = tmp[0]


                streamUrl = 'http://www.movie-loads.net/'+streamBlock.get('href')

                def getDlUrl(self, streamUrl, writeOnly=False):
                    url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':writeOnly})
                    if url.data.find('Unerlaubter Scriptaufruf!') > 0:
                        log.error(1)
                        log.error(streamUrl)
                        import sys
                        sys.exit(1)
                    dlUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
                    return dlUrl

                dlUrl = getDlUrl(self, streamUrl)

                # multiple parts possible: v id="navi_parts"><ul><li><a href="#" onclick="update('streamframe.php?v=102256&part=1');" class="active" id="part_selected">PART 1</a></li><li><a href="#"
                # onclick="update('streamframe.php?v=102256&part=2');">PART 2</a></li
                url = UrlMgr({'url': dlUrl, 'log': self.log, 'cache_writeonly':False})

                if url.data.find('Unerlaubter Scriptaufruf!') > 0:
                    log.error(2)
                    dlUrl = getDlUrl(self, streamUrl, True)
                    url = UrlMgr({'url': dlUrl, 'log': self.log, 'cache_writeonly':True})
                    if url.data.find('Unerlaubter Scriptaufruf!') > 0:
                        log.error(3)
                        log.error("unexpected error")
                        import sys
                        sys.exit(1)
                root = html.fromstring(url.data)
                try:
                    otherParts = root.get_element_by_id('navi_parts')
                except:
                    otherParts = False

                count = 0
                if otherParts:
                    count = 1

                # we have to reextract this part cause that site invalidates each url after it got requested once
                alternativePart = self.getAlternativePart(streamUrl, alternative, count)

                if otherParts:
                    for opart in otherParts.iterfind(".//a"):
                        if opart.get('class') == 'active':
                            continue
                        count+=1
                        streamUrl = 'http://www.movie-loads.net/'+textextract(opart.get('onclick'), "('", "')")
                        alternativePart = self.getAlternativePart(streamUrl, alternative, num)
        return media

    def getAlternativePart(self, streamUrl, alternative, num):
        part = alternative.part
        media = part.media
        alternativePart = alternative.createSub()
        url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':False})
        streamUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
        if url.data.find('Unerlaubter Scriptaufruf!') > 0:
            log.error(4)
            import sys
            sys.exit(1)
        alternativePart.url = streamUrl
        if num:
            alternativePart.num = num
        self.setPinfo(alternativePart)
        return alternativePart

urlPart = 'movie-loads' # this part will be matched in __init__ to create following class
classRef = MovieLoads
