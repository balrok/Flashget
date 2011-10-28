from tools.page import *
from tools.streams.animeloads import AnimeLoadsStream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class AnimeSeed(Page):
    stream_extract = AnimeLoadsStream

    def __init__(self):
        self.pages_init__()



    #self.data= {'name':'..'}
    #self.parts = [
    #    {
    #        'name':'..',
    #        'streams':[
    #            {
    #                'url':'..',
    #                'pinfo':None
    #            }
    #        ]
    #    }
    #]
    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log})

        try:
            self.data['name'] = remove_html(textextract(url.data, '<title>', ' | AnimeSeed.Com</title>'))
        except:
            self.log.error('couldn\'t extract name, dumping content...')
            self.log.error(url.data)
            sys.exit(1)

        root = html.fromstring(url.data)
        # each link to a video contains episode..
        num = 0
        data = {}
        for streamA in root.xpath(".//a[contains(@href,'/watch/')]"):
            num += 1
            streamLink = streamA.get('href')
            title = streamA.text
            # if we already have an episode but without dub, don't take the dubbed one
            if data and data['name']+" DUB" == title:
                continue
            data = {}
            data['num'] = "%03d"%num
            data['name'] = title

            allStreamLinks = []
            allStreamLinks.append(streamLink)
            url = UrlMgr({'url': streamLink, 'log': self.log})
            root = html.fromstring(url.data)
            mirrorTable = root.get_element_by_id('mirror_table')
            for a in mirrorTable.iterfind('.//a'):
                allStreamLinks.append(a.get('href'))

            data['streams'] = []
            for streamLink in allStreamLinks:
                streamData = {}
                streamData['url'] = streamLink

                pinfo = self.stream_extract(streamData['url'], self.log)
                pinfo.name = self.data['name']
                pinfo.title = data['num'] +" "+ data['name']
                self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
                streamData['pinfo'] = pinfo
                data['streams'].append(streamData)
            self.parts.append(data)

urlPart = 'animeseed.com' # this part will be matched in __init__ to create following class
classRef = AnimeSeed
