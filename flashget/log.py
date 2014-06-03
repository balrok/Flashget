import logging
import logging.config
import sys
import os


loggingConfig = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)5s] %(name)17s:%(lineno)03d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'INFO',
            'class':'logging.StreamHandler',
            "formatter": "standard",
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'debug_file_handler', 'error_file_handler'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

try:
    os.mkdir(os.path.expanduser(os.path.join('~', '.flashget')))
except:
    pass
else:
    logFile = os.path.expanduser(os.path.join('~', '.flashget', 'verbose.log'))
    logFileError = os.path.expanduser(os.path.join('~', '.flashget', 'error.log'))
    loggingConfig['handlers']["debug_file_handler"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": logFile,
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    loggingConfig["handlers"]["error_file_handler"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "standard",
            "filename": logFileError,
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }

logging.config.dictConfig(loggingConfig)

_oldexcepthook = sys.excepthook
def handleException(excType, excValue, traceback):
    _oldexcepthook(excType, excValue, traceback)
    logging.getLogger().error("Uncaught exception", exc_info=(excType, excValue, traceback))
sys.excepthook = handleException
