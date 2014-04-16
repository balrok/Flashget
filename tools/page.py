import config
from tools.stream import VideoInfo
from tools.cache import Cache


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
    def __init__(self):
        self.processedMedia = 0
        self.cache = Cache(config.cache_dir, ['pages', self.name])

    def setPinfo(self, alternativePart, urlHandle = None):
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
            pinfo.title += ' cd'+str(alternativePart.num) #+' of '+str(len(alternative.subs))
        try:
            log.info('added url: %s -> %s'%(pinfo.title , pinfo.url))
        except:
            try:
                log.warning('problem with urlencoding of: '+pinfo.title)
            except:
                try:
                    log.warning('problem with titleencoding of: '+pinfo.url)
                except:
                    log.error('Couldn\'t log the title and url')
        alternativePart.setPinfo(pinfo)

    def beforeExtract(self):
        self.processedMedia += 1
        if config.extractStart > self.processedMedia:
            return False
        if config.extractStart+config.extractAmount < self.processedMedia:
            return False
        return True

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
            log.error('couldn\'t extract name, wrong url or html has changed (link:"'+link+'")')
            return None
        self.count+=1
        #if self.count == 1:
        #    raise Exception
        log.info("Processed Media: "+str(self.processedMedia))
        media.page = self
        media.addTag(self.name)
        return media

    def get(self):
        raise Exception
        return self

class BaseMedia(object):
    _indent = 0 # used for printing
    sub = None
    subs = []
    parent = None
    subNum = 1
    def __init__(self, parent):
        self.subs = []
        self.parent = parent
    def getSubs(self):
        return self.subs
    def createSub(self):
        if not self.sub:
            raise Exception
            return None
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
        9: 'Spanish',
        10:'Italian',
        11:'Turkish',
        12:'Hindi',
        13:'Greek',
        14:'Dutch',
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
            raise Exception("Language '"+name+"' not found")
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
        self.name = name
        self.url = link
        self.tags = []
        self.year = None
        self.img = ''
        self.thumbs = []
        self.length = 0
        self.views = 0
        self.rating = 0.0
        BaseMedia.__init__(self,None)

    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Media:")
        ret.append(indent*" "+self.name)
        ret.append(indent*" "+str(self.tags))
        if self.img:
            ret.append(indent*" "+self.img)
        for part in self.getSubs():
            part._indent = indent + 2
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

    def __init__(self,media):
        self.name = ''
        self.num = 0
        self.season = 0
        BaseMedia.__init__(self, media)
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Part:")
        if self.num:
            ret.append(indent*u" "+str(self.num))
        if self.name:
            ret.append(indent*u" "+self.name)
        for alt in self.getSubs():
            alt._indent = indent+2
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
        self.languageId = None
        self.subtitleId = None
        BaseMedia.__init__(self, part)
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
        indent = self._indent
        ret.append(self._indent*" "+"AltPart:")
        if self.name:
            ret.append(indent*" "+self.name+" "+str(self.num))
        if self.url:
            ret.append(indent*" "+self.url)
        if self.pinfo:
            ret.append(indent*" "+self.pinfo.__str__())
        for sub in self.getSubs():
            sub._indent = indent+2
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
        BaseMedia.__init__(self, alternativePart)
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Flv:")
        if self.flvType:
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
    alternativePartId = property(fget=BaseMedia.getParentId)


from tools.extension import ExtensionRegistrator
pages = ExtensionRegistrator()
pages.loadFolder('tools/pages/')
