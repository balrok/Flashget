import sys

def color(color, str):
# http://www.siafoo.net/snippet/88
    if color is 'red':
        str = '\033[1;31m' + str
    if color is 'green':
        str = '\033[1;32m' + str
    if color is 'yellow':
        str = '\033[1;33m' + str
    return str+'\033[1;m'


class LogHandler(object):
    def __init__(self, type, parent = None):
        self.type   = type
        self.parent = parent
        self.intendent = 0
        if self.parent:
            self.intendent += self.parent.intendent + len(self.parent.type)
            print self.intendent

    def info(self, str):
        str = '[' + color('green', self.type) + ']: '+ str
        print str.zfill(self.intendent).replace('0',' ')
    def error(self, str):
        str = '[' + color('red', self.type) + ']: '+ str
        print str.zfill(self.intendent).replace('0',' ')

    def warning(self, str):
        str = '[' + color('yellow', self.type) + ']: '+ str
        print str.zfill(self.intendent).replace('0',' ')
