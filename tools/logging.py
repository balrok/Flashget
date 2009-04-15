import sys
import tools.display as display
import config
import time

def color(color, str):
    return str
# http://www.siafoo.net/snippet/88
    if color is 'red':
        str = '\033[1;31m' + str
    if color is 'green':
        str = '\033[1;32m' + str
    if color is 'yellow':
        str = '\033[1;33m' + str
    return str+'\033[1;m'

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '

class LogHandler(object):
    def __init__(self, type, parent = None):
        self.type   = type
        self.parent = parent
        if self.parent:
            self.type =  parent.type + ':' + self.type
        self.log_win = config.win_mgr.log


    def info(self, str):
        str = '[' + color('green', self.type) + ']: '+ str
        self.log_win.add_line(timestamp()+ str)

    def error(self, str):
        str = '[' + color('red', self.type) + ']: '+ str
        self.log_win.add_line(timestamp() + str)

    def warning(self, str):
        str = '[' + color('yellow', self.type) + ']: '+ str
        self.log_win.add_line(timestamp() + str)
