'''
thevideo urlresolver plugin
Copyright (C) 2014 Eldorado

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
import re, urllib
from urlresolver import common
from lib import jsunpack

MAX_TRIES=3

class TheVideoResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "thevideo"
    domains = ["thevideo.me"]

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        html = self.net.http_GET(web_url).content
        r = re.findall(r"'label'\s*:\s*'([^']+)p'\s*,\s*'file'\s*:\s*'([^']+)", html)
        if not r:
            raise UrlResolver.ResolverError('Unable to locate link')
        else:
            max_quality = 0
            for quality, stream_url in r:
                if int(quality) >= max_quality:
                    best_stream_url = stream_url
                    max_quality = int(quality)
            return best_stream_url

    def get_url(self, host, media_id):
        return 'http://%s/embed-%s.html' % (host, media_id)

    def get_host_and_id(self, url):
        r = re.search('//(.+?)/(?:embed-)?([0-9a-zA-Z/]+)', url)
        if r:
            return r.groups()
        else:
            return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return (re.match('http://(www\.|embed-)?thevideo.me/' +
                         '[0-9A-Za-z]+', url) or
                         'thevideo' in host)
