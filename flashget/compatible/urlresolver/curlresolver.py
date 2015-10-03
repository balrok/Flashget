import sys
import os
import logging
log = logging.getLogger(__name__)


# The purpose of this class is to get as far as possible
# without anybody knowing this class is empty
class Empty(object):
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name, *args, **kwargs):
        try:
            return self.name
        except:
            return Empty
    def __repr__(self, *args, **kwargs):
        return "Empty"
    def __str__(self, *args, **kwargs):
        return "Empty"
    def __nonzero__(self, *args, **kwargs):
        return True
    def __add__(self, *args, **kwargs):
        # add should return the same types as the arguments
        if len(args) > 0:
            return args[0]
        return None

class Addon(Empty):
    def get_setting(self, name):
        # the YoutubeResolver will work with a kodi-plugin
        # so does not return anything useful
        if name == "YoutubeResolver_enabled":
            return False
        if name.endswith("_priority"):
            return 0
        if name.endswith("_enabled"):
            return True
        if name == "allow_universal":
            return True
    def log_debug(self, a, *args):
        log.debug(a, *args)
    def log_error(self, a, *args):
        log.error(a, *args)
    def log(self, a, *args):
        log.info(a, *args)


current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)
urlresolver_path = os.path.join(current_path, "script.module.urlresolver", "lib")
sys.path.append(urlresolver_path)

sys.modules['xbmc'] = Empty()
sys.modules['xbmc'].LOGNOTICE = 0
sys.modules['xbmcaddon'] = Empty()
sys.modules['xbmcaddon'].Addon = Empty
sys.modules['xbmcaddon'].getAddonInfo = Empty
sys.modules['xbmcgui'] = Empty()
sys.modules['xbmcplugin'] = Empty()

#sys.modules['t0mm0'] = t0mm0

sys.modules['t0mm0'] = Empty
sys.modules['t0mm0'].common = Empty
sys.modules['t0mm0.common'] = Empty
sys.modules['t0mm0'].common.addon = Empty #__import__("t0mm0_common_addon")
sys.modules['t0mm0.common.addon'] = Empty #__import__("t0mm0_common_addon")
sys.modules['t0mm0'].common.addon.Addon = Addon #__import__("t0mm0_common_addon")
sys.modules['t0mm0.common.addon.Addon'] = Addon #__import__("t0mm0_common_addon")

sys.modules['t0mm0'].common.net = __import__("t0mm0_common_net")
sys.modules['t0mm0.common.net'] = __import__("t0mm0_common_net")

import urlresolver

path = os.path.join(urlresolver_path, "urlresolver", "plugins")
urlresolver.common.plugins_path = path
urlresolver.plugnplay.set_plugin_dirs(path)

def resolve(url):
    try:
        return urlresolver.resolve(url)
    except:
        log.error("some error happened when resolving")
        return False
