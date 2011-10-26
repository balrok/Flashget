from tools.url import UrlMgr
from tools.helper import *
import tools.defines as defs
from stream_extract import *


def extract_stream(data):
    ''' extracts the streamlink from specified data '''
    url = ''
    post = textextract(data, 'value="domain=hdweb.ru&', '&mode') # TODO: i think we can extract this from the url
    if post:
        url = 'http://hdweb.ru'
    if not url:
        url = textextract(data, '<embed src="', '"')
    if not url:
        url = textextract(data, '<embed src=\'', '\'')
    if not url:
        url = textextract(data, '<param name="movie" value="','"')
    if not url:
        url = textextract(data, '<param name=\'movie\' value=\'','\'')
    return {'url': url, 'post': post}

class VideoInfo(object):

    def init__(self, url, log):
        self.url = urldecode(url)
        self.log = log
        self.stream_post = None
        self.url_handle = UrlMgr({'url': self.url, 'log': self.log})

    def throw_error(self, str):
        self.log.error('%s %s' % (str, self.url))
        return

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.url)

    def get_name__(self, name):
        if not name:
            self.name = self.__hash__()
            self.log.info('couldnt extract name - will now use hash: %s' % self.name)
        else:
            self.name = normalize_title(name)
        return self.name

    def get_title__(self, title):
        if not title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self) # normalize_title isn't needed, the hash will make sure that the title looks ok
            self.log.info('couldnt extract title - will now use the hash from this url: %s' % self.title)
        else:
            self.title = normalize_title(title)
        return self.title

    def get_subdir__(self, dir):
        import os
        import config
        dir2 = os.path.join(config.flash_dir, dir)
        if os.path.isdir(dir2) is False:
            try:
                os.makedirs(dir2)
            except:
                self.throw_error('couldn\'t create subdir in %s' % dir2)
                dir = ''
            open(dir2 + '/.flashget_log', 'a').write(' '.join(sys.argv) + '\n')
        self.subdir = dir
        return self.subdir

    def get_stream__(self, args):
        self.stream_url = args['url']
        if 'post' in args:
            self.stream_post = args['post']
        self.stream_type = defs.Stream.NONE
        if not self.stream_url:
            self.throw_error('couldn\'t find a streamlink inside this url')
            return None
        for i in url2defs:
            if self.stream_url.find(i) > 0:
                self.stream_type = url2defs[i]
                break
        else:
            self.throw_error('couldn\'t find a supported streamlink in: %s' % self.stream_url)
        return self.stream_url

    def get_flv__(self):
        ret = def2func[self.stream_type](self)
        if not ret:
            ret = (None, (None, None))
        self.flv_url, self.flv_call = ret
        return self.flv_url

    def __getattr__(self, key):
        if key == 'title':
            if config.dl_title:
                return config.dl_title
            return self.get_title__(self.get_title())
        elif(key == 'name'):
            if config.dl_name:
                return config.dl_name
            return self.get_name__(self.get_name())
        elif key == 'subdir':
            return self.get_subdir__(self.get_subdir())
        elif(key == 'stream_url'):
            return self.get_stream__(self.get_stream())
        elif(key == 'stream_type'):
            self.get_stream__(self.get_stream())
            return self.stream_type
        elif(key == 'flv_url'):
            return self.get_flv__()
        elif(key == 'flv_call'):
            self.get_flv__()
            return self.flv_call

