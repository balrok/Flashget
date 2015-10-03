# -*- coding: utf-8 -*-

"""
Stream2k urlresolver XBMC Addon based on VKResolver
Copyright (C) 2015 Seberoth
Version 0.0.1 
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
import xbmcgui
from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
import simplejson as json

class Stream2kResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "stream2k.tv"
    domains = ["stream2k.tv"]

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()
        self.pattern = '//((?:www.)?stream2k.tv)/player/framer\.php\?i=(.+)'

    def get_media_url(self, host, media_id):
        base_url = self.get_url(host, media_id)
        soup = self.net.http_GET(base_url).content
        html = soup.decode('cp1251')
        sources = re.compile("sources: \[(.*?)\]", flags=re.S).findall(html)

        if sources:
            cSources = sources[0].strip()
            cSources = cSources[:-1]
            cSources = '{"sources": [' + cSources + ']}'

            jsonvars = json.loads(cSources)

            purged_jsonvars = {}
            for item in jsonvars['sources']:
                quality = re.sub("[^0-9]", "", item['label'])
                purged_jsonvars[quality] = item['file']

            lines = []
            best = '0'

            for item in purged_jsonvars:
                lines.append(str(item))
                if int(str(item)) > int(best): best = str(item)

            lines = sorted(lines, key=int)

            if len(lines) == 1:
                return purged_jsonvars[lines[0]].encode('utf-8')
            else:
                if self.get_setting('auto_pick') == 'true':
                    return purged_jsonvars[(str(best))].encode('utf-8') + '|User-Agent=%s' % (common.IE_USER_AGENT)
                else:
                    result = xbmcgui.Dialog().select('Choose the link', lines)
            if result != -1:
                return purged_jsonvars[lines[result]].encode('utf-8') + '|User-Agent=%s' % (common.IE_USER_AGENT)
            else:
                raise UrlResolver.ResolverError('No link selected')
        else:
            raise UrlResolver.ResolverError('No sources found')

    def get_url(self, host, media_id):
        return 'http://%s/player/framer.php?i=%s' % (host, media_id)

    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            return r.groups()
        else:
            return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false':
            return False
        return re.search(self.pattern, url) or 'stream2k' in host

    def get_settings_xml(self):
        xml = PluginSettings.get_settings_xml(self)
        xml += '<setting id="%s_auto_pick" type="bool" label="Automatically pick best quality" default="false" visible="true"/>' % (self.__class__.__name__)
        return xml
