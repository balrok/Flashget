# -*- coding: utf-8 -*-
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import os


config = {}

def updateConfig(newConfig):
    global config
    for k in newConfig:
        if k in ['cache_dir', 'cache_dir_for_flv', 'flash_dir', 'stream_extension_dir', 'page_extension_dir']:
            config[k] = os.path.expanduser(newConfig[k])
        else:
            config[k] = newConfig[k]

def loadConfig():
    global config
    configFiles = [os.path.join('etc', 'flashget.cfg'), os.path.expanduser(os.path.join('~', '.flashget', 'config.cfg')), '.flashget.cfg']
    if not os.path.exists(os.path.expanduser(os.path.join('~', '.flashget'))):
        os.mkdir(os.path.expanduser(os.path.join('~', '.flashget')))
    if not os.path.isfile(configFiles[1]):
        createConfigFile(configFiles[1])
    for filepath in configFiles:
        if os.path.isfile(filepath):
            configP = configparser.SafeConfigParser(allow_no_value = True)
            configP.read(filepath)
            # TODO parse to int and boolean
            updateConfig(dict(configP.items("DEFAULT")))
    return config

def createConfigFile(path):
    config = configparser.SafeConfigParser(allow_no_value = True)
    config.add_section('')
    config.set('', '; temporary caches for http-data - you have to clean them by hand since flashget won\'t purge them')
    config.set('', '; cache for html pages (you also might put it into /tmp)')
    config.set('', 'cache_dir', os.path.join('~', '.flashget', 'cacheHtml'))
    config.set('', '; cache for the large streamdownloads (if you clean it, the downloads can\'t be resumed')
    config.set('', 'cache_dir_for_flv', os.path.join('~', '.flashget', 'cacheFlv'))
    config.set('', '; all finished flashdownloads go in this directory and will be deleted from the cachedir')
    config.set('', 'flash_dir', os.path.join('~', '.flashget', 'downloads'))
    config.set('', '; how many downloads will be processed in parallel')
    config.set('', '; this only works for one instance of this program')
    config.set('', 'dl_instances', "6")
    config.set('', '; default download title, if you download directly from a stream - but better use commandline argument')
    config.set('', 'dl_title', "tmp")
    config.set('', '; default download name, if you download directly from a stream - but better use commandline argument')
    config.set('', 'dl_name', "tmp")
    config.set('', '; It is possible for you to extend this program by other streamtypes or pages - please look at the existing ones how to program them')
    config.set('', 'stream_extension_dir', os.path.join('~', '.flashget', 'streamExtensions'))
    config.set('', 'page_extension_dir', os.path.join('~', '.flashget', 'pageExtensions'))
    config.set('', '; how many media files should be skipped when using extract all')
    config.set('', 'extractStart', "0")
    config.set('', '; how many media files should be extracted when using extract all')
    config.set('', 'extractAmount', "999999")
    config.set('', '; if you run the caching as client/server (when you have multiple parallel instances) - configure the port here')
    config.set('', 'cachePort', "0")
    config.set('', 'preferHypertable', "False")
    config.set('', 'preferFileCache', "False")

    with open(path, 'w+') as fp:
        config.write(fp)
