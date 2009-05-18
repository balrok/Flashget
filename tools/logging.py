import sys
import config
import time
import os
from tools.defines import Log

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '


log_colors = { Log.ERROR: config.colors.esc_RED_BLACK,
               Log.BUG: config.colors.esc_RED_BLACK,
               Log.INFO: config.colors.esc_GREEN_BLACK,
               Log.WARNING: config.colors.esc_YELLOW_BLACK
            }

class LogHandler(object):
    def __init__(self, prefix, parent = None):
        self.name = prefix
        self.prefix = prefix
        self.parent = parent
        if self.parent:
            self.prefix =  parent.prefix + ':' + self.prefix
        self.log_win = config.win_mgr.log

    def info(self, str):
        self.log(Log.INFO, str)
    def error(self, str):
        self.log(Log.ERROR, str)
    def bug(self, str):
        self.log(Log.BUG, str)
    def warning(self, str):
        self.log(Log.WARNING, str)

    def should_log(self, place, type):
        if self.name in config.log[place]['extra_types']:
            return config.log[place]['extra_types'][self.name] & type
        return config.log[place]['types'] & type

    def log(self, type, str):
        if self.should_log('file', type):
            if self.name in config.log['file']['extra_file']:
                path = config.log['file']['extra_file'] + '.' + Log.str[type]
            else:
                path = Log.str[type]
            stream = open(os.path.join(config.log['file']['dir'], path), 'a')
            stream.write(time.strftime('%H:%M:%S') + ' ' + self.prefix + ' ' + str.encode('utf-8') + '\n')
        if self.should_log('display', type):
            str = '[' + log_colors[type] + self.prefix + config.colors.esc_end + ']: '+ str
            self.log_win.add_line(timestamp() + str)
