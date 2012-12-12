import time
import config
import logging

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '

def setLogHandler():

    if config.log['ALL']:
        for i in config.logger:
            if 'level' in config.log['ALL']:
                level = config.log['ALL']['level']
            if 'format' in config.log['ALL']:
                format = config.log['ALL']['format']
            if i in config.log:
                if 'level' in config.log[i]:
                    level = config.log['ALL']['level']
                if 'format' in config.log[i]:
                    format = config.log['ALL']['format']
            handler = logging.StreamHandler()
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
