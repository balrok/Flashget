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
    movie_types    = ['movies', 'ovas', 'asia', 'serien']

    def __init__(self):
        self.pages_init__()
        self.cookies = ['hentai=aktiviert']

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

        try:
            self.data['name'] = textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>')
        except:
            self.log.error('couldn\'t extract name, dumping content...')
            self.log.error(url.data)
            sys.exit(1)

        root = html.fromstring(url.data)
        listTable = root.get_element_by_id('partlist')
        if listTable == None:
            self.log.error("no partlist table inside data")
            self.log.error(url.data)
            sys.exit(1)
        for row in listTable.iterfind(".//tr[@class='link']"):
            data = {}
            curCol = 0
            for column in row.iterfind("td"):
                curCol += 1
                if curCol == 1:
                    data['num'] = column.text
                if curCol == 2:
                    data['name'] = column.text
                #if curCol == 3: not used cause we have it also per stream
                #    data['audio'] = re.findall("lang/(..)\.png", etree.tostring(column))
                #if curCol == 4:
                #    data['sub'] = re.findall("lang/(..)\.png", etree.tostring(column))
                if curCol == 5: # download links
                    pass
                if curCol == 6: # stream links
                    dlTable = column.find(".//table[@class='dltable']")
                    if dlTable == None:
                        print ERROR
                        continue
                    streams = []
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        streamData = {}
                        streamCurCol = 0
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            if streamCurCol == 1:
                                streamColumnString = etree.tostring(streamColumn)
                                streamData['hoster'] = re.search("hoster/(.*?)\.png", streamColumnString)
                                if streamData['hoster']:
                                    streamData['hoster'] = streamData['hoster'].group(1)
                                redirectUrl = re.search("a href=\"(.*?)\"", streamColumnString)
                                streamData['url'] = ''
                                if redirectUrl:
                                    redirectUrl = UrlMgr({'url': redirectUrl.group(1), 'log': self.log, 'cookies': self.cookies})
                                    realUrl = re.search("http-equiv=\"refresh\" content=\".;URL=(.*?)\"", redirectUrl.data)
                                    if realUrl:
                                        streamData['url'] = realUrl.group(1)
                            if streamCurCol == 2:
                                streamData['audio'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 3:
                                streamData['sub'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 4:
                                streamData['size'] = streamColumn.text

                        pinfo = self.stream_extract(streamData['url'], self)
                        pinfo.name = self.data['name']
                        pinfo.title = data['num'] +" "+ data['name']
                        self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
                        streamData['pinfo'] = pinfo
                        streams.append(streamData)
                    data['streams'] = streams
            self.parts.append(data)

urlPart = 'anime-loads' # this part will be matched in __init__ to create following class
classRef = AnimeLoads
