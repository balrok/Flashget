"""
Youwatch urlresolver XBMC Addon
Copyright (C) 2015 tknorris

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
"""
import re
from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
from lib import jsunpack

MAX_TRIES = 5
    
class YouWatchResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "youwatch"
    domains = ["youwatch.org"]

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()
        self.pattern = '//((?:www.)?youwatch.org)/(?:embed-)?([A-Za-z0-9]+)(?:-\d+x\d+\.html)?'
            
    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {
                   'Referer': web_url
        }
        tries = 0
        while tries < MAX_TRIES:
            html = self.net.http_GET(web_url, headers=headers).content
            r = re.search('<iframe[^>]*src="([^"]+/embed[^"]+)', html)
            if r:
                headers['Referer'] = web_url
                web_url = r.group(1)
            else:
                break
            tries += 1
        
        for match in re.finditer('(eval\(function.*?)</script>', html, re.DOTALL):
            js_data = jsunpack.unpack(match.group(1))
            match2 = re.search('file\s*:\s*"([^"]+)', js_data)
            if match2:
                return match2.group(1) + '|User-Agent=%s' % (common.IE_USER_AGENT)
    
        raise UrlResolver.ResolverError('Unable to resolve youwatch link. Filelink not found.')

    def get_url(self, host, media_id):
        return 'http://youwatch.org/embed-%s-640x360.html' % media_id

    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            return r.groups()
        else:
            return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': 
            return False
        return re.search(self.pattern, url) or 'youwatch' in host
