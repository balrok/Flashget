import config
import tools.defines as defs
from tools.stream import VideoInfo

from tools.db import *

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
class Page(Base):
    __tablename__ = "page"
    id = Column(Integer, primary_key = True)
    name = Column(String(255), unique=True)
    url = Column(String(255), unique=True)
    _cache = {}

    @staticmethod
    def getPage(classRef):
        c = classRef()
        if c.name in Page._cache:
            return Page._cache[c.name]
        return c

    def __init__(self):
        self.log = log
        page = session.query(Page).filter_by(name=self.name).first()
        self.processedMedia = 0
        if not page:
            session.merge(self)
            session.commit()
        else:
            self.id = page.id

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
        page = session.query(Page).filter_by(name=self.name).first()
        if page:
            self = page
        return self

class BaseMedia(object):
    id = Column(Integer, primary_key = True)
    _indent = 0 # used for printing
    sub = None
    def getSubs(self):
        return None
    def createSub(self):
        if not self.sub:
            return None
        sub = eval(self.sub+"(self)")
        sub.page = self.page
        return sub


media_to_tag = Table('media_to_tag', Base.metadata,
    Column('mediaId', Integer, ForeignKey('media.id')),
    Column('tagId', Integer, ForeignKey('tag.id'))
)

class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key = True)
    name = Column(String(255), unique=True)
    medias = relation('Media', secondary=media_to_tag, backref=backref('tags'))
    _idCache = {}
    _cache = {}

    # id must be set, else inserting to db will be problematic
    def setId(self, name):
        if name not in self._idCache:
            tag = session.query(Tag).filter_by(name=name).first()
            if not tag:
                session.merge(self)
                session.commit()
                self._idCache[name] = self.id
            else:
                self._idCache[name] = tag.id
        self.id = self._idCache[name]

    def __init__(self, name):
        self.name = name
        self.setId(name)
        self._cache[self.name] = self

    @staticmethod
    def getTag(name):
        if name in Tag._cache:
            return Tag._cache[name]
        return Tag(name)

    def __str__(self):
        return self.name
    def __repr__(self):
        if self.name:
            return 'Tag:'+self.name
        return 'TAG:-'

media_subtitles = Table('media_subtitles', Base.metadata,
    Column('mediaId', Integer, ForeignKey('media.id')),
    Column('languageId', Integer, ForeignKey('language.id'))
)
media_languages = Table('media_languages', Base.metadata,
    Column('mediaId', Integer, ForeignKey('media.id')),
    Column('languageId', Integer, ForeignKey('language.id'))
)
# the databse entries for this table are predefined here
class Language(Base):
    __tablename__ = "language"
    id = Column(Integer, primary_key = True)
    name = Column(String(255), unique=True)
    subMedias = relation('Media', secondary=media_subtitles, backref=backref('subtitles'))
    langMedias = relation('Media', secondary=media_languages, backref=backref('languages'))
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

    # id must be set, else inserting to db will be problematic
    def setId(self, name):
        for id in self.idToLanguages:
            if self.idToLanguages[id] == name:
                break
        else:
            raise Exception
        self.id = id

    @staticmethod
    def getLanguage(name):
        if name in Language._cache:
            return Language._cache[name]
        return Language(name)

    def __init__(self, name):
        self.name = name
        self.setId(name)
        self.name = self.idToLanguages[self.id]
        Language._cache[self.name] = self

    def __str__(self):
        return self.name
    def __repr__(self):
        if self.name:
            return 'Lang:'+self.name
        return 'Lang:-'
class Media(Base, BaseMedia):
    __tablename__ = "media"
    name = Column(String(255))
    img = Column(String(255))
    url = Column(String(255))
    year = Column(Integer)
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('medias'), enable_typechecks=False)
    sub = 'Part'

    def __init__(self, name="", link=""):
        if not name:
            raise ValueError
        self.name = unicode(name)
        self.url = unicode(link)

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
    def getSubs(self):
        return self.parts
    def addTag(self, tagName):
        tag = Tag.getTag(tagName)
        if tag not in self.tags:
            self.tags.append(tag)
    def addTags(self, tagNames):
        for tagName in tagNames:
            self.addTag(tagName)

class Part(Base, BaseMedia):
    __tablename__ = "media_part"
    name = Column(String(255))
    num = Column(String(255))
    mediaId = Column(Integer, ForeignKey(Media.id))
    media = relationship(Media, backref=backref('parts'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('parts'), enable_typechecks=False)
    sub = 'Alternative'

    def __init__(self,media):
        self.name = ''
        self.num = 0
        self.media = media
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
    def getSubs(self):
        return self.alternatives

class Alternative(Base, BaseMedia):
    __tablename__ = "media_alternative"
    name = Column(String(255))
    hoster = Column(JSONEncodedDict())
    partId = Column(Integer, ForeignKey(Part.id))
    part = relationship(Part, backref=backref('alternatives'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('alternatives'), enable_typechecks=False)

    subtitleId = Column(Integer, ForeignKey(Language.id))
    subtitle = relationship(Language, backref=backref('subAlternatives'), primaryjoin="Language.id==Alternative.subtitleId", enable_typechecks=False)
    languageId = Column(Integer, ForeignKey(Language.id))
    language = relationship(Language, backref=backref('langAlternatives'), primaryjoin="Language.id==Alternative.languageId", enable_typechecks=False)

    sub = 'AlternativePart'
    def __init__(self, part):
        self.name = ''
        self.hoster = ''
        self.part = part
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
    def getSubs(self):
        return self.alternativeParts

class AlternativePart(Base, BaseMedia):
    __tablename__ = "media_alternative_part"
    name = Column(String(255))
    url = Column(String(255))
    num = Column(String(255))
    pinfo = None
    alternativeId = Column(Integer, ForeignKey(Alternative.id))
    alternative = relationship(Alternative, backref=backref('alternativeParts'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('alternativeParts'), enable_typechecks=False)
    sub = 'Flv'
    def __init__(self, alternative):
        self.name = ''
        self.alternative = alternative
        self.url = ''
        self.pinfo = None
        self.num = 0
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
    def getSubs(self):
        return self.flvs
    def setPinfo(self,pinfo):
        flv = self.createSub()
        flv.setPinfo(pinfo)
        if not config.extract_all:
            self.pinfo = pinfo

class Flv(Base, BaseMedia):
    __tablename__ = "media_flv"
    link = Column(String(255))
    code = Column(String(255))
    type = Column(String(255))
    data = Column(Text(255))
    available = Column(Boolean())
    alternativePartId = Column(Integer, ForeignKey(AlternativePart.id))
    alternativePart = relationship(AlternativePart, backref=backref('flvs'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('flvs'), enable_typechecks=False)

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

Base.metadata.create_all(engine)
