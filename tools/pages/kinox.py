from tools.page import *
from tools.stream import extract_stream
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
        pageTypeToTag = {
            'Series': ['serie'],
            'Documentations': ['documentation'],
        }
        pageTypeToParam = {
            'Series':'series',
            'Documentations':'documentations',
        }
        for pageType in ('Series', 'Documentations'):
            url = self.checkPage(UrlMgr({'url':'http://kinox.to/'+pageType+'.html', 'log':log}), 'span class="Count">')
            maxItems = int(textextract(url.data, 'span class="Count">', '</span>'))
            for i in range(0, maxItems, 25):
                link = ['http://kinox.to/aGET/List/?sEcho=2&iColumns=7&sColumns=&iDisplayStart='+str(i),
                    '&iDisplayLength=25',
                    '&iSortingCols=1',
                    '&iSortCol_0=2',
                    '&sSortDir_0=asc',
                    #'&bSortable_0=true',
                    #'&bSortable_1=true',
                    #'&bSortable_2=true',
                    #'&bSortable_3=false',
                    #'&bSortable_4=false',
                    #'&bSortable_5=false',
                    #'&bSortable_6=true',
                    '&additional=%7B%22fType%22%3A%22'+pageTypeToParam[pageType]+'%22%2C%22fLetter%22%3A%22%22%7D']
                link = ''.join(link)
                url = UrlMgr({'url':link, 'log':log})
                data = json.loads(url.data)
                for item in data['aaData']:
                    lang = item[0] # 1=ger, 2=eng, 15=ger/eng 'http://kinox.to//gr/sys/lng/'+lang+'.png'
                    cat = item[1]
                    streamData = item[2]
                    unk1 = item[3]
                    unk2 = item[4]
                    unk3 = item[5]
                    unk4 = item[6]
                    streamLink = 'http://kinox.to/'+textextract(streamData, 'href="', '"')
                    #media = self.extract(streamLink)
                    #allPages.append(media)
        return allPages

    def checkPage(self, url, part):
        if not url.data.find(part) > 0:
            url.clear_connection()
            url.setCacheWriteOnly()
            if not url.data.find(part) > 0:
                self.log.error('download problem?')
                import time
                self.log.error("sleeping 10 seconds")
                time.sleep(10)
                url.clear_connection()
                url.setCacheWriteOnly()
                if not url.data.find(part) > 0:
                    self.log.error('download problem!')
                    self.log.error(url.url)
                    self.log.error(url.data)
        return url

    def extract(self, link):
        url = self.checkPage(UrlMgr({'url': link, 'log': self.log}), 'Stream online')
        origName = textextract(url.data, '<title>', ' Stream online anschauen und downloaden auf Kino</title>')
        log.info("Extract: "+origName)
        name = origName
        if not origName:
            return None

        def createAltPart(self, part, link):
            url = self.checkPage(UrlMgr({'url':link, 'log':self.log}), 'HosterName')
            try:
                data = json.loads(url.data)
            except:
                log.error("no json")
                log.error(url.data)
            hoster = data['HosterName']
            hosterHome = data['HosterHome']
            streamLink = textextract(data['Stream'], 'href="', '"')
            if not streamLink:
                streamLink = extract_stream(data['Stream'])
                if not streamLink and not streamLink['url']:
                    log.error("cant extract stream from kinox")
                    log.error(data['Stream'])
                streamLink = streamLink['url']
            altPart = part.createSub().createSub()
            altPart.url = streamLink
            self.setPinfo(altPart)

        seasonSelect = textextract(url.data , '<select size="1" id="SeasonSelection"', '</select')
        if seasonSelect:
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
                    part.num = "%03d"%int(episode)
                    url = self.checkPage(UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode, 'log':self.log}), 'HosterList')
                    # todo alternatives for streams can be found with <b>Mirror</b>: 1/2<br 
                    streams = textextractall(url.data, 'rel="', '"')
                    for stream in streams:
                        createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        hosterList = textextract(url.data , '<ul id="HosterList" ', '</ul>')
        if hosterList:
            media = Page.getMedia(self, origName, link)
            part = media.createSub()
            part.name = media.name
            streams = textextractall(hosterList, 'rel="', '"')
            for stream in streams:
                createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        return media

urlPart = 'kinox.to' # this part will be matched in __init__ to create following class
classRef = Kinox
