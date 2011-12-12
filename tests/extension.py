from tools.extension import *

a = ExtensionRegistrator()
a.loadFolder('tools/pages/')

print a.getExtensionByName('animeloads')
print a.getExtensionByRegexStringMatch('http://www.kinox.to')
