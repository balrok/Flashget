from tools.page import *
from tools.stream import extract_stream
from tools.streams.animeloads import AnimeLoadsStream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class MovieLoads(Page):
    stream_extract = AnimeLoadsStream

    def __init__(self):
        self.pages_init__()

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log})

        try:
            media = Media(textextract(url.data, '<title>',' - Movie-Loads.NET</title>'))
        except:
            self.log.error('couldn\'t extract name, wrong url or html has changed')
            return None

        root = html.fromstring(url.data)
        part = Part()
        part.name = media.name
        if root.find(".//div[@class='boxstream']") is None:
            self.log.error('No stream download found')
            return None
        for box in root.iterfind(".//div[@class='boxstream']"):
            curCol = 0
            alternative = Alternative()
            alternative.name = box.find("h2").text_content()

            streamBlock = box.find(".//a[@rel='#overlay']") # normally there are multiple streams.. but cause they are from videobb and videozer it makes no sense

            alternative.audio = re.findall("language/(.*?)\.gif", etree.tostring(streamBlock))
            alternative.hoster = re.findall("img/stream_(.*?)\.png", etree.tostring(streamBlock))

            alternativePart = AlternativePart()
            streamUrl = 'http://www.movie-loads.net/'+streamBlock.get('href')
            url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
            streamUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
            realUrl = streamUrl
            url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})

            # multiple parts possible: v id="navi_parts"><ul><li><a href="#" onclick="update('streamframe.php?v=102256&part=1');" class="active" id="part_selected">PART 1</a></li><li><a href="#"
            # onclick="update('streamframe.php?v=102256&part=2');">PART 2</a></li
            root = html.fromstring(url.data)
            try:
                otherParts = root.get_element_by_id('navi_parts')
                log.error(otherParts.text_content())
            except:
                otherParts = False


            alternativePart.url = realUrl
            pinfo = self.stream_extract(realUrl, self.log)
            pinfo.name = media.name
            pinfo.title = part.name
            if otherParts:
                alternativePart.num = 1
                pinfo.title = str(alternativePart.num)+'_'+pinfo.title
            self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
            alternativePart.pinfo = pinfo
            alternative.alternativeParts.append(alternativePart)

            if otherParts:
                count = 1
                for opart in otherParts.iterfind(".//a"):
                    if opart.get('class') == 'active':
                        continue
                    count+=1
                    alternativePart = AlternativePart()
                    streamUrl = 'http://www.movie-loads.net/'+textextract(opart.get('onclick'), "('", "')")
                    realUrl = streamUrl

                    alternativePart.url = realUrl
                    pinfo = self.stream_extract(realUrl, self.log)
                    pinfo.name = self.data['name']
                    alternativePart.num = count
                    pinfo.title = str(alternativePart.num)+'_'+media.name
                    self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
                    alternativePart.pinfo = pinfo
                    alternative.alternativeParts.append(alternativePart)
            part.alternatives.append(alternative)
        media.parts.append(part)
        return media

urlPart = 'movie-loads' # this part will be matched in __init__ to create following class
classRef = MovieLoads
