import config
import tools.defines as defs

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

class Media(object):
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
        for part in self.parts:
            part._indent = indent + 2
            ret.append(str(part))
        return "\n".join(ret)

class Part(object):
    def __init__(self):
        self.name = ''
        self.num = 0
        self.media = None
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
        for alt in self.alternatives:
            alt._indent = indent+2
            ret.append(str(alt))
        return "\n".join(ret)

class Alternative(object):
    def __init__(self):
        self.name = ''
        self.hoster = ''
        self.part = None
        self.alternativeParts = []
        self._indent = 0 # used for printing
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"Alt:")
        if self.hoster:
            ret.append(indent*" "+self.hoster)
        if self.name:
            ret.append(indent*" "+self.name)
        for altP in self.alternativeParts:
            altP._indent = indent+2
            ret.append(str(altP))
        return "\n".join(ret)

class AlternativePart(object):
    def __init__(self):
        self.name = ''
        self.alternative = None
        self.url = ''
        self.pinfo = None
        self._indent = 0 # used for printing
    def __str__(self):
        ret = []
        indent = self._indent
        ret.append(self._indent*" "+"AltPart:")
        if self.name:
            ret.append(indent*" "+self.name)
        if self.url:
            ret.append(indent*" "+self.url)
        if self.pinfo:
            ret.append(indent*" "+self.pinfo)
        return "\n".join(ret)
