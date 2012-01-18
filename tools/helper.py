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
    while True:
        pos1 = data.find(startstr, startpos)
        if pos1 == -1:
            break
        pos1 += len(startstr)
        pos2 = data.find(endstr, pos1)
        if pos2 == -1:
            break
        startpos = pos2 + len(endstr)
        yield data[pos1:pos2]

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



def format_bytes(bytes):
    if bytes is None:
        return 'N/A'
    if bytes > (1024**2):
        bytes = float(bytes / (1024.0**2))
        suffix = 'Mb'
    elif bytes <= (1024**2):
        bytes = float(bytes / 1024.0)
        suffix = 'kb'
    return '%.2f%s' % (bytes, suffix)

def calc_percent(current, all):
    if current is None:
        return '---.-%'
    return '%5s' % ('%3.1f' % (float(current) / float(all) * 100.0))

_calc_eta_cache = {}
import time
def calc_eta(start, total, current):
    now = time.time()
    if total is None or now-start == 0:
        return '--:--'
    if current == 0:
        return '--:--'
    eta = long((float(total) - float(current)) / (float(current) / (now-start)))
    (eta_mins, eta_secs) = divmod(eta, 60)
    return '%02d:%02d' % (eta_mins, eta_secs)

def calc_speed(start, bytes):
    now = time.time()
    dif = now - start
    if bytes == 0 or dif < 0.001: # One millisecond
        return '%10s' % '---b/s'
    return '%10s' % ('%s/s' % format_bytes(float(bytes) / dif))
