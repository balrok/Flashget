from tools.page import Page
from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import textextract, textextractall

class GenxAnime(Page):
    def __init__(self):
        self.name = 'genx-anime'
        self.url = 'http://www.genx-anime.org'
        self.cookies = []
        Page.__init__(self)

    def getAllPages(self, link):
        return []

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = UrlMgr(url=link, cookies=self.cookies)

        name = textextract(url.data, '<h2>&raquo; ', ' &laquo;</h2>')
        media = Page.getMedia(self, name, link)
        if not media:
            return None
        media.origUrl = textextract(url.data, 'on <a style="color:#BBB;" href="', '"')
        '''
<td><b>Folge 2: Lektion 2

-> 'id="folge_2"', '</div>' -> 'go&link=', '"'
-> 'id="download_2"', '</div>' -> 'go&link=', '"'

                <td colspan="2">

                    <div id="folge_2" style="display: none;">
                       <a target="_blank" href="index.php?do=go&link=aHR0cDovL3d3dy5kaXZ4c3RhZ2UubmV0L3ZpZGVvL3JvNDlnZGVobmlpMG0="><img
                       name="play" src="images/hoster/StandartP.png"></a><a target="_blank"
                       href="index.php?do=go&link=aHR0cDovL3N0cmVhbWNsb3VkLmV1LzFqNXRtNDExOHlzcy9nZW5YLUFuaW1lLm9yZ19HLlQuT19fTGVrdGlvbl8wMi54dmlkLmdlci1zdWIuQlMtQUUuYXZpLmh0bWw="><img
                       name="play" src="images/hoster/StreamCloud.eu.png"></a>                    </div>
                    <div id="download_2" style="display: none;">
                    <a target="_blank" href="index.php?do=go&link=aHR0cDovL3d3dy5zaGFyZS1vbmxpbmUuYml6L2RsL0VDU0pSODVNSkRY"><img
                    src="images/hoster/Share-Online.biz.png"></a><a target="_blank"
                    href="index.php?do=go&link=aHR0cDovL3VsLnRvL2hxbm0ydjlv"><img src="images/hoster/Uploaded.to.png"></a><a target="_blank"
                    href="index.php?do=go&link=aHR0cDovL3VwbG9hZGVkLnRvL2ZpbGUvM3E1enZqNGU="><img src="images/hoster/StandartD.png"></a>
                    </div>
                </td>
                '''
        for number in textextractall(url.data, '<td><b>Folge ', ':'):
            part = media.createSub()
            part.num = number
            #part.title = textextract(url.data, '<td><b>Folge '+number+": ", " \n")
            streamArea = textextract(url.data, 'id="folge_'+number+'"', '</div>')
            for link in textextractall(streamArea, 'go&link=', '"'):
                alternative = part.createSub()
                alternativePart = alternative.createSub()
                alternativePart.url = link.decode('base64')
                self.setPinfo(alternativePart)
            dlArea = textextract(url.data, 'id="download_'+number+'"', '</div>')
            for link in textextractall(dlArea, 'go&link=', '"'):
                alternative = part.createSub()
                alternativePart = alternative.createSub()
                alternativePart.url = link.decode('base64')
                self.setPinfo(alternativePart)


        return media




baseRegex = '^(http://)?(www\.)?genx-anime\.org'
class SingleGenxAnimeExtension(GenxAnime, Extension):
    eregex = baseRegex+'/index\.php\?do=show_download.*'
    ename = 'genxanime_s'
    def get(self, link):
        return GenxAnime.extract(self, link)
