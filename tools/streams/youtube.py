from tools.stream import *
import tools.defines as defs


class YouTubeStream(VideoInfo):
    homepage_type = defs.Homepage.YOUTUBE
    def __init__(self, url, parent):
        self.init__(url, parent.log) # call baseclass init

    def get_title(self):
        # <title>YouTube - Georg Kreisler - Taubenvergiften</title>
        return textextract(self.url_handle.data, 'title>YouTube - ', '</title').decode('utf-8')

    def get_name(self):
        return 'youtube'

    def get_subdir(self):
        return self.name

    def get_stream(self):
        # var swfArgs = {"q": "georg%20kreisler", "fexp": "900026,900018", "enablecsi": "1", "vq": null, "sourceid": "ys", "video_id": "OOqsfPrsFRU", "l": 158, "sk": "9mEvI6FCZGm3kxjitpsWLfuA3pd2ny8fC", "fmt_map": "18/512000/9/0/115,34/0/9/0/115,5/0/7/0/0", "usef": 0, "t": "vjVQa1PpcFPD0-luSj0ipQrNGlifdaiKTqla87p4l6s=", "hl": "de", "plid": "AARq38-sU-qXE4Bx", "keywords": "Georg%2CKreisler%2CTaubenvergiften%2CSatire%2Cim%2CPark%2CMusic%2CPiano%2CKlavier%2CSchwarzer%2CHumor%2C%C3%96sterreich%2CLied%2CKabarett%2CKult", "cr": "DE"};
        # l seems to be the playlength
        swfargs = textextract(self.url_handle.data, 'var swfArgs', '};')
        # from youtube-dl: (mobj.group(1) is "t"
        # video_real_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&el=detailpage&ps=' % (video_id, mobj.group(1))
        video_id = textextract(swfargs, '"video_id": "', '"')
        t = textextract(swfargs, '"t": "', '"')
        url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&el=detailpage&ps=' % (video_id, t)
        return {'url':url}

