from tools.page import Page, log, Language
from tools.extension import Extension
from tools.stream import extract_stream
from tools.url import UrlMgr
from tools.helper import textextract, textextractall
import re
import json

class Kinox(Page):
    def __init__(self):
        self.name = 'kinox.to'
        self.url = 'http://kinox.to'
        Page.__init__(self)

    def getAllPages(self, link):
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

        extractLinks = {} # a map cause we want uniqueness and also store additional data

        for pageType in pageTypes:
            # url = self.checkPage(UrlMgr({'url':'http://kinox.to/'+pageType+'.html'}), pageTypeToCountSearch[pageType])
            lastData = None
            # there is a bug, when letter=='' it should retrieve all.. but the bug makes that only the firs 3000 entries are retrieved and then the first 25 entries are repeated until the end
            # but the "all" page is still needed for non-alpanumeric character
            for letter in ('','1','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'):
                log.info('Letter:%s', letter)
                i = 0
                maxItems = 0
                while True:
                    if letter == '' and i > 200: # last time I looked there were 55 non-alphanum entries
                        break
                    log.info("page %d", i)
                    link = ['http://kinox.to/aGET/List/?sEcho=2&iColumns=7&sColumns=&iDisplayStart='+str(i),
                        '&iDisplayLength=25',
                        '&iSortingCols=1',
                        '&iSortCol_0=2',
                        '&sSortDir_0=asc',
                        # '&bSortable_0=true',
                        # '&bSortable_1=true',
                        # '&bSortable_2=true',
                        # '&bSortable_3=false',
                        # '&bSortable_4=false',
                        # '&bSortable_5=false',
                        # '&bSortable_6=true',
                        '&additional=%7B%22fType%22%3A%22'+pageTypeToParam[pageType]+'%22%2C%22fLetter%22%3A%22'+letter+'%22%7D']
                    link = ''.join(link)

                    url = self.checkPage(UrlMgr({'url':link}), 'aaData')
                    if not url:
                        log.error("Connection problem ignore this one")
                        continue

                    data = json.loads(url.data)
                    if data == lastData:
                        log.info(link)
                        log.info(data)
                        raise Exception("Got 2 times the same data")
                    lastData = data
                    maxItems = int(data['iTotalDisplayRecords'])

                    for item in data['aaData']:
                        lang = item[0] # 1=ger, 2=eng, 15=ger/eng 'http://kinox.to//gr/sys/lng/'+lang+'.png'
                        # cat = item[1]
                        streamData = item[2]
                        # unk1 = item[3]
                        # unk2 = item[4]
                        # unk3 = item[5]
                        # unk4 = item[6]
                        streamLink = 'http://kinox.to'+textextract(streamData, 'href="', '"')
                        extractLinks[streamLink] = {'lang':lang, 'tags':pageTypeToTag[pageType]}
                    if i >= maxItems:
                        break
                    i+=25

        # we have to sort the keys else each access to the script will run in random order
        links = extractLinks.keys()
        links.sort()
        i = 0
        for link in links:
            i+=1
            media = self.extract(link)
            if media:
                log.info('link %d of %d', i, len(extractLinks))
                data = extractLinks[link]
                lang = data['lang']
                tags = data['tags']
                allPages.append(media)
                media.addTags(tags)
                for part in media.getSubs():
                    for alternative in part.getSubs():
                        langs = getLanguage(int(lang))
                        if len(langs) > 0 and alternative.subtitle:
                            try:
                                langs.remove(alternative.subtitle)
                            except Exception:
                                pass
                        alternative.language = getLanguage(int(lang))[0]

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
                        return None
        return url

    def extract(self, link):
        if not self.beforeExtract():
            return None

        url = self.checkPage(UrlMgr({'url': link}), ' Stream online anschauen und downloaden auf Kino</title>')
        if not url:
            return None

        name = textextract(url.data, '<title>', ' Stream online anschauen und downloaden auf Kino</title>')
        if not name:
            return None
        name = unicode(name, 'utf-8')
        try:
            year = int(name[-5:-1])
        except ValueError:
            year = 0
            log.error("couldn't exctract year from '%s'", name)
        name = name[:-7]

        subtitle = None
        if name.find('subbed') > 0:
            titleToLang = {
                '*english subbed*':'English',
                '*german subbed*':'German',
            }
            for i in titleToLang:
                if name.find(i) > 0:
                    subtitle = Language(titleToLang[i])
                    name = name.replace(i, '').rstrip()
                    break

        media = Page.getMedia(self, name, link)
        media.year = year
        if not media:
            return None
        log.info("Extract: %s", name)


        genre = textextract(url.data, "<td class=\"Label\" nowrap>Genre:</td>\t<td class=\"Value\">", '</td>')
        if genre:
            tags = textextractall(genre, '>', '</a>')
            media.addTags(tags)
        # #RelativesBlock if translated title is also in db


        seasonSelect = textextract(url.data , '<select size="1" id="SeasonSelection"', '</select')
        if seasonSelect:
            getUrl = 'http://kinox.to/aGET/MirrorByEpisode/'+textextract(seasonSelect, 'rel="', '"')
            seasons = textextractall(seasonSelect, 'value="', '"')
            for season in seasons:
                episodes = textextract(seasonSelect, 'value="'+season+'" rel="', '"').split(',')
                if len(seasons) > 1:
                    log.info('%s/%s with %s episodes', name, seasons[-1], episodes[-1])
                if episodes[-1] == '0':
                    log.info("--> don't look at this cause of 0 episodes")
                    continue
                for episode in episodes:
                    log.debug("%s Episode: %s", name, episode)
                    part = media.createSub()
                    part.num = int(episode)
                    if int(season) > 1 or len(seasons) > 0:
                        part.season = season
                    part.name = media.name
                    url = UrlMgr({'url':getUrl+'&Season='+season+'&Episode='+episode})
                    if url.data == '':
                        log.warning("%s Episode: %s has no data", name, episode)
                        continue
                    url = self.checkPage(url, 'HosterList')
                    if not url:
                        continue
                    for alternative in self.getAlternatives(url.data, part, subtitle):
                        pass
        else:
            part = media.createSub()
            part.name = media.name
            for alternative in self.getAlternatives(url.data, part, subtitle):
                pass
        return self.afterExtract(media)

    def createAlternativeParts(self, data, alternative, isLeaf = False):
        data = json.loads(data)
        data = data['Stream']
        streamLink = textextract(data, 'href="', '"')
        if not streamLink:
            streamLink = extract_stream(data)
            if not streamLink and not streamLink['url']:
                log.error("cant extract stream from kinox")
                log.error(data)
            streamLink = streamLink['url']
        if not streamLink:
            return
        altPart = alternative.createSub()
        currentPart = textextract(data, 'class="Partrun">Part ', '</a>')
        if currentPart != None:
            altPart.num = currentPart
            if isLeaf == False:
                otherParts = textextractall(data, '<a rel="', '</a>')
                for i in otherParts:
                    if i.find('Partrun') != -1:
                        continue
                    link = 'http://kinox.to/aGET/Mirror/'+textextract(i, '', '"').replace('amp;', '')
                    url = self.checkPage(UrlMgr({'url':link}), 'HosterName')
                    if not url:
                        return None
                    self.createAlternativeParts(url.data, alternative, True)
        if streamLink.startswith('/Out/?s='):
            streamLink = streamLink[8:]
        if streamLink.startswith('[url='):
            streamLink = textextract(streamLink, '[url=', '[/url]')
        altPart.url = streamLink

    def createAlternative(self, part, link, subtitle):
        url = self.checkPage(UrlMgr({'url':link}), 'HosterName')
        if not url:
            return None
        alternative = part.createSub()
        alternative.subtitle = subtitle
        self.createAlternativeParts(url.data, alternative)
        return alternative

    def getAlternatives(self, data, part, subtitle):
        hosterList = textextract(data , '<ul id="HosterList" ', '</ul>')
        if not hosterList:
            log.error("no hosterList")
            return
        streams = textextractall(hosterList, '<li id', '</li>')
        for stream in streams:
            url = textextract(stream, 'rel="', '"')
            mirrors = textextract(stream, '<b>Mirror</b>: ', '<br />')
            if mirrors:
                maxMirror = int(textextract(mirrors, '/', ''))
                urls = []
                url = re.sub(r'(&amp;)?Mirror=[0-9]+', '', url) # replace Mirror=123 when exists in original url
                for i in range(1, maxMirror+1):
                    urls.append(url+'&amp;Mirror='+str(i))
            else:
                urls = [url]
            for url in urls:
                yield self.createAlternative(part, 'http://kinox.to/aGET/Mirror/'+url.replace('amp;', ''), subtitle)


def getLanguage(id):
    langMap = {
        0: ['Unknown'],
        1: ['German'],
        2: ['English'],
        4: ['Chinese'],
        5: ['Spanish'],
        6: ['French'],
        7: ['Turkish'],
        8: ['Japanese'],
        11:['Italian'],
        15:['German', 'English'],
        16:['Dutch'],
        17:['Korean'],
        24:['Greek'],
        25:['Russian'],
        26:['Hindi'],
    }
    ret = []
    for i in langMap[id]:
        ret.append(Language(i))
    return ret

baseRegex = '^(http://)?(www\.)?kinox\.to'
class SingleKinoxExtension(Kinox, Extension):
    eregex = baseRegex+'/Stream/.*\.html$'
    ename = 'Kinox_s'
    def get(self, link):
        return Kinox.extract(self, link)

class AllKinoxExtension(Kinox, Extension):
    eregex = '('+baseRegex+'/?$)|('+baseRegex+'/(Movies|Documentations|Series|)\.html)|(^kinox$)'
    ename = 'Kinox_a'
    def get(self, link):
        return Kinox.getAllPages(self, link)
