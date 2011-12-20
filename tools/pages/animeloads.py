from tools.page import *
from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re

class AnimeLoads(Page):
    def __init__(self):
        self.cookies = ['hentai=aktiviert']
        self.name = 'anime-loads'
        self.url = 'http://www.anime-loads.org'
        Page.__init__(self)

    def getAllPages(self, link):
        allPages = []
        pageTypeToTag = {
            'serie': ['serie', 'anime'],
            'movie': ['movie', 'anime'],
            'ova': ['anime'],
            'asia': ['movie', 'asia']
        }
        for pageType in ('serie', 'movie', 'ova', 'asia'):
            url = UrlMgr({'url': 'http://www.anime-loads.org/media/'+pageType+'/ALL', 'cookies': self.cookies})
            root = html.fromstring(url.data)
            lastPageA = root.find(".//a[@class='pg_last']")
            lastPage = textextract(lastPageA.get('href'), 'ALL/', '')
            log.info("Get all pages from '"+pageType+"' with "+lastPage+" pages.")
            for pageNum in range(1, int(lastPage)+1):
                log.info("page "+str(pageNum))
                url = UrlMgr({'url': 'http://www.anime-loads.org/media/'+pageType+'/ALL/'+str(pageNum), 'cookies': self.cookies})
                root = html.fromstring(url.data)

                for row in root.iterfind(".//tr[@class='mediaitem itm']"):
                    curCol = 0
                    for column in row.iterfind("td"):
                        curCol += 1
                        if curCol == 1:
                            tmp = textextract(etree.tostring(column), 'src="', '"')
                            if tmp.find('http:') == 0:
                                img = tmp
                            else:
                                img = 'http://www.anime-loads.org/'+tmp
                        elif curCol == 2:
                            mediaUrl = textextract(etree.tostring(column), 'href="', '"')
                            break
                    media = self.extract(mediaUrl)
                    if media:
                        media.img = img
                        media.addTags(pageTypeToTag[pageType])
                        log.info("finished page '"+media.name+"'")
                        allPages.append(media)
        return allPages

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = UrlMgr({'url': link, 'cookies': self.cookies})
        name = unicode(textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>'), 'utf-8')
        media = Page.getMedia(self, name, link)
        if not media:
            return None

        root = html.fromstring(url.data)
        try:
            listTable = root.get_element_by_id('partlist')
        except:
            log.error("no partlist table inside data")
            log.error(link)
            log.error(url.data)
            return None
        for row in listTable.iterfind(".//tr[@class='link']"):
            part = media.createSub()
            curCol = 0
            for column in row.iterfind("td"):
                curCol += 1
                if curCol == 1:
                    part.num = column.text
                elif curCol == 2:
                    part.name = column.text
                elif curCol == 5: # download links
                    pass
                elif curCol == 6: # stream links
                    dlTable = column.find(".//table[@class='dltable']")
                    if dlTable == None:
                        dlTable = column.find(".//table[@class='list']")
                        if dlTable == None:
                            log.error("no downloadtable in "+link)
                            continue
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        alternative = part.createSub()
                        streamCurCol = 0
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            if streamCurCol == 1:
                                streamColumnString = etree.tostring(streamColumn)
                                tmp = re.search("hoster/(.*?)\.png", streamColumnString)
                                if tmp:
                                    alternative.hoster = tmp.group(1)
                                alternativePart = alternative.createSub()
                                redirectUrl = re.search("a href=\"(.*?)\"", streamColumnString)
                                if redirectUrl:
                                    redirectUrl = UrlMgr({'url': redirectUrl.group(1), 'cookies': self.cookies})
                                    realUrl = re.search("http-equiv=\"refresh\" content=\".;URL=(.*?)\"", redirectUrl.data)
                                    if realUrl:
                                        realUrl = realUrl.group(1)
                                        if not realUrl.startswith('http'):
                                            if realUrl.startswith('ttp'):
                                                realUrl = 'h'+realUrl
                                            else:
                                                # no url found
                                                continue
                                        alternativePart.url = realUrl
                            if streamCurCol == 2:
                                # there can exist multiple langs but i take just one
                                lang = re.search("lang/(..)\.png", etree.tostring(streamColumn))
                                if lang:
                                    lang = lang.group(1)
                                alternative.language = getLanguage(lang, 'de')
                            if streamCurCol == 3:
                                # there can exist multiple langs but i take just one
                                lang = re.search("lang/(..)\.png", etree.tostring(streamColumn))
                                if lang:
                                    lang = lang.group(1)
                                alternative.subtitle = getLanguage(lang)
                            if streamCurCol == 4:
                                alternativePart.size = streamColumn.text

                        self.setPinfo(alternativePart)
        tags = []
        for i in ('Zielgruppe', 'Genres'):
            newTags = textextract(url.data, '<dt>'+i+'</dt>', '</dd>')
            if newTags:
                newTags = textextract(newTags, '<dd>', '')
                newTags = newTags.split(', ')
                tags.extend(newTags)
        year = textextract(url.data, '<dt>Jahr</dt>', '</dd>')
        try:
            year = textextract(year, '<dd>', '')
            media.year = int(year[:4])
        except:
            log.warning("Problem with year on "+link)
        media.addTags(tags)
        return media


def getLanguage(name, default=None):
    mapping = {
        'ja': 'Japanese',
        'de': 'German',
        'en': 'English',
        'fr': 'French',
        'ru': 'Russian',
        'cn': 'Chinese',
        'kr': 'Korean',
        None: 'Unknown',
    }
    if name is None:
        name = default
    return Language.getLanguage(mapping[name])
def getLanguages(names):
    ret = []
    for i in names:
        ret.append(getLanguage(i))
    return ret


baseRegex = '^(http://)?(www\.)?anime-loads\.org'
class SingleAnimeLoadsExtension(AnimeLoads, Extension):
    eregex = baseRegex+'/media/[0-9]+$'
    ename = 'animeloads_s'
    def extract(self, link):
        AnimeLoads.extract(self, link)

class AllAnimeLoadsExtension(AnimeLoads, Extension):
    eregex = '('+baseRegex+'/?$)|('+baseRegex+'/media/(serie|movie|ova|asia)/?)|(^anime-loads$)'
    ename = 'animeloads_a'
    def extract(self, link):
        AnimeLoads.getAllPages(self, link)
