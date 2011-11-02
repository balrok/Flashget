import config
import tools.defines as defs
from tools.stream import VideoInfo

from tools.db import *

log = config.logger['page']


# TODO:
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
    name = Column(String(255))
    url = Column(String(255))
    TYPE_UNK    = 0
    TYPE_MULTI  = 1
    TYPE_SINGLE = 2

    def pages_init__(self):
        self.log = log

    def setPinfo(self, alternativePart):
        alternative = alternativePart.alternative
        part = alternative.part
        media = part.media

        pinfo = VideoInfo(alternativePart.url, self.log)
        pinfo.name = media.name
        pinfo.title = ""
        if part.num:
            pinfo.title = part.num+": "
        if part.name:
            pinfo.title += part.name
        else:
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
        alternativePart.pinfo = pinfo



class BaseMedia(object):
    id = Column(Integer, primary_key = True)
    _indent = 0 # used for printing
    def save(self):
        session.add(self)
        if self.getSubs():
            for sub in self.getSubs():
                sub.save()
        session.commit()
    def delete(self):
        if self.getSubs():
            for sub in self.getSubs():
                sub.delete()
        session.delete(self)
        session.commit()
    def getSubs(self):
        return None


class Media(Base, BaseMedia):
    __tablename__ = "media"
    name = Column(String(255))
    img = Column(String(255))
    tags = Column(JSONEncodedDict())
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('medias'))

    def __init__(self, name=""):
        if not name:
            raise ValueError
        self.name = unicode(name)
        self.parts = []
        self.tags = []

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
    def createSub(self):
        sub = Part(self)
        return sub
    def getSubs(self):
        return self.parts

class Part(Base, BaseMedia):
    __tablename__ = "media_part"
    name = Column(String(255))
    num = Column(String(4))
    mediaId = Column(Integer, ForeignKey(Media.id))
    media = relationship(Media, backref=backref('parts'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('parts'))
    alternatives = []

    def __init__(self,media):
        self.name = ''
        self.num = 0
        self.media = media
        self.alternatives = []
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
    def createSub(self):
        sub = Alternative(self)
        return sub
    def getSubs(self):
        return self.alternatives

class Alternative(Base, BaseMedia):
    __tablename__ = "media_alternative"
    name = Column(String(255))
    hoster = Column(JSONEncodedDict())
    audio = Column(JSONEncodedDict())
    partId = Column(Integer, ForeignKey(Part.id))
    part = relationship(Part, backref=backref('alternatives'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('alternatives'))

    def __init__(self, part):
        self.name = ''
        self.hoster = ''
        self.part = part
        self.alternativeParts = []
        self.audio = ''
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Alt:")
        if self.audio:
            ret.append(self._indent*" "+str(self.audio))
        if self.hoster:
            ret.append(self._indent*" "+self.hoster)
        if self.name:
            ret.append(indent*" "+self.name)
        for altP in self.getSubs():
            altP._indent = indent+2
            ret.append(unicode(altP))
        return "\n".join(ret)
    def createSub(self):
        sub = AlternativePart(self)
        return sub
    def getSubs(self):
        return self.alternativeParts

class AlternativePart(Base, BaseMedia):
    __tablename__ = "media_alternative_part"
    name = Column(String(255))
    url = Column(String(255))
    num = Column(String(4))
    pinfo = None
    alternativeId = Column(Integer, ForeignKey(Alternative.id))
    alternative = relationship(Alternative, backref=backref('alternativeParts'))
    pageId = Column(Integer, ForeignKey(Page.id))
    page = relationship(Page, backref=backref('alternativeParts'))
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
        return "\n".join(ret)
