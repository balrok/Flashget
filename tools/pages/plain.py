from tools.page import *
from tools.streams.plain import PlainStream


class Plain(Page):
    stream_extract = PlainStream
    def __init__(self, log):
        self.pages_init__(log)

    def extract_url(self, url, type = Page.TYPE_SINGLE):
        links = [url]
        name, list = self.add_streams(links)
        self.tmp = {}
        if name:
            container = VideoContainer(name)
            self.video_container.append(container)
            container.list = list
            return container
        return None

    def name_handle(self, i, pinfo):
        pinfo.title = 'no title'
    def links_handle(self, i, links):
        return links[i]


registerPage('', Plain) # match all
