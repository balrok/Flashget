# vim: set fileencoding=utf-8 :

html_dict = {'&Auml;':u'Ä', '&auml;':u'ä', '&Euml;':u'Ë', '&euml;':u'ë', '&Iuml;':u'Ï', '&iuml;':u'ï',
            '&Ouml;':u'Ö', '&ouml;':u'ö', '&Uuml;':u'Ü', '&uuml;':u'ü', '&Aacute;':u'Á', '&aacute;':u'á',
            '&Eacute;':u'É', '&eacute;':u'é', '&Iacute;':u'Í', '&iacute;':u'í', '&Oacute;':u'Ó', '&oacute;':u'ó',
            '&Uacute;':u'Ú', '&uacute;':u'ú', '&Agrave;':u'À', '&agrave;':u'à', '&Egrave;':u'È', '&egrave;':u'è',
            '&Igrave;':u'Ì', '&igrave;':u'ì', '&Ograve;':u'Ò', '&ograve;':u'ò', '&Ugrave;':u'Ù', '&ugrave;':u'ù',
            '&Acirc;':u'Â', '&acirc;':u'â', '&Ecirc;':u'Ê', '&ecirc;':u'ê', '&Icirc;':u'Î', '&icirc;':u'î',
            '&Ocirc;':u'Ô', '&ocirc;':u'ô', '&Ucirc;':u'Û', '&ucirc;':u'û', '&Aring;':u'Å', '&aring;':u'å',
            '&deg;':u'°', '&szlig;':u'ß', '&frac12;':u'½', '&amp;':u'&', '&apos;':u'\''}

def remove_html(txt):
    for i in html_dict:
        txt = txt.replace(i, html_dict[i])
    return txt


def normalize_title(str):
    str = str.replace('/', '_')
    return str.decode('iso-8859-1')


def textextract(data, startstr, endstr):
    if startstr == '':
        pos1 = 0
    else:
        pos1=data.find(startstr)
        if pos1 < 0:
            return
        pos1 += len(startstr)

    if endstr == '':
        return data[pos1:]
    pos2 = data.find(endstr, pos1)
    if pos2 < 0:
        return
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
        self.log.info('freeing id %d' % id)

    def new(self):
        for i in xrange(0, len(self.ids)):
            if self.ids[i] == 0:
                break
        else:
            i += 1
            self.ids.append(1)
        self.ids[i] = 1
        self.log.info('using id %d' % (i + self.start))
        return i + self.start
