from .page import Page
from .stream import BaseStream
from .config import config

from .youtubedlwrapper import YoutubedlWrapper


try:
    from compatible.urlresolver.curlresolver import getPlugins as getURPlugins
except:
    ur_plugins = False
else:
    ur_plugins = True

from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileLocator, PluginFileAnalyzerMathingRegex

import re
import os

plugins = PluginManager(plugin_locator=PluginFileLocator([PluginFileAnalyzerMathingRegex("all", "^[a-zA-Z][a-zA-Z_]*\.py$")]))
plugins.setCategoriesFilter({
   "Page" : Page,
})

def loadExtension():
    # folder from this project
    path = os.path.dirname(os.path.abspath(__file__))

    pathes = []
    pathes.append(os.path.join(path, 'pages'))
    # folder from config
    # for con in ('page_extension_dir'):
    #     c_path = config.get(con, "")
    #     if len(c_path) > 1:
    #         pathes.append(c_path)
    plugins.setPluginPlaces(pathes)
    plugins.collectPlugins()

def getPageByLink(link):
    loadExtension()
    for pluginInfo in plugins.getPluginsOfCategory("Page"):
        if re.match(pluginInfo.plugin_object.eregex, link):
            obj = pluginInfo.plugin_object.__class__()
            obj.setLink(link)
            return obj
def getAllPages():
    loadExtension()
    return [(p.plugin_object, p.path) for p in plugins.getPluginsOfCategory("Page")]

def getStreamByLink(link):
    return YoutubedlWrapper(link)

def getAllStreams():
    # TODO deprecated
    return []
