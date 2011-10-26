from tools.page import *
from tools.streams.animeloads import AnimeLoadsStream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re

class AnimeLoads(Page):
    stream_extract = AnimeLoadsStream
    movie_types    = ['movies', 'ovas', 'asia', 'serien']

    def __init__(self, log):
        self.pages_init__(log)
        self.cookies = ['hentai=aktiviert']

    def extract_url(self, url, type = Page.TYPE_UNK):
        url = UrlMgr({'url': url, 'log': self.log, 'cookies': self.cookies})

        try:
            self.tmpName = glob_name = textextract(textextract(url.data, '<h2>','</h2>'), ' :: ', '</span>')
        except:
            self.log.error('couldn\'t extract name, dumping content...')
            self.log.error(url.data)
            import sys
            sys.exit(1)

        root = html.fromstring(url.data)
        listTable = root.get_element_by_id('partlist')
        if listTable == None:
            pass # throw error
        self.tmp = []
        links = []
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
                    for streamRow in dlTable.iterfind(".//tr[@class='medialink']"):
                        streamData = {}
                        streamCurCol = 0
                        streamLinks = []
                        for streamColumn in streamRow.iterfind("td"):
                            streamCurCol += 1
                            if streamCurCol == 1:
                                streamColumnString = etree.tostring(streamColumn)
                                streamData['hoster'] = re.search("hoster/(.*?)\.png", streamColumnString)
                                if streamData['hoster']:
                                    streamData['hoster'] = streamData['hoster'].group(1)
                                streamData['redirectUrl'] = re.search("a href=\"(.*?)\"", streamColumnString)
                                if streamData['redirectUrl']:
                                    streamData['redirectUrl'] = streamData['redirectUrl'].group(1)
                                    redirectUrl = UrlMgr({'url': streamData['redirectUrl'], 'log': self.log, 'cookies': self.cookies})
                                    realUrl = re.search("http-equiv=\"refresh\" content=\".;URL=(.*?)\"", redirectUrl.data)
                                    if realUrl:
                                        streamData['url'] = realUrl.group(1)
                                        streamLinks.append(realUrl.group(1))
                                    else:
                                        streamData['url'] = ''
                                        streamLinks.append('')
                            if streamCurCol == 2:
                                streamData['audio'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                            if streamCurCol == 3:
                                streamData['sub'] = re.findall("lang/(..)\.png", etree.tostring(streamColumn))
                    data['stream'] = streamData
                    links.append(streamLinks)
            self.tmp.append(data)
        i, list = self.add_streams(links)
        if list:
            container = VideoContainer(glob_name)
            container.list = list
            self.video_container.append(container)
            return container
        return None

    def links_handle(self, i, links):
        return self.tmp[i]['stream']['url']

    def name_handle(self, i, pinfo):
        pinfo.name = self.tmpName
        pinfo.title = self.tmp[i]['num'] +" "+self.tmp[i]['name']
