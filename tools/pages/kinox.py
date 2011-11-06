from tools.page import *
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys
import json

class Kinox(Page):
    def __init__(self):
        self.name = 'kinox.to'
        self.url = 'http://kinox.to'
        Page.__init__(self)

    def getAllPages(self):
        allPages = []
        return allPages

    def checkPage(self, url, part):
        if not url.data.find(part) > 0:
            url.clear_connection()
            url.setCacheWriteOnly()
            if not url.data.find(part) > 0:
                self.log.error('download problem?')
                self.log.error(url.url)
                self.log.error(url.data)
        return url

    def extract(self, link):
        url = self.checkPage(UrlMgr({'url': link, 'log': self.log}), 'Stream online')
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
                part = media.createSub()
                part.name = episode
                part.num = episode
                url = self.checkPage(UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode, 'log':self.log}), 'HosterList')
                streams = textextractall(url.data, 'rel="', '"')
                for stream in streams:
                    url = self.checkPage(UrlMgr({'url':'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''), 'log':self.log}), 'HosterName')
                    try:
                        data = json.loads(url.data)
                    except:
                        log.error("no json")
                    hoster = data['HosterName']
                    hosterHome = data['HosterHome']
                    streamLink = textextract(data['Stream'], 'href="', '"')
                    altPart = part.createSub().createSub()
                    altPart.url = streamLink
                    self.setPinfo(altPart)
        return media

urlPart = 'kinox.to' # this part will be matched in __init__ to create following class
classRef = Kinox
