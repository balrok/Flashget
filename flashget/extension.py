# coding=utf-8
import os
import glob
import imp
import inspect
import re

# This module provides a simple extension interface
# An extension is a class which gets autoloaded by the extensionregistrator via a specified directory (loadFolder)
# After that each individual extension can be retrieved by its name or with a string, which matches the regex from the extension
# To create new Extensions they need to inherit from this Extension class

class Extension(object):
    ename = None  # name is required
    eregex = ''  # regex can be empty
    ePriority = 0  # Extensions with a higher priority come first - default is 0


def get_subclasses(mod, cls):
    """Yield the classes in module ``mod`` that inherit from ``cls``"""
    for name, obj in inspect.getmembers(mod):
        if hasattr(obj, "__bases__"):
            if cls != obj and cls in obj.mro()[:-1]:
                yield obj


class ExtensionRegistrator(object):
    def __init__(self):
        self.extensions = []
        self.loaded = False

    def loadFolder(self, dir_name):
        self.loaded = True
        # get all .py files from this folder
        files = [os.path.basename(f)[:-3] for f in glob.glob(os.path.realpath(dir_name)+"/*.py")]
        for f in files:
            mod = imp.load_source(f, os.path.join(dir_name,f+".py"))
            for ext in get_subclasses(mod, Extension):
                if ext not in self.extensions:
                    self.register(ext)
        self.extensions.sort(key=lambda x: x.ePriority, reverse=True)

    def register(self, ext):
        if ext in self.extensions:
            return
        if not ext.ename or ext.ename == '':
            raise Exception('Each extension needs a name (%s)' % ext.__name__)
        if self.getExtensionByName(ext.ename):
            raise Exception('The Name of the extension should be unique (%s, %s)' % (ext.ename, repr(ext)))
        if ext.eregex:
            if isinstance(ext.eregex, str) or isinstance(ext.eregex, unicode):
                ext.eregex = re.compile(ext.eregex)
        self.extensions.append(ext)

    def initAll(self, *args):
        for i in range(0, len(self.extensions)):
            self.extensions[i] = self.extensions[i](*args)

    def getExtensionByName(self, name):
        for i in self.extensions:
            if i.ename == name:
                return i

    def getExtensionByRegexStringMatch(self, string):
        for ext in self.getExtensionsByRegexStringMatch(string):
            return ext

    def getExtensionsByRegexStringMatch(self, string):
        for i in self.extensions:
            if i.eregex and i.eregex.match(string):
                yield i
