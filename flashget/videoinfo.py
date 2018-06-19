
import logging

from .url import UrlMgr
from .helper import urldecode, normalize_title

log = logging.getLogger(__name__)

# maintains lowlevel information about the video file
# basically name, title and stream object
class VideoInfo(object):
    def __init__(self, url):
        self.subdir = ""
        self.flv_url = ""
        self.title = ""
        self.has_stream = False
        # don't set the following values because they are set by getattr
        # self.stream = None
        if isinstance(url, UrlMgr):
            self.stream_url = url.url
        else:
            self.stream_url = urldecode(url)

    def __hash__(self):
        # the hash will always start with "h" to create also a good filename
        # hash will be used, if title-extraction won't work
        return 'h %s' % hash(self.stream_url)

    def __getattr__(self, key):
        if key == 'subdir':
            return self.get_subdir()
        elif key == 'stream_url':
            return self.get_stream()
        elif key == 'stream':
            self.get_stream()
            return self.stream
        elif key == 'flv_url':
            return self.get_flv()
        elif key == 'flv_type':
            if self.has_stream:
                self.flv_type = self.stream.ename
            else:
                self.flv_type = None
            return self.flv_type

    def __repr__(self):
        return "%s: %s .-. %s" % (self.__class__.__name__, self.flv_type, self.title)

    def get_subdir(self):
        self.subdir = self.name
        return self.subdir

    def get_flv(self):
        self.flv_url = self.stream.get(self)
        return self.flv_url

    def get_title(self):
        log.error("TITLE must be downloaded from overviewpage")
        if not self.title:
            # it isn't fatal if we don't have the title, just use the own hash, which should be unique
            # maybe in future, we should set a variable here, so that we know from outside,
            # if the title is only the hash and we need to discover a better one
            self.title = hash(self)  # normalize_title isn't needed, the hash will make sure that the title looks ok
            log.info('couldnt extract title - will now use the hash from this url: %s', self.title)
        else:
            self.title = normalize_title(self.title)
        return self.title

    def get_stream(self):
        # to avoid recursive dependencies, import it here
        from .plugins import getStreamByLink

        stream = getStreamByLink(self.stream_url)
        if self.flv_type: # normally a stream knows its flv_type - but redirection pages don't..
            stream.flv_type = self.flv_type

        # this would open the page and look for common flash embedding to find a link for the download
        # I think this code doesn't belong here and should go to each individual page extractor (only if needed - most won't need this)
        # if stream is None:
        #     streamData = extract_stream(UrlMgr(url=self.stream_url).data)
        #     if streamData and streamData['url']:
        #         stream = findStream(streamData['url'])
        #         self.stream_url = streamData['url']

        if stream is None or stream.flvUrl is None:
            log.warning('couldn\'t find a supported streamlink in: %s', self.stream_url)
            self.stream_url = None
            self.stream = None
            return None
        self.stream = stream
        self.has_stream = True
        return self.stream_url
