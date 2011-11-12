import os
import glob
import config
import sys
from tools.page import Page
import logging

log = logging.getLogger('page')

pages = {}

def getClass(link):
    if link == '':
        log.error("empty page added")
        return None
    link = link.lower()
    # urlparts are getting sorted, so that the longer strings getting matched first.. so '' for plain is always the last one.. and "test.com" also comes after "mytest.com"
    urlParts = pages.keys()
    urlParts.sort(key=len, reverse=True)
    for urlPart in urlParts:
        if link.find(urlPart) >= 0:
            classRef = pages[urlPart]
            return Page.getPage(classRef)
    log.error("page %s is not supported, must contain any of those: %s" % (link, str(urlParts)))
    return None


# import all submodules to let them register
__all__ = [ os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py")]
from . import *

# get urlPart and classRef from all submodules
for i in sys.modules.keys():
    for j in __all__:
        if i == 'tools.pages.'+j:
            f = sys.modules[i]
            pages[f.urlPart] = f.classRef
