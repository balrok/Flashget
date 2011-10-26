import config
import tools.defines as defs


class VideoContainer(object):
    def __init__(self, name = ''):
        self.name = name # the name of the videocontainer (name of a serie, or name of a movie)
        self.list = []   # contains list of videos

class Page(object):
    TYPE_UNK    = 0
    TYPE_MULTI  = 1
    TYPE_SINGLE = 2

    def pages_init__(self, log):
        self.video_container = []
        self.log = log
        self.tmp             = {}

    def name_handle(self, i, pinfo):
        ''' i == index in links-list, pinfo == pinfo from current url in links-list '''
        return

    def add_streams(self, links):
        dlList = []
        ll = len(links)
        if ll == 0:
            self.log.error('failed to extract the links')
            return (None, None)
        for i in xrange(0, ll):
            if isinstance(links[i], (list, tuple)):
                for j in links[i]:
                    pinfo = self.stream_extract(self.links_handle(i, links), self)
                    self.name_handle(i, pinfo)
                    dlList.append(pinfo)
                    self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
            else:
                pinfo = self.stream_extract(self.links_handle(i, links), self)
                self.name_handle(i, pinfo)
                dlList.append(pinfo)
                self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
        if config.win_mgr:
            config.win_mgr.append_title(defs.Homepage.str[pinfo.homepage_type])
            config.win_mgr.append_title(pinfo.name.encode('utf-8'))
            if ll == 1:
                config.win_mgr.append_title(pinfo.title.encode('utf-8'))
        return (pinfo.name, dlList)


pages = {}
def registerPage(urlPart, classRef):
    pages[urlPart] = classRef


def getClass(link, log):
    if link == '':
        log.error("empty page added")
        return None
    link = link.lower()
    # urlparts are getting sorted, so that the longer strings getting matched first.. so '' for plain is always the last one.. and "test.com" also comes after "mytest.com"
    urlParts = pages.keys()
    urlParts.sort(key=len, reverse=True)
    for urlPart in urlParts:
        if link.find(urlPart) >= 0:
            classRef = pages[urlPart]
            return classRef(log)
    log.error("page %s is not supported, must contain any of those: %s" % (link, str(urlParts)))
    return None
