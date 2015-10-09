Version 3.2 (xx.2015)
===========================
- have a config-home were logging/configs take place
- more simplification (just one cache implementation, no db)
- started writing tests - but now abandoned (I would need some non-copyright streams for this)
- captcha support
- removed/added animeloads
- tried different gui systems: qt,tk,gtk - all to complicated
- use gooey as gui system - it just starts from my argparse config
- commandline:
	- limit download speed
	- resume downloads when no arguments
	- interactive mode to select stream files
- use yapsy as plugin manager
	- could again remove some of my own code - yapsy seems ok
- use urlresolver api for getting flash-download url
	- this is a bigger change as it makes this tool a bit less fragile and
		I don't need to put so much time on developing these things anymore
- unified config-setting/loading, commandline and gui (via gooey)

Version 3 (16.05.2014)
===========================
- python3 compatibility
- removed broken streams and not used library
- some new streams and pages
- static code analyze with landscape.io
- test automation with travis-ci
- simplification and cleanup in all parts of the code
- removed many threads
- renaming tools to flashget and having everything more like other python projects
- the config file is now ini format and can be in the home directory
- have a setup.py for installing

Version 2 (30.12.2012)
===========================
- big cleanup: removed curses and other not used tools
- don't use my http-lib but requests
- use argparse

Version 2 (30.12.2011)
===========================
- stream_extract: implement putlocker
- improved cache interface
- added new caches (Leveldb, HypterTable, KyotoCacheComp (=Kyotocabinet with compression turned on))
- urlmanager will look if it received binary data and won't cache it
- http library improvements (header parsing, error handling)
- nicely close the program and join all threads
- own extension manager
- extension manager for pages and streams
- direct download of streams via commandline
- streams are objects now too
- support https


Version 2 (17.Nov 2011)
===========================
after so long time another version increment is needed
change in version numbering cause of simplicity

- allow disabling of curses interface
- improved http library with many bugfixes
- (re-)implement animeloads, eliteanimes, movie-loads, kinox.to
- extracting all data from sites and store it into a mysql database
- improved extract-interface
- allow multithreaded extract-all through specifying start and amount
- replaced my own cache implementation with kyotocabinet cause filesystem got too slow
- dropped idea of client-server style program

Version 1.1 (25.Jul 2009)
===========================
again no particular reason for this, i just think this version is stable (:

- generic xvid implementation + some supported pages for it
- my http-implementation
  - bugfix: correctly get the port from a link
  - bugfix: keywords (like content-length) in http-protcol aren't casesensitive
  - using a dns-cache
- added crypt-it container.. but currently they don't realy work.. you just can
  display the links inside a container
- first idea + some code about making this program in a client-server style
  to support later more guis (but currently doesn't work)
- many other smaller things, just use git cherry -v 7e46d271


Version 1
==============
there is no particular reason why exactly this revision got version 1, it's
just that i can add a version with the commandline-option

cause this is the first version, i will mostly list features here:
 - tools for easy adding new commandline options
 - own http-class which implements keep-alive and which is (compared to other python http-libs) very small
 - classes to handle the webpages, where flashfiles can be found. supported pages:
    + anime-loads, animekiwi, anime-junkies, youtube, kino.to
 - classes to handle the flv-streams, which can extract a direct-download link. supported streams:
    + veoh, eatlime, megavideo, hdweb, sevenload, youtube, imeem, hdshare, zeec, plain (direct dl-link is inside html)
 - class for logging + config-params to filter some logging stuff
    not very advanced yet
 - class for creating a gui in ncurses
    not very advanced yet + has some bugs with the scrolling in those logs
    but has already some nice features and is, i think, quite fast

