from __future__ import unicode_literals
import youtube_dl
from pprint import pprint
import logging
import tempfile

from .url import LargeDownload
from .config import config

log = logging.getLogger(__name__)

ydl_opts = {'cachedir': config.get('cache_dir_for_flv', tempfile.mkdtemp()),
        'fixup': 'warn',
        'max_downloads': config.get('dl_instances', 6),
        'output': '/home/balrok/.flashget/downloads/%(title)',
        }
ydl = youtube_dl.YoutubeDL(ydl_opts)


class YoutubedlWrapper(object):
    ename = 'YoutubedlWrapper'
    eregex = '.*'
    url = '.*'
    ePriority = 100
    score = 0

    def __init__(self, link):
        self.link = link
        self.flvUrl = link # shouldnt this be None
        self.info = None

    def __getattr__(self, key):
        if key == 'info':
            return self.getInfo()

    def getInfo(self):
        if self.info is not None:
            return self.info
        try:
            self.info = ydl.extract_info(self.link, download=False)
        except:
            self.flvUrl = None
            return None
        return self.info

    def getId(self):
        return self.getInfo()['id']

    def download(self, **kwargs):
        if not self.link:
            raise Exception("No flv url - can't start download")

        self.flvUrl = self.getInfo()['url']
        kwargs['url'] = self.flvUrl
        kwargs['header'] = self.info['http_headers']

        # TODO overwrite target-name if it is unknown

        # TODO later let YoutubeDL handle this and get into progress_hooks

        log.info('Extracted following url for download: %s', self.flvUrl)
        return LargeDownload(**kwargs)

    def getScore(self):
        return self.score

    def __str__(self):
        ret = self.__class__.__name__
        try:
            ret += ": " + self.info['extractor_key']
            try:
                ret += ": " + self.info['title']
            except:
                pass
        except:
            try:
                ret += ": " + self.flvUrl
            except:
                pass
        return ret

# example of info
#{u'display_id': u'6jdcx3su36ne',
# u'ext': u'mp4',
# u'extractor': u'streamcloud.eu',
# u'extractor_key': 'Streamcloud',
# u'format': u'0 - unknown',
# u'format_id': u'0',
# u'http_headers': {u'Accept': u'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#                   u'Accept-Charset': u'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
#                   u'Accept-Encoding': u'gzip, deflate',
#                   u'Accept-Language': u'en-us,en;q=0.5',
#                   u'Cookie': 'lang=english',
#                   u'User-Agent': u'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)'},
# u'id': u'6jdcx3su36ne',
# u'playlist': None,
# u'playlist_index': None,
# u'requested_subtitles': None,
# u'thumbnail': u'http://stor6.streamcloud.eu:8080/i/01/00133/9esmzguaie5w.jpg',
# u'thumbnails': [{u'id': u'0',
#                  u'url': u'http://stor6.streamcloud.eu:8080/i/01/00133/9esmzguaie5w.jpg'}],
# u'title': u'1988-Police Story 2-zz4308-1938',
# u'url': u'http://cdn5.streamcloud.eu:8080/s7v75q3je2oax3ptx3gindhnw24jpyjw5ijz2xi6vcpi7kjylcxmggtuue/video.mp4',
# u'webpage_url': u'http://streamcloud.eu/6jdcx3su36ne/1988-Police_Story_2-zz4308-1938.avi.html',
# u'webpage_url_basename': u'1988-Police_Story_2-zz4308-1938.avi.html'}


from .helper import EndableThreadingClass
class ThreadedYDL(EndableThreadingClass):
    def __init__(self, url):
        EndableThreadingClass.__init__(self)
