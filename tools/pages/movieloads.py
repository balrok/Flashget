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
        self.pages_init__()

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log})

        try:
            media = Media(textextract(url.data, '<title>',' - Movie-Loads.NET</title>'))
        except:
            self.log.error('couldn\'t extract name, wrong url or html has changed')
            return None

        root = html.fromstring(url.data)
        part = media.createSub()
        part.name = media.name
        if root.find(".//div[@class='boxstream']") is None:
            self.log.error('No stream download found')
            return None
        for box in root.iterfind(".//div[@class='boxstream']"):
            curCol = 0

            # TODO we would need alternatives below alternatives..
            # alternative:level1 has codec/audio.. whatever information
            # alternative:level2 has the actual streems inside
            for streamBlock in box.iterfind(".//a[@rel='#overlay']"):
                alternative = part.createSub()
                alternative.name = box.find("h2").text_content()

                tmp = re.findall("language/(.*?)\.gif", etree.tostring(streamBlock))
                if len(tmp) > 0:
                    alternative.audio = tmp[0]
                tmp = re.findall("img/stream_(.*?)\.png", etree.tostring(streamBlock))
                if len(tmp) > 0:
                    alternative.hoster = tmp[0]


                streamUrl = 'http://www.movie-loads.net/'+streamBlock.get('href')
                url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
                dlUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')

                # multiple parts possible: v id="navi_parts"><ul><li><a href="#" onclick="update('streamframe.php?v=102256&part=1');" class="active" id="part_selected">PART 1</a></li><li><a href="#"
                # onclick="update('streamframe.php?v=102256&part=2');">PART 2</a></li
                url = UrlMgr({'url': dlUrl, 'log': self.log, 'cache_writeonly':True})
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
        url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
        streamUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
        alternativePart.url = streamUrl
        if num:
            alternativePart.num = num
        self.setPinfo(alternativePart)
        return alternativePart

urlPart = 'movie-loads' # this part will be matched in __init__ to create following class
classRef = MovieLoads
