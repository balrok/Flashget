from flashget.extension import Extension
from flashget.url import UrlMgr #, LargeDownload
from flashget.helper import textextract
from flashget.stream import BaseStream
from flashget.captcha import solveRecaptcha
from flashget.stream import getStreamByLink

import re
import logging
import json

log = logging.getLogger(__name__)


# TODO use captchaservice
# page: http://www.9kw.eu
# name: 72093
# pw: 8UYBBMJY061LKHW

class AnimeLoadsRedirect(Extension, BaseStream):
    """ this is no real streamprovider but an intermediate page where it redirects to the stream
        so to not rewrite the entire application this one here will first go to the redirection
        page and after that try to find another Stream-class
    """
    ename = 'AnimeLoadsRedirect'
    eregex = 'http://www.anime-loads.org/redirect/.*'
    url = "http://www.anime-loads.org/redirect/"
    ePriority = 1

    def getId(self):
        return textextract(self.flvUrl, '.org/redirect/', '')

    def download(self, **kwargs):
        if "retry" not in kwargs:
            kwargs["retry"] = 1
        if kwargs["retry"] == 4:
            log.error("maximum number of retries reached")
            return None

        url = UrlMgr(url=self.flvUrl, nocache=True)

        # before looking at the captcha we have to look at their advertisement
        # the error msg for a wrong captcha and not looking at their advertisement is
        # the same - so if you seem to be unlucky maybe they changed something with that
        match = re.search(r'<iframe.*src="([^"]+)"', url.data)
        if not match:
            log.error("could not find the iframe with advertisement")
            return None

        log.debug("loading advertisement %s", repr(match.group(1)))
        adUrl = UrlMgr(match.group(1), nocache=True)
        adUrl.data
        # in theory when i give the above url a header={"referer":self.flvUrl} following would be executed too
        # but to get the actual link it is enough to just load the start page

        # redirect = textextract(adUrl.data, '<meta http-equiv="refresh" content="0; url=', '">')
        # adUrl2 = UrlMgr(redirect, header={"referer":self.flvUrl}, nocache=True)
        # redirect2 = textextract(adUrl2.data, '<form target="_parent" method="post" action="', '"')
        # adUrl3 = UrlMgr(redirect2, post={"":""}, nocache=True)

        recaptchaId = textextract(url.data, 'src="http://www.google.com/recaptcha/api/challenge?k=', '"')

        challenge, solution = solveRecaptcha(recaptchaId, referer=self.flvUrl)
        if challenge.find("&") > 0:
            challenge = textextract(challenge, "", "&")
        post = {"action": "web", "recaptcha_challenge_field": challenge, "recaptcha_response_field": solution}

        # the x-Requested-With is quite important else it doesn't work
        url = UrlMgr(url=self.flvUrl, post=post, header={"X-Requested-With": "XMLHttpRequest", }, nocache=True)

        try:
            data = json.loads(url.data[3:])
        except:
            log.error("No json returned, showing first 200 chars:")
            log.error(url.data.replace("\n", "").replace("\r", "")[:200])
            data = {"ok": False}
        if not data["ok"]:
            kwargs["retry"] += 1
            return self.download(**kwargs)
        else:
            link = data["response"].decode("base64")
            log.info("found new link %s", repr(link))
            stream = getStreamByLink(link)
            return stream.download(**kwargs)
        return None

    # this type of stream is really bad - try to avoid it at all costs:
    def getScore(self):
        if self.flv_type == "streamcloud":
            return -1
        elif self.flv_type == "hellsmedia":
            return -2
        log.warning("Unknown flv_type for this redirect - I have no score for it")
        return 0


    @staticmethod
    def getTestData():
        return {'link': 'http://www.anime-loads.org/redirect/196625/c32cacf4f0',
            'linkId': '196625',
            'className': 'AnimeLoadsRedirect',
            'size': 146445261,
        }
