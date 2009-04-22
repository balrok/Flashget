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
        str = '[' + config.colors.esc_GREEN_BLACK + self.prefix + config.colors.esc_end + ']: '+ str
        self.log_win.add_line(timestamp() + str)

    def error(self, str):
        str = '[' + config.colors.esc_RED_BLACK + self.prefix + config.colors.esc_end + ']: '+ str
        self.log_win.add_line(timestamp() + str)

    def warning(self, str):
        str = '[' + config.colors.esc_YELLOW_BLACK + self.prefix + config.colors.esc_end + ']: '+ str
        self.log_win.add_line(timestamp() + str)
