from .page import Page
from .stream import BaseStream
from .config import config

try:
    from compatible.urlresolver.curlresolver import getPlugins as getURPlugins
    from compatible.urlresolver.streamhandler_urlresolver import Urlresolver
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
   "Stream" : BaseStream,
})

def loadExtension():
    # folder from this project
    path = os.path.dirname(os.path.abspath(__file__))

    pathes = []
    pathes.append(os.path.join(path, 'pages'))
    pathes.append(os.path.join(path, 'streams'))
    # folder from config
    for con in ('page_extension_dir', 'stream_extension_dir'):
        c_path = config.get(con, "")
        if len(c_path) > 1:
            pathes.append(c_path)
    plugins.setPluginPlaces(pathes)
    plugins.collectPlugins()

def getPageByLink(link):
    loadExtension()
    for pluginInfo in plugins.getPluginsOfCategory("Page"):
        if re.match(pluginInfo.plugin_object.eregex, link):
            pluginInfo.plugin_object.setLink(link)
            return pluginInfo.plugin_object
def getAllPages():
    loadExtension()
    return [(p.plugin_object, p.path) for p in plugins.getPluginsOfCategory("Page")]

def getStreamByLink(link):
    loadExtension()
    for pluginInfo in plugins.getPluginsOfCategory("Stream"):
        print pluginInfo.plugin_object.eregex
        if re.match(pluginInfo.plugin_object.eregex, link):
            pluginInfo.plugin_object.setLink(link)
            return pluginInfo.plugin_object
    if ur_plugins:
        for stream in getURPlugins():
            for d in stream.domains:
                if d != "*" and re.match(".*%s.*"%d, link):
                    plugin = Urlresolver()
                    plugin.setLink(link)
                    return plugin

def getAllStreams():
    loadExtension()
    streams = [(p.plugin_object, p.path) for p in plugins.getPluginsOfCategory("Stream")]
    if ur_plugins:
        for stream in getURPlugins():
            stream.ename = stream.name
            stream.url = "::".join(stream.domains)
            streams.append((stream, stream.__class__.__name__))
    return streams


