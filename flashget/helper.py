# vim: set fileencoding=utf-8 :
try:
    from html.entities import entitydefs
except ImportError:
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
        txt = txt.replace('&'+i, entitydefs[i])
    for s in textextractall(txt, '&#', ';'):
        if s[0] == 'x':
            x = int(s[1:], 16)
        else:
            x = int(s)
        if x >= 128:
            txt = txt.replace('&#%s;' % s, unichr(x))
        else:
            txt = txt.replace('&#%s;' % s, chr(x))
    return txt


def normalize_title(text):
    return text.replace('/', '_')


def urldecode(text):
    return text.replace('%3A', ':').replace('%2F', '/')

def textposextract(data, startstr, endstr, startpos=0):
    ''' extracts a text from data, which is between startstr and endstr
        if startstr is '' it will extract from the beginning of data
        if endstr   is '' it will extract until the end of data
        the optional parameter startpos will indicate the startposition from where startstr will be searched
        returns the text and the position of the last character from text inside data or None, 0 in case of error
    '''
    if startstr == '':
        pos1 = startpos
    else:
        pos1 = data.find(startstr, startpos)
        if pos1 < 0:
            return None, 0
        pos1 += len(startstr)

    if endstr == '':
        return data[pos1:], len(data)
    pos2 = data.find(endstr, pos1)
    if pos2 < 0:
        return None, 0
    return data[pos1:pos2], pos2


def textextract(data, startstr, endstr, startpos=0):
    ''' @see textposextract
        only difference is, that it will just return the text without position
    '''
    text, dummy = textposextract(data, startstr, endstr, startpos)
    return text


def textextractall(data, startstr, endstr):
    assert startstr # it doesn't make sense when this is empty
    assert endstr
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
        for producing the ids
        this class then provides the function new(), with which you can create a new id, which will be as small as possible
        and free(id) where you can free an id '''
    def __init__(self, log, start):
        self.ids = [0]
        self.log = log
        self.start = start

    def free(self, sId):
        self.ids[sId - self.start] = 0
        if self.log:
            self.log.info('freeing id %d', sId)

    def new(self):
        for i in range(0, len(self.ids)):
            if self.ids[i] == 0:
                break
        else:
            i += 1
            self.ids.append(1)
        self.ids[i] = 1
        if self.log:
            self.log.debug('using id %d', i + self.start)
        return i + self.start


is_array = lambda var: isinstance(var, (list, tuple))


def format_bytes(bytesInt):
    if bytesInt is None:
        return 'N/A'
    if bytesInt > (1024**2):
        bytesInt = float(bytesInt / (1024.0**2))
        suffix = 'Mb'
    elif bytesInt <= (1024**2):
        bytesInt = float(bytesInt / 1024.0)
        suffix = 'kb'
    return '%.2f%s' % (bytesInt, suffix)


def calc_percent(current, maximum):
    if current is None:
        return '---.-%'
    return '%5s' % ('%3.1f' % (float(current) / float(maximum) * 100.0))

_calc_eta_cache = {}
import time


def calc_eta(start, total, current):
    now = time.time()
    if total is None or now-start == 0:
        return '--:--'
    if current == 0:
        return '--:--'
    eta = int((float(total) - float(current)) / (float(current) / (now-start)))
    (eta_mins, eta_secs) = divmod(eta, 60)
    return '%02d:%02d' % (eta_mins, eta_secs)


def calc_speed(start, bytesInt):
    now = time.time()
    dif = now - start
    if bytesInt == 0 or dif < 0.001:  # One millisecond
        return '%10s' % '---b/s'
    return '%10s' % ('%s/s' % format_bytes(float(bytesInt) / dif))

import threading


class EndableThreadingClass(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._end = threading.Event()

    def end(self):
        self._end.set()

    def ended(self, wait_blocking=False, timeout=None):
        if wait_blocking:
            return self._end.wait(timeout)
        return self._end.isSet()
