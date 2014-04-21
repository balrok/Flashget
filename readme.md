# Flashget
[![Code Health](https://landscape.io/github/balrok/Flashget/master/landscape.png)](https://landscape.io/github/balrok/Flashget/master)
[![Build Status](https://travis-ci.org/balrok/Flashget.svg?branch=master)](https://travis-ci.org/balrok/Flashget)

A tool to download flashstreams from movie-streaming sites like kinox.to or anime-loads.org

## Bugs:

Since all webpages change often and the program relies on the html-structure of them many pages and streams are not working.
Currently (21.04.2014) the page [ddl.me](http://ddl.me) and the streams [streamcloud](http://streamcloud.eu),
[nowvideo](http://nowvideo.sx), [firedrive](http://firedrive.com) are working.
To check the streams you can run `python stream_tests.py`.

## Features:

- Support(ed) several streaming sites as kinox.to anime-loads.org movie-loads animeseed eliteanimes
- Support(ed) several streamhoster like: bitshare, megavideo, eatlime, videobb, myvideo, stagevu, veoh, sevenload, putlocker/sockshare,
  zeec, ccf and generic xvid, directdownload
- allows to build up a database from the streamhoster - I made a little php stream-database with that if there is interest mail me
- extensive caching with various backends
- multiple downloads / queues
- many hidden bugs and eastereggs

## Thanks:

Many download-algorithms are from foreign websites or foreign source code. I'm not sure if I marked every codesection as such. But still
want to thank them for making their software opensource or writing good blog posts. If you find uncredited code please write me - it was no
bad intent :)

## Contributing:

If you like to improve this program but don't like the ugly code - just send me a mail and I will help you.


## License:

MIT License
Copyright (c) 2009-2012 Carl Schönbach

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
