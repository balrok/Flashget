from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class AnimeSeed(Page):
    def __init__(self):
        self.name = 'animeseed'
        self.url = 'http://animeseed.com'
        Page.__init__(self)

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = UrlMgr({'url': link, 'log': self.log})

        root = html.fromstring(url.data)
        name = root.find(".//a[@rel='bookmark']").get("title")
        media = Page.getMedia(self, name, link)

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
