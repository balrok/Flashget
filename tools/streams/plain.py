from tools.stream import *
import tools.defines as defs


class PlainStream(VideoInfo):
    homepage_type = defs.Homepage.Plain
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        return 'no title'

    def get_name(self):
        return 'no name'

    def get_subdir(self):
        return 'plain'

    def get_stream(self):
        return {'url': self.url}

