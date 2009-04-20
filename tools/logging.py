import sys
import tools.display as display
import config
import time

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '

class LogHandler(object):
    def __init__(self, prefix, parent = None):
        self.prefix = prefix
        self.parent = parent
        if self.parent:
            self.prefix =  parent.prefix + ':' + self.prefix
        self.log_win = config.win_mgr.log

    def info(self, str):
        str = '[' + self.prefix + ']: '+ str
        self.log_win.add_line(timestamp()+ str)

    def error(self, str):
        str = '[' + self.prefix + ']: '+ str
        self.log_win.add_line(timestamp() + str)

    def warning(self, str):
        str = '[' + self.prefix + ']: '+ str
        self.log_win.add_line(timestamp() + str)
