from tools.page import Page
from tools.extension import Extension
from tools.url import UrlMgr
from tools.helper import textextract, textextractall

class GenxAnime(Page):
    def __init__(self):
        self.name = 'genx-anime'
        self.url = 'http://www.genx-anime.org'
        Page.__init__(self)

    def getAllPages(self, link):
        return []

    def extract(self, link):
        if not self.beforeExtract():
            return None
        url = UrlMgr(url=link, cookies=self.cookies)


        name = textextract(url.data, '<h1 class="h1_video">', '</h1>')
        media = Page.getMedia(self, name, link)
        if not media:
            return None
        media.origUrl = textextract(url.data, 'on <a style="color:#BBB;" href="', '"')

        part = media.createSub()
        alternative = part.createSub()
        alternativePart = alternative.createSub()
        alternativePart.url = link
        tagData = textextract(url.data, 'Tags:</span>', '</table>')
        tags = set()
        for i in textextractall(tagData, '"/search/', '/videos/"'):
            tags.add(i)
        media.addTags(list(tags))
        return media




baseRegex = '^(http://)?(www\.)?genx-anime\.org'
class SingleGenxAnimeExtension(GenxAnime, Extension):
    eregex = baseRegex+'/index.php?do=show_download'
    ename = 'genxanime_s'
    def get(self, link):
        return GenxAnime.extract(self, link)
