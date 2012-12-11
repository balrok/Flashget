import os
import glob
import imp
import logging
import inspect
import re

log = logging.getLogger('tools.extension')

# This module provides a simple extension interface
# An extension is a class which gets autoloaded by the extensionregistrator via a specified directory (loadFolder)
# After that each individual extension can be retrieved by its name or with a string, which matches the regex from the extension
# To create new Extensions they need to inherit from this Extension class

class Extension(object):
    ename = None # name is required
    eregex = '' # regex can be empty
    eloewestPriority = False # this extension should be used just as last resort (mostly when very generic regexes)


def get_subclasses(mod, cls):
    """Yield the classes in module ``mod`` that inherit from ``cls``"""
    for name, obj in inspect.getmembers(mod):
        if hasattr(obj, "__bases__"):
            if cls in obj.__bases__:
                yield obj

class ExtensionRegistrator(object):
    def __init__(self):
        self.extensions = []

    def loadFolder(self, dirName):
        # get all .py files from this folder
        files = [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(dirName)+"/*.py")]
        for f in files:
            mod = imp.load_source(f, dirName+f+".py")
            for ext in get_subclasses(mod, Extension):
                if ext not in self.extensions:
                    self.register(ext)

    def register(self, ext):
        if ext in self.extensions:
            return
        if not ext.ename or ext.ename == '':
            raise Exception('Each extension needs a name')
        if self.getExtensionByName(ext.ename):
            return
            raise Exception('The Name of the extension should be unique (%s, %s)' % (ext.ename, repr(ext)))
        log.info('Registered '+ext.ename)
        if ext.eregex:
            if isinstance(ext.eregex, str) or isinstance(ext.eregex, unicode):
                ext.eregex = re.compile(ext.eregex)
        self.extensions.append(ext)

    def getExtensionByName(self, name):
        for i in self.extensions:
            if i.ename == name:
                return i

    def getExtensionByRegexStringMatch(self, string):
        match = None
        for i in self.extensions:
            if i.eregex:
                if i.eregex.match(string):
                    if i.eloewestPriority:
                        match = i
                    else:
                        return i
        return match
