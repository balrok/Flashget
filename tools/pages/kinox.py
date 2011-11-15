from tools.page import *
from tools.stream import extract_stream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys
try:
    import json
except:
    import simplejson as json

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
            'Documentations':'documentation',
            'Movies':'movie',
        }
        pageTypeToCountSearch = {
            'Series': 'Serien</span><span class="Count">',
            'Documentations': '<span>Dokus</span><span class="Count">',
            'Movies': '<span>Filme</span><span class="Count">',
        }
        for pageType in pageTypes:
            #url = self.checkPage(UrlMgr({'url':'http://kinox.to/'+pageType+'.html'}), pageTypeToCountSearch[pageType])
            #maxItems = int(textextract(url.data, pageTypeToCountSearch[pageType], '</span>'))
            lastData = None
            # there is a bug, when letter=='' it should retrieve all.. but the bug makes that only the firs 3000 entries are retrieved and then the first 25 entries are repeated until the end
            # but the "all" page is still needed for non-alpanumeric character
            for letter in ('','1','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'):
                log.info('Letter:'+letter)
                i = 0
                maxItems = 0
                while True:
                    if letter == '' and i > 200: # last time I looked there were 55 non-alphanum entries
                        break
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
                        '&additional=%7B%22fType%22%3A%22'+pageTypeToParam[pageType]+'%22%2C%22fLetter%22%3A%22'+letter+'%22%7D']
                    link = ''.join(link)
                    try:
                        url = UrlMgr({'url':link})
                        url = self.checkPage(url, 'aaData')
                    except:
                        import time
                        log.error("Connection reset: sleeping 4 seconds")
                        time.sleep(4)
                        url.clear_connection()
                        url.setCacheWriteOnly()
                    data = json.loads(url.data)
                    if data == lastData:
                        print link
                        print data
                        raise Exception("Got 2 times the same data")
                    lastData = data
                    maxItems = int(data['iTotalDisplayRecords'])

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
                            log.info(media.name)
                            allPages.append(media)
                            for part in media.getSubs():
                                for alternative in part.getSubs():
                                    alternative.language = getLanguage(int(lang))[0]
                    if i >= maxItems:
                        break
                    i+=25
        return allPages

    def checkPage(self, url, part):
        if not url.data.find(part) > 0:
            url.clear_connection()
            url.setCacheWriteOnly()
            if not url.data.find(part) > 0:
                log.error('download problem?')
                url.clear_connection()
                url.setCacheWriteOnly()
                if not url.data.find(part) > 0:
                    import time
                    log.error("sleeping 3 seconds")
                    time.sleep(3)
                    url.clear_connection()
                    url.setCacheWriteOnly()
                    if not url.data.find(part) > 0:
                        log.error('download problem!')
                        url.clearCache()
                        log.error(url.url)
                        log.error(url.data)
        return url

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = self.checkPage(UrlMgr({'url': link}), ' Stream online anschauen und downloaden auf Kino</title>')
        name = textextract(url.data, '<title>', ' Stream online anschauen und downloaden auf Kino</title>')
        if not name:
            return None
        year = int(name[-5:-1])
        name = unicode(name, 'utf-8')[:-7]
        media = Page.getMedia(self, name, link)
        media.year = year
        if not media:
            return None
        log.info("Extract: "+name)


        genre = textextract(url.data, '<td class="Label" nowrap>Genre:</td>   <td class="Value">', '</td>')
        if genre:
            tags = textextractall(genre, '>', '</a>')
            media.addTags(tags)
        # #RelativesBlock if translated title is also in db


        def createAltPart(self, part, link):
            url = self.checkPage(UrlMgr({'url':link}), 'HosterName')
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
                    log.info(name+"/"+seasons[-1]+" with %s episodes " % episodes[-1])
                if episodes[-1] == '0':
                    log.info("--> don't look at this cause of 0 episodes")
                    continue
                for episode in episodes:
                    log.debug(name+" Episode: "+episode)
                    part = media.createSub()
                    part.num = int(episode)
                    part.season = season
                    url = UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode})
                    if url.data == '':
                        log.warning(name+" Episode: "+episode+" has no data")
                        continue
                    url = self.checkPage(url, 'HosterList')
                    # todo alternatives for streams can be found with <b>Mirror</b>: 1/2<br 
                    streams = textextractall(url.data, 'rel="', '"')
                    for stream in streams:
                        createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        else:
            hosterList = textextract(url.data , '<ul id="HosterList" ', '</ul>')
            if hosterList:
                part = media.createSub()
                part.name = media.name
                streams = textextractall(hosterList, 'rel="', '"')
                for stream in streams:
                    createAltPart(self, part, 'http://kinox.to/aGET/Mirror/'+stream.replace('amp;', ''))
        return media

urlPart = 'kinox.to' # this part will be matched in __init__ to create following class
classRef = Kinox


def getLanguage(id):
    langMap = {
        1: ['German'],
        2: ['English'],
        4: ['Chinese'],
        5: ['Spanish'],
        6: ['French'],
        7: ['Turkish'],
        8: ['Japanese'],
        11:['Italian'],
        15:['German', 'English'],
        17:['Korean'],
        24:['Greek'],
        25:['Russian'],
        26:['Hindi'],
    }
    ret = []
    for i in langMap[id]:
        ret.append(Language(i))
    return ret
