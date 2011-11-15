# vim: set fileencoding=utf-8 :
from htmlentitydefs import entitydefs
import inspect

def getCaller():
    ret = ""
    ret += str(inspect.stack()[2][1])
    ret += ": "+str(inspect.stack()[2][2])
    return ret

def remove_html(txt):
    txt = txt.replace('&amp;', '&') # cause things like &amp;auml; are possible ~_~
    for i in entitydefs:
        txt = txt.replace(i, '&'+entitydefs[i])
    for x in textextractall(txt, '&#', ';'):
        if not x:
            break
        if len(x) == 4:
            txt = txt.replace('&#%s;' % x, unichr(int(x)))
        elif len(x) == 3:
            txt = txt.replace('&#%s;' % x, chr(int(x)))
    return txt

def normalize_title(str):
    return str.replace('/', '_')

def urldecode(str):
    str = str.replace('%3A', ':')
    str = str.replace('%2F', '/')
    return str

def textextract(data, startstr, endstr, startpos = 0):
    ''' extracts a text from data, which is between startstr and endstr
        if startstr is '' it will extract from the beginning of data
        if endstr   is '' it will extract until the end of data
        the optional parameter startpos will indicate the startposition from where startstr will be searched
        and if startpos is something else than 0 it will return a tuple of the extracted string and the endposition of this string '''
    if startstr == '':
        pos1 = startpos
    else:
        pos1 = data.find(startstr, startpos)
        if pos1 < 0:
            return None
        pos1 += len(startstr)

    if endstr == '':
        return data[pos1:]
    pos2 = data.find(endstr, pos1)
    if pos2 < 0:
        return None
    if startpos != 0:
        return (data[pos1:pos2], pos2)
    return data[pos1:pos2]


def textextractall(data, startstr, endstr):
    startpos  = 0
    foundlist = []
    while True:
        pos1 = data.find(startstr, startpos)
        if pos1 < 0:
            return foundlist
        pos1 += len(startstr)
        pos2 = data.find(endstr, pos1)
        if pos2 < 0:
            return foundlist
        startpos = pos2 + len(endstr) + 1
        foundlist.append(data[pos1:pos2])

class SmallId(object):
    ''' this class is used to produce small ids
        call it with a = SmallId(log, start)
        where log is a pointer to the logging module, and start will be the lowest integer, which gets used
        for producing the ids '''
    ''' this class then provides the function new(), with which you can create a new id, which will be as small as possible
        and free(id) where you can free an id '''
    def __init__(self, log, start):
        self.ids = [0]
        self.log = log
        self.start = start

    def free(self, id):
        self.ids[id - self.start] = 0
        if self.log:
            self.log.info('freeing id %d' % id)

    def new(self):
        for i in xrange(0, len(self.ids)):
            if self.ids[i] == 0:
                break
        else:
            i += 1
            self.ids.append(1)
        self.ids[i] = 1
        if self.log:
            self.log.debug('using id %d' % (i + self.start))
        return i + self.start


def get_aes(key, log = None):
    # import our aes-module here, so we need to call the init only once
    try:
        from Crypto.Cipher import AES
        if log: # after import in case of error, this wouldn't be displayed
            log.info('using pycrypto aes')
        return AES.new(key)
    except:
        if log: # before import so in case of error we know which aes-module it tried to load
            log.info('using pure python aes')
        import aes
        return aes.rijndael(key)



is_array = lambda var: isinstance(var, (list, tuple))
