from tools.stream import *
import tools.defines as defs

class AnimeLoadsStream(VideoInfo):
    homepage_type = defs.Homepage.ANIMELOADS
    def __init__(self, url, log):
        self.init__(url, log) # call baseclass init

    def get_title(self):
        self.log.error("TITLE must be downloaded from overviewpage")
        return ''

    def get_name(self):
        return textextract(self.url, 'streams/','/')

    def get_subdir(self):
        return self.name

    def get_stream(self):
        x = self.url_handle.data.find('id="download"')
        stream = extract_stream(self.url_handle.data[x+50:])
        # for some videos this happened and resulted in bad requests it's possible to implement this check generic, but currently it's only for animeloads
        if stream and stream['url']:
            if stream['url'].endswith('\r\n'):
                stream['url'] = stream['url'][:-2]
        return stream

