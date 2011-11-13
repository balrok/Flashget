import config
import tools.defines as defs
from tools.stream import VideoInfo

log = config.logger['page']


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
#       contains additional description (codec, language)
#   * AlternativePart
#       contains the part-number and dl-url
class Page():
    @staticmethod
    def getPage(classRef):
        return classRef()

    def __init__(self):
        self.log = log
        self.processedMedia = 0

    def setPinfo(self, alternativePart, urlHandle = None):
        alternative = alternativePart.alternative
        part = alternative.part
        media = part.media

        if urlHandle:
            pinfo = VideoInfo(urlHandle, self.log)
        else:
            pinfo = VideoInfo(alternativePart.url, self.log)
        pinfo.name = media.name
        pinfo.title = ""
        if part.num:
            pinfo.title = part.num
        if part.name:
            if part.num:
                pinfo.title += ": "
            pinfo.title += part.name
        else:
            if not part.num:
                pinfo.title += " - "
        if alternativePart.num:
            pinfo.title += '_'+str(num)
        try:
            self.log.info('added url: %s -> %s'%(unicode(pinfo.title) , unicode(pinfo.url)))
        except:
            try:
                self.log.warning('problem with urlencoding of: '+unicode(pinfo.title))
            except:
                try:
                    self.log.warning('problem with titleencoding of: '+unicode(pinfo.url))
                except:
                    self.log.error('Couldn\'t log the title and url')
        alternativePart.setPinfo(pinfo)

    def beforeExtract(self):
        self.processedMedia += 1
        if config.extractStart > self.processedMedia:
            return False
        if config.extractStart+config.extractAmount < self.processedMedia:
            return False
        return True

    def getMedia(self, name, link):
        try:
            media = Media(name, link)
        except ValueError:
            self.log.error('couldn\'t extract name, wrong url or html has changed (link:"'+link+'")')
            return None
        self.log.info("Processed Media: "+str(self.processedMedia))
        media.page = self
        return media

    def get(self):
        raise Exception
        return self

class BaseMedia(object):
    _indent = 0 # used for printing
    sub = None
    subs = []
    def __init__(self):
        self.subs = []
    def getSubs(self):
        return self.subs
    def createSub(self):
        if not self.sub:
            raise Exception
            return None
        sub = eval(self.sub+"(self)")
        sub.page = self.page
        self.subs.append(sub)
        return sub

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

# the databse entries for this table are predefined here
class Language(object):
    # this is the dbcontent
    idToLanguages = {
        1: 'German',
        2: 'English',
        3: 'Japanese',
        4: 'Chinese',
        5: 'Korean',
        6: 'French',
        7: 'Unknown',
        8: 'Russian',
    }
    _cache = {}

    @staticmethod
    def getLanguage(name):
        if name not in Language._cache:
            Language._cache[name] = Language(name)

        return Language._cache[name]

    def setId(self, name):
        for id in self.idToLanguages:
            if self.idToLanguages[id] == name:
                break
        else:
            raise Exception
        self.id = id

    def __init__(self, name):
        self.setId(name)
        self.name = self.idToLanguages[self.id]
        Language._cache[self.name] = self
    def __str__(self):
        return self.name
    def __repr__(self):
        if self.name:
            return 'Lang:'+self.name
        return 'Lang:-'

class Media(BaseMedia):
    sub = 'Part'

    def __init__(self, name="", link=""):
        if not name:
            raise ValueError
        self.name = unicode(name)
        self.url = unicode(link)
        self.tags = []
        self.year = None
        self.parts = []
        BaseMedia.__init__(self)

    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Media:")
        ret.append(indent*" "+self.name)
        if self.img:
            ret.append(indent*" "+self.img)
        for part in self.getSubs():
            part._indent = indent + 2
            ret.append(unicode(part))
        return "\n".join(ret)
    def addTag(self, tagName):
        tag = Tag.getTag(tagName)
        if tag not in self.tags:
            self.tags.append(tag)
    def addTags(self, tagNames):
        for tagName in tagNames:
            self.addTag(tagName)

class Part(BaseMedia):
    sub = 'Alternative'

    def __init__(self,media):
        self.name = ''
        self.num = 0
        self.media = media
        BaseMedia.__init__(self)
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Part:")
        if self.num:
            ret.append(indent*" "+self.num)
        if self.name:
            ret.append(indent*" "+self.name)
        for alt in self.getSubs():
            alt._indent = indent+2
            ret.append(unicode(alt))
        return "\n".join(ret)

class Alternative(BaseMedia):
    sub = 'AlternativePart'
    def __init__(self, part):
        self.name = ''
        self.hoster = ''
        self.part = part
        self.subtitle = None
        self.subtitleId = None
        BaseMedia.__init__(self)
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Alt:")
        if self.hoster:
            ret.append(self._indent*" "+self.hoster)
        if self.name:
            ret.append(indent*" "+self.name)
        if self.subtitle:
            ret.append(self._indent*" "+str(self.subtitle))
        if self.language:
            ret.append(self._indent*" "+str(self.language))
        for altP in self.getSubs():
            altP._indent = indent+2
            ret.append(unicode(altP))
        return "\n".join(ret)

class AlternativePart(BaseMedia):
    sub = 'Flv'
    def __init__(self, alternative):
        self.name = ''
        self.alternative = alternative
        self.url = ''
        self.pinfo = None
        self.num = 0
        BaseMedia.__init__(self)
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"AltPart:")
        if self.name:
            ret.append(indent*" "+self.name)
        if self.url:
            ret.append(indent*" "+self.url)
        if self.pinfo:
            ret.append(indent*" "+unicode(self.pinfo))
        for sub in self.getSubs():
            sub._indent = indent+2
            ret.append(unicode(sub))
        return "\n".join(ret)
    def setPinfo(self,pinfo):
        flv = self.createSub()
        flv.setPinfo(pinfo)
        if not config.extract_all:
            self.pinfo = pinfo

class Flv(BaseMedia):
    def __init__(self, alternativePart):
        self.link = ''
        self.flvId = ''
        self.flvType = ''
        self.data = ''
        self.alternativePart = alternativePart
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Flv:")
        ret.append(self._indent*" "+str(self.flvType))
        if self.link:
            ret.append(self._indent*" "+str(self.link))
        if self.flvId:
            ret.append(self._indent*" "+str(self.flvId))
        if self.data:
            ret.append(indent*" "+self.data)
        return "\n".join(ret)
    def setPinfo(self, pinfo):
        self.link = pinfo.stream_url
        self.code = pinfo.stream_id
        self.type = pinfo.flv_type
        if self.link and pinfo.flv_available:
            self.available = True
        else:
            self.available = False
