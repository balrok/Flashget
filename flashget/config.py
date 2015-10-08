# -*- coding: utf-8 -*-
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import os
from .helper import open
import tempfile


config = {}

# TODO implement a checking method which looks if all required configs are set
# and if all directories are writeable


def updateConfig(newConfig):
    global config
    for k in newConfig:
        if newConfig[k] is None:
            continue
        if k in ['cache_dir', 'cache_dir_for_flv', 'flash_dir', 'stream_extension_dir', 'page_extension_dir']:
            config[k] = os.path.expanduser(newConfig[k])
        else:
            config[k] = newConfig[k]

def getDefaultConfig():
    return {
            'cache_dir': os.path.join(tempfile.gettempdir(), 'flashget', 'cacheHtml'),
            'cache_dir_for_flv': os.path.join(tempfile.gettempdir(), 'flashget', 'cacheFlv'),
            'flash_dir': os.path.join('~', '.flashget', 'downloads'),
            'dl_instances': 6,
            'dl_title': 'tmp',
            'dl_name': 'tmp',
            'limit': 0,
            'stream_extension_dir': os.path.join('~', '.flashget', 'streamExtensions'),
            'page_extension_dir': os.path.join('~', '.flashget', 'pageExtensions'),
            'captcha_selfsolve': True,
            'captcha_selfsolve_imgprogram': 'xv',
            'captcha9kw_solve': False,
            'captcha9kw_pass': 'Enter your pass key',
            'interactive': False
            }

def getConfigLocations():
    return [os.path.join('etc', 'flashget.cfg'),
            os.path.expanduser(os.path.join('~', '.flashget', 'config.cfg')),
            '.flashget.cfg']

def loadConfig():
    global config
    config = getDefaultConfig()

    # todo make this more generic:
    if not os.path.exists(os.path.expanduser(os.path.join('~', '.flashget'))):
        os.mkdir(os.path.expanduser(os.path.join('~', '.flashget')))
    configFiles = getConfigLocations()
    if not os.path.isfile(configFiles[1]):
        createConfigFile(configFiles[1], getDefaultConfig())
    configP = configparser.SafeConfigParser(allow_no_value=True)
    configP.read(configFiles)
    updateConfig(dict(configP.items("DEFAULT")))
    return config


def createConfigFile(path, config):
    parser = configparser.SafeConfigParser(allow_no_value=True)
    def cset(index, parser_=parser, config_=config):
        parser_.set('', index, unicode(config_[index]))

    parser.add_section('')
    parser.set('', '; temporary caches for http-data - you have to clean them by hand since flashget won\'t purge them')
    parser.set('', '; cache for html pages (you also might put it into /tmp)')
    cset('cache_dir')
    parser.set('', '; cache for the large streamdownloads (if you clean it, the downloads can\'t be resumed')
    parser.set('', 'cache_dir_for_flv', config['cache_dir_for_flv'])
    parser.set('', '; all finished flashdownloads go in this directory and will be deleted from the cachedir')
    cset('flash_dir')
    parser.set('', '; how many downloads will be processed in parallel')
    parser.set('', '; this only works for one instance of this program')
    cset('dl_instances')
    parser.set('', '; default download title, if you download directly from a stream - but better use commandline argument')
    cset('dl_title')
    parser.set('', '; default download name, if you download directly from a stream - but better use commandline argument')
    cset('dl_name')
    parser.set('', '; limit the bandwidth in kb/s - 0 for no limit')
    cset('limit')
    parser.set('', '; It is possible for you to extend this program by other streamtypes or pages - please look at the existing ones how to program them')
    cset('stream_extension_dir')
    cset('page_extension_dir')
    parser.set('', '; Captcha configs')
    parser.set('', '; solve the captcha by yourself')
    cset('captcha_selfsolve')
    parser.set('', '; it will execute this program with the image as parameter')
    cset('captcha_selfsolve_imgprogram')
    cset('captcha9kw_solve')
    cset('captcha9kw_pass')
    parser.set('', '; When interactive it will ask which stream to take')
    cset('interactive')

    with open(path, 'w+') as fp:
        parser.write(fp)
