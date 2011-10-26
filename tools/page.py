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
        config.win_mgr.append_title(defs.Homepage.str[pinfo.homepage_type])
        config.win_mgr.append_title(pinfo.name.encode('utf-8'))
        if ll == 1:
            config.win_mgr.append_title(pinfo.title.encode('utf-8'))
        return (pinfo.name, dlList)

