from tools.url import UrlMgr
from tools.helper import textextract, textextractall
import re
import os

import logging
log = logging.getLogger('pyload')

import imp

class Pyload(object):

    def getFiles(self, dirs):
        latest=self.latest
        url = UrlMgr(url='https://bitbucket.org/spoob/pyload/src/'+latest+'/'+('/'.join(dirs)))
        items = textextractall(url.data, '<td class="name filename"><a href="/spoob/pyload/src/'+latest+'/'+('/'.join(dirs))+"/", '"')
        basePath = 'pyload'
        for i in dirs:
            basePath = os.path.join(basePath, i)
        if os.path.isdir(basePath) is False:
            os.makedirs(basePath)
        open(os.path.join(basePath, '__init__.py'), "w").write("")
        for i in items:
            if i == '__init__.py':
                continue
            url = UrlMgr(url='https://bitbucket.org/spoob/pyload/raw/'+latest+'/'+('/'.join(dirs))+"/"+i)
            data = url.data
            data = data.replace('  self.pyfile.name = ', '  pass # flashget remove: self.pyfile.name = ')
            data = data.replace('  pyfile.name = ', '  pass # flashget remove: pyfile.name = ')
            data = data.replace('from UploadkingCom', 'from module.plugins.hoster.UploadkingCom')
            data = data.replace('from interaction.', 'from module.interaction.')
            data = re.sub('from module\.', 'from pyload.module.', data)
            path = os.path.join(basePath, i)
            open(path, "w").write(data)
            try:
                os.remove(path+"c")
            except:
                pass
            yield (i, data,path)

    def run(self):
        url = UrlMgr(url='https://bitbucket.org/spoob/pyload/changesets')
        self.latest = textextract(url.data, '<li><a href="/spoob/pyload/src/', '"')



        for folder in ['plugins', 'network', 'common', 'interaction']:
            dirs = ['module', folder]
            for i,data,path in self.getFiles(dirs):
                pass

        for folder in ['internal', 'hoster']:
            dirs = ['module', 'plugins', folder]
            for i,data,path in self.getFiles(dirs):
                pass
        dirs = ['module']
        for i,data,path in self.getFiles(dirs):
            pass

        path = os.path.join("pyload", '__init__.py')
        open(path, "w").write(" ")

        dirs = ['module', 'plugins', 'hoster']
        for i,data,path in self.getFiles(dirs):
            print i
            print path
            try:
                mod = imp.load_source(i[:-3], path)
            except:
                print "err"
            else:
                yield mod
