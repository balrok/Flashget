from tools.page import *
from tools.streams.animeloads import AnimeLoadsStream
from tools.url import UrlMgr
from tools.helper import *
from lxml import html
from lxml import etree
import re
import sys

class MovieLoads(Page):
    stream_extract = AnimeLoadsStream

    def __init__(self):
        self.pages_init__()

    def extract(self, url):
        url = UrlMgr({'url': url, 'log': self.log})

        try:
            self.data['name'] = textextract(url.data, '<title>',' - Movie-Loads.NET</title>')
        except:
            self.log.error('couldn\'t extract name, dumping content...')
            self.log.error(url.data)
            sys.exit(1)


        #self.data= {'name':'..'}
        #self.parts = [
        #    {
        #        'name':'..',
        #        'parts':[
        #            {
        #                'url':'..',
        #                'pinfo':None
        #            }
        #        ]
        #    }
        #]

        root = html.fromstring(url.data)
        for box in root.iterfind(".//div[@class='boxstream']"):
            data = {}
            curCol = 0
            data['name'] = box.find("h2").text_content()
            data['parts'] = []

            streamBlock = box.find(".//a[@rel='#overlay']") # normally there are multiple streams.. but cause they are from videobb and videozer it makes no sense

            data['audio'] = re.findall("language/(.*?)\.gif", etree.tostring(streamBlock))
            data['hoster'] = re.findall("img/stream_(.*?)\.png", etree.tostring(streamBlock))

            partData = {}
            streamUrl = 'http://www.movie-loads.net/'+streamBlock.get('href')
            url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
            streamUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
            url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
            realUrl = ''
            if url.data.find('videobb') > 0:
                realUrl = 'http://www.videobb.com/video/'+textextract(url.data, 'http://www.videobb.com/f/', '.swf')
            if url.data.find('videozer') > 0:
                realUrl = 'http://www.videozer.com/video/'+textextract(url.data, 'http://www.videozer.com/flash/', '.swf')
            partData['url'] = realUrl


            # multiple parts possible: v id="navi_parts"><ul><li><a href="#" onclick="update('streamframe.php?v=102256&part=1');" class="active" id="part_selected">PART 1</a></li><li><a href="#"
            # onclick="update('streamframe.php?v=102256&part=2');">PART 2</a></li
            root = html.fromstring(url.data)
            try:
                otherParts = root.get_element_by_id('navi_parts')
            except:
                otherParts = False


            pinfo = self.stream_extract(realUrl, self.log)
            pinfo.name = self.data['name']
            pinfo.title = data['name']
            if otherParts:
                pinfo.title = '1_'+pinfo.title
            self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
            partData['pinfo'] = pinfo
            data['parts'].append(partData)

            if otherParts:
                count = 1
                for part in otherParts.iterfind(".//a"):
                    if part.get('class') == 'active':
                        continue
                    count+=1
                    partData = {}
                    streamUrl = 'http://www.movie-loads.net/'+textextract(part.get('onclick'), "('", "')")
                    url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
                    streamUrl = 'http://www.movie-loads.net/'+textextract(url.data, '<iframe name="iframe" src="', '"')
                    url = UrlMgr({'url': streamUrl, 'log': self.log, 'cache_writeonly':True})
                    realUrl = ''
                    if url.data.find('videobb') > 0:
                        realUrl = 'http://www.videobb.com/video/'+textextract(url.data, 'http://www.videobb.com/f/', '.swf')
                    if url.data.find('videozer') > 0:
                        realUrl = 'http://www.videozer.com/video/'+textextract(url.data, 'http://www.videozer.com/flash/', '.swf')

                    partData['url'] = realUrl
                    pinfo = self.stream_extract(realUrl, self.log)
                    pinfo.name = self.data['name']
                    pinfo.title = str(count)+'_'+data['name']
                    self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
                    partData['pinfo'] = pinfo
                    data['parts'].append(partData)
            self.parts.append(data)

urlPart = 'movie-loads' # this part will be matched in __init__ to create following class
classRef = MovieLoads
