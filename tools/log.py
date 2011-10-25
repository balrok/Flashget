import time
import config
import logging

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '

log_colors = { logging.ERROR: config.colors.esc_RED_BLACK,
               logging.INFO: config.colors.esc_GREEN_BLACK,
               logging.WARNING: config.colors.esc_YELLOW_BLACK,
               logging.DEBUG: config.colors.esc_BLUE_BLACK
            }

class WinHandler(logging.Handler): # Inherit from logging.Handler
    def __init__(self, log_win):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        self.log_win = log_win
    def emit(self, record):
        message = record.getMessage().replace("\n","")
        MAX = 170
        if len(message) > MAX:
            message = message[:MAX]+"..."
        self.log_win.add_line('%s[%s%s%s]:%s' % (timestamp(), log_colors[record.levelno], record.name, config.colors.esc_end, message))
