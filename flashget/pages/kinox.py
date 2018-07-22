from flashget.page import Page, log
from flashget.stream import extract_stream
from flashget.url import UrlMgr
from flashget.helper import textextract, textextractall
import re
import json

class Kinox(Page):
    eregex = '^(https?://)?(www\.)?kinox\.to/.*'
    ename = 'anime-loads'

    name = 'kinox.to'
    url = 'http://kinox.to'

    def __init__(self):
        Page.__init__(self)

    def get(self):
        link = self.link
        allPages = []
        i = 0
        i+=1
        media = self.extract(link)
        return self.afterExtract(media)

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
        url = self.checkPage(UrlMgr(url=link), ' Stream   online anschauen und downloaden auf KinoX</title>')
        if not url:
            return None

        name = textextract(url.data, '<title>', ' Stream   online anschauen und downloaden auf KinoX</title>')
        if not name:
            return None
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
                    subtitle = getLanguage(titleToLang[i])
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
            seasons = list(textextractall(seasonSelect, 'value="', '"'))
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
                        part.season = int(season)
                    part.name = media.name
                    #url = UrlMgr(url=getUrl+'&Season='+season+'&Episode='+episode)
                    #if url.data == '':
                    #    log.warning("%s Episode: %s has no data", name, episode)
                    #    continue
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
            streamLink = textextract(data, 'src="', '"')
            #if not streamLink and not streamLink['url']:
            #    log.error("cant extract stream from kinox")
            #    log.error(data)
            #streamLink = streamLink['url']
        if not streamLink:
            log.error("no streamlink")
            return
        if streamLink.startswith("//"):
            streamLink = "https:" + streamLink
        print(streamLink)
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
                    url = self.checkPage(UrlMgr(url=link), 'HosterName')
                    if not url:
                        return None
                    self.createAlternativeParts(url.data, alternative, True)
        if streamLink.startswith('/Out/?s='):
            streamLink = streamLink[8:]
        if streamLink.startswith('[url='):
            streamLink = textextract(streamLink, '[url=', '[/url]')
        altPart.url = streamLink

    def createAlternative(self, part, link, subtitle):
        print(link)
        try:
            url = self.checkPage(UrlMgr(url=link), 'HosterName')
        except:
            import time
            time.sleep(5)
            return None
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
