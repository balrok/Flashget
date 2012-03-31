Flashget
A tool to download flashstreams from movie-streaming sites like kinox.to or anime-loads.org

Bugs:
Since all webpages change often and the program relies on the html-structure of them I think all pages are broken.
The ncurses interface might not work - at least I haven't used it since long ago.

Features:
- Support(ed) several streaming sites as kinox.to anime-loads.org movie-loads animeseed eliteanimes
- Support(ed) several streamhoster like: bitshare, megavideo, eatlime, videobb, myvideo, stagevu, veoh, sevenload, putlocker/sockshare,
  zeec, ccf and generic xvid, directdownload
- allows to build up a database from the streamhoster - I made a little php stream-database with that if there is interest mail me
- extensive caching with various backends
- multiple downloads / queues
- many hidden bugs and eastereggs

About:
This project is currently dead. I developed it long time just for me because I think it's not good if such a tool exists because the hoster
won't get money from their advertisements. But since it is broken anyway I guess noone will use it for bad. Also I feel like giving
something back after I copied so much of foreign algorithms.

In this project I developed an own http-library based on sockets. This was needed since I disliked the python defaultimplementation and the
requests library wasn't available yet. The http-lib is quite robust since it came over many errors while crawling. But I won't say it has no
errors. Also it doesn't has the cleanest code. If I had the time I would try to replace it with requests.

Another thing I developed was a simple plugin interface which is responsible for adding new stream-hoster and streaming sites. You just need
to tell it the directory and it will autodetect every class which implements the plugin interface. After much googling I didn't find
anything as simple and easy than what I did.

Random cool things are:
    The textextract function which realy helps with extracting information from known html layout.
    The various cache implementations under one interface + converting-function.
    Perhaps the datastructure to put the streamsite-content into db.

Thanks:
Many download-algorithms are from foreign websites or foreign source code. I'm not sure if I marked every codesection as such. But still
want to thank them for making their software opensource or writing good blog posts.


Contributing:
If you like to improve this program just send me a mail and I will help you.


License:
MIT License
Copyright (c) 2009-2012 Carl Schönbach

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
