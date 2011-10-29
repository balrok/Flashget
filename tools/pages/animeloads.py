from tools.page import *
from tools.streams.animeloads import AnimeLoadsStream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class AnimeLoads(Page):
    stream_extract = AnimeLoadsStream

    def __init__(self):
        self.pages_init__()
        self.cookies = ['hentai=aktiviert']

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

        try:
            media = Media(textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>'))
        except:
            self.log.error('couldn\'t extract name, wrong url or html has changed')
            return None

        root = html.fromstring(url.data)
        try:
            listTable = root.get_element_by_id('partlist')
        except:
            self.log.error("no partlist table inside data")
            self.log.error(url.data)
            sys.exit(1)
        for row in listTable.iterfind(".//tr[@class='link']"):
            part = Part()
            curCol = 0
            for column in row.iterfind("td"):
                curCol += 1
                if curCol == 1:
                    part.num = column.text
                if curCol == 2:
                    part.name = column.text
                if curCol == 5: # download links
                    pass
                if curCol == 6: # stream links
                    dlTable = column.find(".//table[@class='dltable']")
                    if dlTable == None:
                        print ERROR
                        continue
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        alternative = Alternative()
                        streamCurCol = 0
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            if streamCurCol == 1:
                                streamColumnString = etree.tostring(streamColumn)
                                tmp = re.search("hoster/(.*?)\.png", streamColumnString)
                                if tmp:
                                    alternative.hoster = tmp.group(1)
                                alternativePart = AlternativePart()
                                redirectUrl = re.search("a href=\"(.*?)\"", streamColumnString)
                                if redirectUrl:
                                    redirectUrl = UrlMgr({'url': redirectUrl.group(1), 'log': self.log, 'cookies': self.cookies})
                                    realUrl = re.search("http-equiv=\"refresh\" content=\".;URL=(.*?)\"", redirectUrl.data)
                                    if realUrl:
                                        alternativePart.url = realUrl.group(1)
                                alternative.alternativeParts.append(alternativePart)
                            if streamCurCol == 2:
                                alternative.audio = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 3:
                                alternative.sub = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 4:
                                alternativePart.size = streamColumn.text

                        pinfo = self.stream_extract(alternativePart.url, self.log)
                        pinfo.name = media.name
                        pinfo.title = part.num + " " + part.name
                        self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
                        alternativePart.pinfo = pinfo
                        part.alternatives.append(alternative)
            media.parts.append(part)
        return media

urlPart = 'anime-loads' # this part will be matched in __init__ to create following class
classRef = AnimeLoads
