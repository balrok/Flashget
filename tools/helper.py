
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
        startpos = pos2 + len(endstr) + 1                         # TODO look if this is ok
        foundlist.append(data[pos1:pos2])


