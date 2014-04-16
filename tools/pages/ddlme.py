from tools.page import Page
from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import textextract
try:
    import json
except:
    import lib.simplejson
    json.fixPyLintError=True
    json = lib.simplejson

class DdlMe(Page):
    name = 'ddl me'
    url = 'http://de.ddl.me'

    def __init__(self):
        Page.__init__(self)

    def extract(self, link):
        if not self.beforeExtract():
            return None
        # this page is special: in it's headers it says it is iso-8859-1 but it actually returns utf-8
        url = UrlMgr({'url': link, 'encoding':'utf-8'})
        name = textextract(url.data, "<h1 class='itemHeading detailHeading' id='itemType' rel='0'>",' <b ')
        media = Page.getMedia(self, name, link)
        part = media.createSub()
        if not media:
            return None

        streams = textextract(url.data, '<script type="text/javascript">var subcats = ', '};')+"}"
        streams = json.loads(streams)
        for id in streams:
            for streamName in streams[id]['links']:
                streamParts = streams[id]['links'][streamName]
                alternative = part.createSub()
                existingPartIds = []
                for p in streamParts: # 0=partId, 1=js action, 2=icon, 3=url, 4=hoster id, 5=type
                    # TODO write a system to correct this - but I guess since the dataformat
                    # of them is so bad, it is better to wait until they change it
                    if p[0] in existingPartIds:
                        continue
                    existingPartIds.append(p[0])
                    alternativePart = alternative.createSub()
                    alternativePart.url = p[3]
        return self.afterExtract(media)

baseRegex = '.*ddl.me.*'
class SingleDdlMeExtension(DdlMe, Extension):
    eregex = baseRegex
    ename = 'ddl me s'
    def get(self, link):
        return DdlMe.extract(self, link)
