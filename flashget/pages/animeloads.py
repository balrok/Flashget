from flashget.page import Page, log
from flashget.extension import Extension
from flashget.url import UrlMgr
from flashget.helper import textextract
from lxml import html
from lxml import etree
import re

class AnimeLoads(Page, Extension):
    eregex = '.*anime-loads.org/media/.*'
    ename = 'anime-loads'

    name = 'anime-loads'
    url = 'http://anime-loads.org'

    def __init__(self, *args, **kwargs):
        self.cookies = {'hentai':'aktiviert'}
        super(AnimeLoads, self).__init__(*args, **kwargs)

    def get(self):
        link = self.link
        url = UrlMgr(url=link, cookies=self.cookies, encoding='utf-8')
        name = textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>')
        media = self.getMedia(name, link)

        if not media:
            return None

        season = 0

        # there is no season information on that page :/
        # look if it is a tvshow by that string and just assume a season
        if "Anime-Serie ::" in url.data:
            season = 1

        root = html.fromstring(url.data)
        try:
            listTable = root.get_element_by_id('partlist')
        except Exception: # TODO take a more specific exception
            log.error("no partlist table inside data")
            log.error(link)
            log.error(url.data)
            return None
        for row in listTable.iterfind(".//tr[@class='link']"):
            part = media.createSub()
            part.season = season
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
                    if dlTable is None:
                        dlTable = column.find(".//table[@class='list']")
                        if dlTable is None:
                            log.error("no downloadtable in %s", link)
                            continue
                    # they use streamCurCol == 4 with the content "Part 1", "Part 2" etc to name this
                    # but sometimes streamCurCol == 4 would be the size.. so it is quite complicated
                    hasMultipleParts = False
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        if hasMultipleParts:
                            rowString = etree.tostring(streamRow)
                            # create an alternative if that row has no "Part XYZ" inside it
                            # or if that row is Part1/Part 1
                            if rowString.find("Part") == -1 or rowString.find("Part 1") != -1 or rowString.find("Part1") != -1:
                                alternative = part.createSub()
                        else:
                            alternative = part.createSub()
                        streamCurCol = 0
                        hasMultipleParts = False
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            streamColumnString = etree.tostring(streamColumn)
                            if streamCurCol == 1:
                                tmp = re.search("hoster/(.*?)\.png", streamColumnString)
                                if tmp:
                                    hoster = tmp.group(1)
                                    alternative.hoster = hoster
                                alternativePart = alternative.createSub()
                                redirectUrl = re.search("a href=\"(.*?)\"", streamColumnString)
                                if redirectUrl:
                                    alternativePart.url = redirectUrl.group(1)
                                else:
                                    continue
                                flv_type = re.search('src="images/hoster/(.*?).png"', streamColumnString)
                                if flv_type:
                                    alternativePart.flv_type = flv_type.group(1)
                            if streamCurCol == 2:
                                # there can exist multiple langs but i take just one
                                lang = re.search("lang/(..)\.png", streamColumnString)
                                if lang:
                                    lang = lang.group(1)
                                alternative.language = getLanguage(lang, 'de')
                            if streamCurCol == 3:
                                # there can exist multiple langs but i take just one
                                lang = re.search("lang/(..)\.png", streamColumnString)
                                if lang:
                                    lang = lang.group(1)
                                alternative.subtitle = getLanguage(lang)
                            if streamCurCol == 4:
                                try:
                                    size = int(streamColumn.text)
                                except:
                                    if streamColumn.text[:4] == "Part":
                                        # with the next part 1 we will create a new alternative
                                        hasMultipleParts = True
                                    else:
                                        log.warning("This media file might have multiple parts but not sure: %s", streamColumn.text)
                                else:
                                    alternativePart.size = size

        tags = []
        for i in ('Zielgruppe', 'Genres'):
            newTags = textextract(url.data, '<dt>'+i+'</dt>', '</dd>')
            if newTags:
                newTags = textextract(newTags, '<dd>', '')
                newTags = newTags.split(', ')
                tags.extend(newTags)
        year = textextract(url.data, '<dt>Jahr</dt>', '</dd>')
        year = textextract(year, '<dd>', '')
        try:
            media.year = int(year[:4])
        except ValueError:
            log.warning("Problem with year in %s", link)
        media.addTags(tags)
        return self.afterExtract(media)


def getLanguage(name, default=None):
    if name is None:
        name = default
    return name
def getLanguages(names):
    ret = []
    for i in names:
        ret.append(getLanguage(i))
    return ret
