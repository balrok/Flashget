
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
    def __init__(self, type):
        self.type = type
    def info(self, str):
        str = '[' + color('green', self.type) + ']: '+ str
        print str
    def error(self, str):
        str = '[' + color('red', self.type) + ']: '+ str
        print str

    def warning(self, str):
        str = '[' + color('yellow', self.type) + ']: '+ str
        print str
