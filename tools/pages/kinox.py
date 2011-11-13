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
        pageTypes = (
            'Series',
            'Documentations',
            'Movies',
        )
        pageTypeToTag = {
            'Series': ['serie'],
            'Documentations': ['documentation'],
            'Movies': ['movie'],
        }
        pageTypeToParam = {
            'Series':'series',
            'Documentations':'documentations',
            'Movies':'movie',
        }
        pageTypeToCountSearch = {
            'Series': 'Serien</span><span class="Count">',
            'Documentations': '<span>Dokus</span><span class="Count">',
            'Movies': '<span>Filme</span><span class="Count">',
        }
        for pageType in pageTypes:
            url = self.checkPage(UrlMgr({'url':'http://kinox.to/'+pageType+'.html', 'log':log}), pageTypeToCountSearch[pageType])
            maxItems = int(textextract(url.data, pageTypeToCountSearch[pageType], '</span>'))
            log.error("maxItems %d" % maxItems)
            for i in range(0, maxItems, 25):
                log.error(i)
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
                try:
                    url = self.checkPage(UrlMgr({'url':link, 'log':log}), 'aaData')
                except:
                    import time
                    self.log.error("Connection reset: sleeping 4 seconds")
                    time.sleep(4)
                    url.clear_connection()
                    url.setCacheWriteOnly()
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
                    media = self.extract(streamLink)
                    if media:
                        allPages.append(media)
        return allPages

    def checkPage(self, url, part):
        if not url.data.find(part) > 0:
            url.clear_connection()
            url.setCacheWriteOnly()
            if not url.data.find(part) > 0:
                self.log.error('download problem?')
                url.clear_connection()
                url.setCacheWriteOnly()
                if not url.data.find(part) > 0:
                    import time
                    self.log.error("sleeping 10 seconds")
                    time.sleep(10)
                    url.clear_connection()
                    url.setCacheWriteOnly()
                    if not url.data.find(part) > 0:
                        self.log.error('download problem!')
                        url.clearCache()
                        self.log.error(url.url)
                        self.log.error(url.data)
        return url

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = self.checkPage(UrlMgr({'url': link, 'log': self.log}), ' Stream online anschauen und downloaden auf Kino</title>')
        origName = textextract(url.data, '<title>', ' Stream online anschauen und downloaden auf Kino</title>')
        if not origName:
            return None
        origName = unicode(origName, 'utf-8')
        log.info("Extract: "+origName)
        name = origName

        def createAltPart(self, part, link):
            url = self.checkPage(UrlMgr({'url':link, 'log':self.log}), 'HosterName')
            try:
                data = json.loads(url.data)
            except:
                log.error("no json")
                log.error(url.data)
                return None
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
            if not config.extract_all:
                self.setPinfo(altPart)

        seasonSelect = textextract(url.data , '<select size="1" id="SeasonSelection"', '</select')
        if seasonSelect:
            getUrl = 'http://kinox.to/aGET/MirrorByEpisode/'+textextract(seasonSelect, 'rel="', '"')
            seasons = textextractall(seasonSelect, 'value="', '"')
            for season in seasons:
                episodes = textextract(seasonSelect, 'value="'+season+'" rel="', '"').split(',')
                if len(seasons) > 1:
                    name = origName
                    name += " "+season
                    log.info(name+"/"+seasons[-1]+" with %s episodes " % episodes[-1])
                if episodes[-1] == '0':
                    log.info("--> don't look at this cause of 0 episodes")
                    continue
                media = Page.getMedia(self, name, link)
                if not media:
                    continue
                for episode in episodes:
                    log.debug(name+" Episode: "+episode)
                    part = media.createSub()
                    part.num = "%03d"%int(episode)
                    url = UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode, 'log':self.log})
                    if url.data == '':
                        log.warning(name+" Episode: "+episode+" has no data")
                        continue
                    url = self.checkPage(url, 'HosterList')
                    # todo alternatives for streams can be found with <b>Mirror</b>: 1/2<br 
                    streams = textextractall(url.data, 'rel="', '"')
                    for stream in streams:
                        createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        hosterList = textextract(url.data , '<ul id="HosterList" ', '</ul>')
        if hosterList:
            media = Page.getMedia(self, origName, link)
            if not media:
                return None
            part = media.createSub()
            part.name = media.name
            streams = textextractall(hosterList, 'rel="', '"')
            for stream in streams:
                createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        return media

urlPart = 'kinox.to' # this part will be matched in __init__ to create following class
classRef = Kinox
