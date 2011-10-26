from tools.page import *
from tools.streams.youtube import YouTubeStream

class YouTube(Page):
    stream_extract = YouTubeStream

    def __init__(self):
        self.pages_init__()

    def extract_url(self, url, type = Page.TYPE_UNK):
        containername = ''
        if type == Page.TYPE_UNK:
            if url.find('view_play_list') >= 0:
                # http://www.youtube.com/view_play_list?p=9E117FE1B8853013&search_query=georg+kreisler
                type = Page.TYPE_MULTI
            else:
                type = Page.TYPE_SINGLE
        if type == Page.TYPE_MULTI:
            url = UrlMgr({'url': url, 'log': self.log})
            # alt="Georg Kreisler: Schlagt sie tot?"></a><div id="quicklist-icon-bmQbYP_VkCw" class="addtoQL90"
            # maybe we can get all this data in one action..
            links = textextractall(url.data, 'id="add-to-quicklist-', '"')
            self.tmp['names'] = textextractall(url.data, '" alt="', '"') # luckily this alt-tag only occurs for those icons :)
            containername = remove_html(self.tmp['names'][0].decode('utf-8'))
        else:
            links = [url]
        self.tmp['type'] = type
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            if containername:
                container.name = containername
            container.list = list
            self.video_container.append(container)
            return container
        return None


    def name_handle(self, i, pinfo):
        if self.tmp['type'] == Page.TYPE_MULTI:
            pinfo.title = remove_html(self.tmp['names'][i + 1].decode('utf-8'))

    def links_handle(self, i, links):
        if self.tmp['type'] == Page.TYPE_MULTI:
            return 'http://www.youtube.com/watch?v=%s' % links[i]
        else:
            return links[i]


registerPage('youtube', YouTube)
