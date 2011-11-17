import time
import config
import logging

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '


class WinHandler(logging.Handler): # Inherit from logging.Handler
    def __init__(self, log_win):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        self.log_win = log_win
    def emit(self, record):

        log_colors = { logging.ERROR: config.colors.esc_RED_BLACK,
                       logging.INFO: config.colors.esc_GREEN_BLACK,
                       logging.WARNING: config.colors.esc_YELLOW_BLACK,
                       logging.DEBUG: config.colors.esc_BLUE_BLACK
                    }
        message = record.getMessage().replace("\n","")
        MAX = 170
        if len(message) > MAX:
            message = message[:MAX]+"..."
        if message.startswith('NO NEWLINE'):
            self.log_win.add_line('%s[%s%s%s]:%s' % (timestamp(), log_colors[record.levelno], record.name, config.colors.esc_end, message), extra=continued)
        else:
            self.log_win.add_line('%s[%s%s%s]:%s' % (timestamp(), log_colors[record.levelno], record.name, config.colors.esc_end, message))


def setLogHandler(win_mgr = None):
    types = {'logconsole': logging.StreamHandler()}
    if win_mgr:
        types['logwin'] = WinHandler(win_mgr.log)

    for type in types:
        if config.log['ALL'][type]:
            for i in config.logger:
                if 'level' in config.log['ALL']:
                    level = config.log['ALL']['level']
                if 'format' in config.log['ALL']:
                    format = config.log['ALL']['format']
                if type in config.log['ALL']:
                    if not config.log['ALL'][type]:
                        continue
                    if 'level' in config.log['ALL'][type]:
                        level = config.log['ALL'][type]['level']
                    if 'format' in config.log['ALL'][type]:
                        format = config.log['ALL'][type]['format']
                if i in config.log:
                    if 'level' in config.log[i]:
                        level = config.log['ALL']['level']
                    if 'format' in config.log[i]:
                        format = config.log['ALL']['format']
                    if type in config.log[i]:
                        if not config.log[i][type]:
                            continue
                        if 'level' in config.log[i][type]:
                            level = config.log[i][type]['level']
                        if 'format' in config.log[i][type]:
                            format = config.log[i][type]['format']
                handler = types[type]
                handler.setLevel(level)
                formatter = logging.Formatter(format)
                handler.setFormatter(formatter)
                config.logger[i].addHandler(handler)

    import sys
    _oldexcepthook = sys.excepthook
    def handleException(excType, excValue, traceback):
        _oldexcepthook(excType, excValue, traceback)
        logging.getLogger().error("Uncaught exception", exc_info=(excType, excValue, traceback))
    sys.excepthook = handleException
