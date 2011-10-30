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
class Page(object):
    TYPE_UNK    = 0
    TYPE_MULTI  = 1
    TYPE_SINGLE = 2

    def pages_init__(self):
        self.log = log
        self.data = {}
        self.parts = []
        self.media = None

    def setPinfo(self, alternativePart):
        alternative = alternativePart.alternative
        part = alternative.part
        media = part.media

        pinfo = VideoInfo(alternativePart.url, self.log)
        pinfo.name = media.name
        pinfo.title = ""
        if part.num:
            pinfo.title = part.num+": "
        pinfo.title += part.name
        if alternativePart.num:
            pinfo.title += '_'+str(num)
        self.log.info('added url: %s -> %s' % (pinfo.title, pinfo.url))
        alternativePart.pinfo = pinfo


def save(self):
    session.add(self)
    subs = self.getSubs()
    if subs:
        session.add_all(subs)
    session.commit()
def getSubs(self):
    return None
Base.id = Column(Integer, primary_key = True)
Base.save = save
Base.getSubs = getSubs

class Media(Base):
    __tablename__ = "media"
    name = Column(String(255))

    def __init__(self, name):
        if not name:
            raise Exception('Name must be set')
        self.name = name
        self.parts = []
        self._indent = 0 # used for printing

    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Media:")
        ret.append(indent*" "+self.name)
        for part in self.getSubs():
            part._indent = indent + 2
            ret.append(unicode(part))
        return "\n".join(ret)
    def createSub(self):
        sub = Part(self)
        self.parts.append(sub)
        return sub
    def getSubs(self):
        return self.parts

class Part(Base):
    __tablename__ = "media_part"
    name = Column(String(255))
    num = Column(String(4))
    mediaId = Column(Integer, ForeignKey('media.id'))
    media = relationship("Media", backref=backref('media', order_by=id))

    def __init__(self,media):
        self.name = ''
        self.num = 0
        self.media = media
        self.alternatives = []
        self._indent = 0 # used for printing
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
        self.alternatives.append(sub)
        return sub
    def getSubs(self):
        return self.alternatives

class Alternative(Base):
    __tablename__ = "media_alternative"
    name = Column(String(255))
    hoster = Column(String(255))
    audio = Column(String(255))
    partId = Column(Integer, ForeignKey('media_part.id'))
    part = relationship("Part", backref=backref('media_part', order_by=id))

    def __init__(self, part):
        self.name = ''
        self.hoster = ''
        self.part = part
        self.alternativeParts = []
        self._indent = 0 # used for printing
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
        self.alternativeParts.append(sub)
        return sub
    def getSubs(self):
        return self.alternativeParts

class AlternativePart(Base):
    __tablename__ = "media_alternative_part"
    name = Column(String(255))
    url = Column(String(255))
    num = Column(String(4))
    alternativeId = Column(Integer, ForeignKey('media_alternative.id'))
    alternative = relationship("Alternative", backref=backref('media_alternative', order_by=id))

    def __init__(self, alternative):
        self.name = ''
        self.alternative = alternative
        self.url = ''
        self.pinfo = None
        self._indent = 0 # used for printing
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
