import time
import config
import logging

def timestamp():
    return '('+time.strftime('%H:%M:%S')+') :: '

def setLogHandler():
    types = {'logconsole': logging.StreamHandler()}

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
