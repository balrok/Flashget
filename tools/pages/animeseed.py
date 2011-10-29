from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class AnimeSeed(Page):
    def __init__(self):
        self.pages_init__()

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log})

        root = html.fromstring(url.data)
        try:
            media = Media(root.find(".//a[@rel='bookmark']").get("title"))
        except:
            self.log.error('couldn\'t extract name, wrong url or html has changed')
            return None

        # each link to a video contains episode..
        num = 0
        part = None
        for streamA in root.xpath(".//a[contains(@href,'/watch/')]"):
            streamLink = streamA.get('href')
            title = streamA.text
            # if we already have an episode but without dub, don't take the dubbed one
            if part and part.name+" DUB" == title:
                continue
            part = media.createSub()
            num += 1
            part.num = "%03d"%num
            part.name = title

            allStreamLinks = []
            allStreamLinks.append(streamLink)
            url = UrlMgr({'url': streamLink, 'log': self.log})
            root = html.fromstring(url.data)
            mirrorTable = root.get_element_by_id('mirror_table')
            for a in mirrorTable.iterfind('.//a'):
                allStreamLinks.append(a.get('href'))

            for streamLink in allStreamLinks:
                alternative = part.createSub()
                alternativePart = alternative.createSub()
                alternativePart.url = streamLink

                self.setPinfo(alternativePart)
        return media

urlPart = 'animeseed.com' # this part will be matched in __init__ to create following class
classRef = AnimeSeed
