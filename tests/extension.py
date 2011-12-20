#!/usr/bin/python
from tools.extension import *

a = ExtensionRegistrator()
a.loadFolder('tools/pages/')

print "byName"
print "------"
for i in ['animeloads_a', 'animeloads_s']:
    print "%s -> %s" % (i, str(a.getExtensionByName(i)))

print ""

print "byRegex"
print "-------"
for i in ['http://www.anime-loads.org/media/2188', 'http://www.kinox.to', 'anime-loads', 'anime-loads.org/media/asia',
    'http://kinox.to/Movies.html', 'http://kinox.to/Stream/A_Beautiful_Life.html']:
    print "%s -> %s" % (i, str(a.getExtensionByRegexStringMatch(i)))
