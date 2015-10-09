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

# TODO make it oject oriented


def updateConfig(newConfig):
    global config
    for k in newConfig:
        if newConfig[k] is None:
            continue
        if k in ['cache_dir', 'cache_dir_for_flv', 'flash_dir', 'stream_extension_dir', 'page_extension_dir']:
            config[k] = os.path.expanduser(newConfig[k])
        else:
            config[k] = newConfig[k]

def getConfigInfo():
    return [
                {
                    'id': 'cache_dir',
                    'default': os.path.join(tempfile.gettempdir(), 'flashget', 'cacheHtml'),
                    'help': "temporary caches for http-data - usually leave it like this",
                    'type': 'dir',
                },
                {
                    'id': 'cache_dir_for_flv',
                    'default': os.path.join(tempfile.gettempdir(), 'flashget', 'cacheFlv'),
                    'help': "temporary cache for large stream downloads usually leave it like this",
                    'type': 'dir',
                },
                {
                    'id':'flash_dir',
                    'default': os.path.join('~', '.flashget', 'downloads'),
                    'help': 'all finished flashdownloads go in this directory and will be deleted from the cache',
                    'type': 'dir',
                },
                {
                    'id': 'dl_instances',
                    'default': 3,
                    'help': 'how many downloads will be processed in parallel',
                    'type': 'int',
                    'args': ('--dl_instances', '-d'),
                },
                {
                    'id': 'dl_title',
                    'default': 'notitle',
                    'help': 'How to name the file, when no title can be extracted',
                    'type': 'str',
                    'args': ('--title', '-t'),
                },
                {
                    'id': 'dl_name',
                    'default': 'noname',
                    'help': 'How to name the file, when no name can be extracted',
                    'type': 'str',
                    'args': ('--name', '-n'),
                },
                {
                    'id': 'limit',
                    'default': 0,
                    'help': 'limit the bandwidth in kb/s - 0 for no limit',
                    'type': 'int',
                    'args': ('--limit', '-l'),
                },
                {
                    'id':'captcha_selfsolve',
                    'default': True,
                    'help': 'An image viewer will show you the captcha and you will enter the letters',
                    'type': 'bool',
                    'args': ('--selfsolve', '-s'),
                },
                {
                    'id':'captcha_selfsolve_imgprogram',
                    'default': 'xv',
                    'help': 'The image viewer',
                    'type': 'str',
                },
                {
                    'id':'captcha9kw_solve',
                    'default': False,
                    'help': 'Captcha9kw is an online service, which solves the captchas for you',
                    'type': 'bool',
                },
                {
                    'id':'captcha9kw_pass',
                    'default': 'enter your pass key',
                    'help': '',
                    'type': 'str',
                },
                {
                    'id':'interactive',
                    'default': False,
                    'help': 'In interactive mode you get asked which stream it will download',
                    'type': 'bool',
                    'args': ('--interactive', '-i'),
                },
            ]

def getDefaultConfig():
    info = getConfigInfo()
    ret = {}
    for a in info:
        ret[a['id']] = a['default']
    return ret

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
    info = getConfigInfo()
    parser = configparser.SafeConfigParser(allow_no_value=True)
    def cset(index, parser_=parser, config_=config):
        parser_.set('', index, unicode(config_[index]))

    parser.add_section('')
    for item in info:
        if "help" in item:
            for h in item["help"].split("\n"):
                parser.set('', '; %s' % h)
        value = config[item['id']]
        if item['type'] in ('int', 'bool'):
            value = unicode(value)
        parser.set('', item['id'], value)

    with open(path, 'w+') as fp:
        parser.write(fp)
