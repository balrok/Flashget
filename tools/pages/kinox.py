from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class Kinox(Page):
    def __init__(self):
        self.name = 'kinox.to'
        self.url = 'http://kinox.to'
        Page.__init__(self)

    def getAllPages(self):
        allPages = []
        return allPages

    def extract(self, link):
        url = UrlMgr({'url': link, 'log': self.log})
        origName = textextract(url.data, '<title>', ' Stream online anschauen und downloaden auf Kino</title>')
        name = origName
        if not origName:
            return None

        seasonSelect = textextract(url.data , '<select size="1" id="SeasonSelection"', '</select')
        getUrl = 'http://kinox.to/aGET/MirrorByEpisode/'+textextract(seasonSelect, 'rel="', '"')
        seasons = textextractall(seasonSelect, 'value="', '"')
        for season in seasons:
            if len(seasons) > 1:
                name = origName
                name += " "+season
            media = Page.getMedia(self, name, link)
            episodes = textextract(seasonSelect, 'value="'+season+'" rel="', '"').split(',')
            for episode in episodes:
                part = media.getSub()
                part.name = episode
                part.num = episode
                log.error(getUrl+'&Season='+season+'&Episode='+episode)
                url = UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode, 'log':self.log})
                streams = textextractall(url.data, 'rel="', '"')
                for stream in streams:


        return media

urlPart = 'kinox.to' # this part will be matched in __init__ to create following class
classRef = Kinox
