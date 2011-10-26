from tools.page import *
from tools.streams.plain import PlainStream


class Plain(Page):
    stream_extract = PlainStream
    def __init__(self):
        self.pages_init__()

    def extract_url(self, url, type = Page.TYPE_SINGLE):
        links = [url]
        name, list = self.add_streams(links)
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


urlPart = '' # this part will be matched in __init__ to create following class
classRef = Plain
