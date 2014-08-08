from .config import config
from .stream import VideoInfo
import logging
import os


log = logging.getLogger(__name__)


# A Page describes a website where a movie or serie is located
# this movie/serie contains a name and 1-* parts
# Each part can contain 1-* alternative Downloadlocations and a name and number
# Each alternative Downloadlocation can contain 1-* parts where each gets a number and a url

# Classes:
#   * Page
#       extracting the information, navigating, creates following classes
# all following classes referencing each other top and down.. so Media<->Part<->Alternative<->AlternativePart
#   * Media (Movie/Serie)
#       contains information (most important the name)
#   * Part
#       contains number and name (for example a serie contains many parts which are numbered)
#   * Alternative
#       cause one part can be downloaded from multiple hosts or with different codecs/audio...
#       contains additional description (codec, language, subtitle)
#   * AlternativePart
#       contains the part-number and dl-url
class Page(object):
    def __init__(self, link):
        self.link = link

    def setPinfo(self, alternativePart, urlHandle=None):
        alternative = alternativePart.parent
        part = alternative.parent
        media = part.parent

        if urlHandle is not None:
            pinfo = VideoInfo(urlHandle)
        else:
            pinfo = VideoInfo(alternativePart.url)
        pinfo.name = media.name
        pinfo.title = media.name

        if len(media.subs) > 1:
            if part.season < 1:
                pinfo.title += u" %02d: " % int(part.num)
            else:
                pinfo.title += u" - [%02dx%02d] - " % (int(part.season), int(part.num))
        if part.name != media.name:
            pinfo.title += part.name
        if len(alternative.subs) > 1:
            pinfo.title += ' cd'+str(alternativePart.num)  # +' of '+str(len(alternative.subs))
        log.info('added url: %s -> %s', pinfo.title, pinfo.url)
        alternativePart.setPinfo(pinfo)

    def afterExtract(self, media):
        for part in media.subs:
            for alternative in part.subs:
                for alternativePart in alternative.subs:
                    self.setPinfo(alternativePart)
        return media

    count = 0

    def getMedia(self, name, link):
        try:
            media = Media(name, link)
        except ValueError:
            log.error('couldn\'t extract name, wrong url or html has changed (link:"%s")', link)
            return None
        self.count += 1
        # if self.count == 1:
        #    raise Exception
        media.page = self
        media.addTag(self.name)
        return media

    def get(self):
        raise Exception


class BaseMedia(object):
    indent = 0  # used for printing
    sub = None
    subs = []
    parent = None
    subNum = 1
    name = ""

    def __init__(self, parent):
        self.subs = []
        self.parent = parent

    def getSubs(self):
        return self.subs

    def createSub(self):
        if not self.sub:
            raise Exception
        sub = eval(self.sub+"(self)")
        sub.num = self.subNum
        self.subNum += 1
        sub.name = self.name
        self.subs.append(sub)
        return sub

    def getParentId(self):
        if self.parent:
            return self.parent.id
        return None

    parentId = property(fget=getParentId)


class Tag(object):
    _cache = {}

    def __init__(self, name):
        self.name = name
        self._cache[self.name] = self

    @staticmethod
    def getTag(name):
        if name not in Tag._cache:
            Tag._cache[name] = Tag(name)
        return Tag._cache[name]

    def __str__(self):
        return self.name

    def __repr__(self):
        if self.name:
            return 'Tag:'+self.name
        return 'TAG:-'


class Media(BaseMedia):
    sub = 'Part'

    def __init__(self, name="", link=""):
        if not name:
            raise ValueError
        self.name = name
        self.url = link
        self.tags = []
        self.year = None
        self.img = ''
        self.thumbs = []
        self.length = 0
        self.views = 0
        self.rating = 0.0
        BaseMedia.__init__(self, None)

    def __str__(self):
        ret = []
        indent = self.indent
        ret.append(self.indent*" "+"Media:")
        ret.append(indent*" "+self.name)
        ret.append(indent*" "+str(self.tags))
        if self.img:
            ret.append(indent*" "+self.img)
        for part in self.getSubs():
            part.indent = indent + 2
            ret.append(part.__str__())
        return u"\n".join(ret)

    def addTag(self, tagName):
        tag = Tag.getTag(tagName)
        if tag not in self.tags:
            self.tags.append(tag)

    def addTags(self, tagNames):
        for tagName in tagNames:
            self.addTag(tagName)

class Part(BaseMedia):
    sub = 'Alternative'

    def __init__(self, media):
        self.name = ''
        self.num = 0
        self.season = 0
        BaseMedia.__init__(self, media)

    def __str__(self):
        ret = []
        indent = self.indent
        ret.append(self.indent*" "+"Part:")
        if self.num:
            ret.append(indent*u" "+str(self.num))
        if self.name:
            ret.append(indent*u" "+self.name)
        for alt in self.getSubs():
            alt.indent = indent+2
            ret.append(alt.__str__())
        return "\n".join(ret)

    mediaId = property(fget=BaseMedia.getParentId)


class Alternative(BaseMedia):
    sub = 'AlternativePart'

    def __init__(self, part):
        self.name = ''
        self.hoster = ''
        self.subtitle = None
        self.language = None
        BaseMedia.__init__(self, part)

    def __str__(self):
        ret = []
        indent = self.indent
        ret.append(self.indent*" "+"Alt:")
        if self.hoster:
            ret.append(self.indent*" "+self.hoster)
        if self.name:
            ret.append(indent*" "+self.name)
        if self.subtitle:
            ret.append(self.indent*" "+str(self.subtitle))
        if self.language:
            ret.append(self.indent*" "+str(self.language))
        for altP in self.getSubs():
            altP.indent = indent+2
            ret.append(altP.__str__())
        return "\n".join(ret)
    partId = property(fget=BaseMedia.getParentId)


class AlternativePart(BaseMedia):
    sub = 'Flv'

    def __init__(self, alternative):
        self.name = ''
        self.url = ''
        self.pinfo = None
        self.num = 0
        BaseMedia.__init__(self, alternative)

    def __str__(self):
        ret = []
        indent = self.indent
        ret.append(self.indent*" "+"AltPart:")
        if self.name:
            ret.append(indent*" "+self.name+" "+str(self.num))
        if self.url:
            ret.append(indent*" "+self.url)
        if self.pinfo:
            ret.append(indent*" "+self.pinfo.__str__())
        for sub in self.getSubs():
            sub.indent = indent+2
            if sub.link is not None:
                ret.append(sub.__str__())
        return "\n".join(ret)

    def setPinfo(self, pinfo):
        flv = self.createSub()
        flv.setPinfo(pinfo)
        self.pinfo = pinfo

    alternativeId = property(fget=BaseMedia.getParentId)


class Flv(BaseMedia):
    def __init__(self, alternativePart):
        self.link = ''
        self.flvId = ''
        self.flvType = ''
        self.data = ''
        self.available = False
        self.code = ''
        self.type = ''
        BaseMedia.__init__(self, alternativePart)

    def __str__(self):
        ret = []
        indent = self.indent
        ret.append(self.indent*" "+"Flv:")
        if self.flvType:
            ret.append(self.indent*" "+str(self.flvType))
        if self.link:
            ret.append(self.indent*" "+str(self.link))
        if self.flvId:
            ret.append(self.indent*" "+str(self.flvId))
        if self.data:
            ret.append(indent*" "+self.data)
        return "\n".join(ret)

    def setPinfo(self, pinfo):
        self.link = pinfo.stream_url
        self.code = pinfo.stream_id
        self.type = pinfo.flv_type
        if self.link and pinfo.flv_available:
            self.available = True
    alternativePartId = property(fget=BaseMedia.getParentId)


from .extension import ExtensionRegistrator
pages = ExtensionRegistrator()


def loadExtension():
    if not pages.loaded:
        # folder from this project
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'pages')
        pages.loadFolder(path)
        # folder from config
        path = config.get('page_extension_dir', "")
        if len(path) > 1:
            pages.loadFolder(path)


def getPageByLink(link):
    loadExtension()
    page = pages.getExtensionByRegexStringMatch(link)
    if page is not None:
        return page(link)
    return None


def getAllPages():
    import inspect
    loadExtension()
    returnData = []
    for page in pages.extensions:
        returnData.append((page, inspect.getfile(page)))
    return returnData
