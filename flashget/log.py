import logging
import logging.config
import sys
import os

logFile = os.path.expanduser(os.path.join('~', '.flashget.verbose.log'))
logFileError = os.path.expanduser(os.path.join('~', '.flashget.error.log'))

logging.config.dictConfig({
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
        "debug_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": logFile,
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "standard",
            "filename": logFileError,
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'debug_file_handler', 'error_file_handler'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
})

_oldexcepthook = sys.excepthook
def handleException(excType, excValue, traceback):
    _oldexcepthook(excType, excValue, traceback)
    logging.getLogger().error("Uncaught exception", exc_info=(excType, excValue, traceback))
sys.excepthook = handleException
