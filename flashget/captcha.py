# helper to solve a captcha

from .captchas.Captcha9kw import Captcha9kw
from .captchas.CaptchaPrompt import CaptchaPrompt
from .url import UrlMgr
from .helper import textextract
from .config import config
import random

try:
    import urlparse
except ImportError:
    # python 3
    import urllib.urlparse as urlparse

from tempfile import NamedTemporaryFile
import logging
import time
import re

log = logging.getLogger(__name__)


class Task(object):
    def __init__(self, url=""):
        urlObj = url
        self.tmpfile = NamedTemporaryFile(delete=False)
        self.tmpfile.write(urlObj.get_rawdata())
        self.tmpfile.close()
        self.captchaFile = self.tmpfile.name
        self.data = {}
        self.handler = []
        self.result = None
        self.waittime = 0

    def isTextual(self):
        return True

    def setWaiting(self, seconds):
        self.waittime = seconds

    def wait(self, seconds):
        time.sleep(1)
        self.waittime -= seconds
        return self.waittime

    def setResult(self, data):
        self.result = data


class DummyClass(object):
    def isClientConnected(self):
        return True


def logDebug(self, string):
    log.debug(string)


def logInfo(self, string):
    log.info(string)


def logError(self, string):
    log.error(string)


def getConfig(self, key):
    if key == "passkey":
        return config.get('captcha9kw_pass')
    if key == "force":
        return True
Captcha9kw.logDebug = logDebug
Captcha9kw.logError = logError
Captcha9kw.logInfo = logInfo
Captcha9kw.getConfig = getConfig
Captcha9kw.core = DummyClass()
Captcha9kw.info = {}

# page: http://www.9kw.eu
# name: 72093
# pw: 8UYBBMJY061LKHW


def solveCaptcha(url):
    task = Task(url)
    if config.get('captcha_selfsolve'):
        # we don't need to wait for this one
        CaptchaPrompt().newCaptchaTask(task)

    if config.get('captcha9kw_solve'):
        if task.result == "-" or task.result == "":
            task.setResult("")
            Captcha9kw().newCaptchaTask(task)
            while True:
                waittime = task.wait(1)
                if task.result:
                    break
                if waittime <= 0:
                    break
    return task.result


# this class is from the pyload program and adjusted for flashget
def solveRecaptcha(rid, referer=""):
    data = UrlMgr("http://www.google.com/recaptcha/api/challenge?k=%s&cachestop=%.17f" % (rid, random.random()), referer=referer, nocache=True).data
    challenge = re.search("challenge : '(.*?)',", data).group(1)
    server = re.search("server : '(.*?)',", data).group(1)
    #time.sleep(1)
    # I've seen a response like "a19d..&th=,8be.."
    # so i use urlparse to unpack if it is required
    challenge = dict(urlparse.parse_qsl("c="+challenge))
    # jdownloader has a constant th parameter but it doesn't change anything
    # normally th is calculated via javascript and an anti-bot messure
    # challenge["th"] = ",8bCUfM53LiuAO7bFaPd8-ycjTP0ABB4IkPz4AGY5eUMG77zJylwqi8V2tXq4paZbqcxKlbawCYORutvj2D2lxCFVtfvhICua_FCe2PxH5siFjV2czSZmjlRCkW04A-F992Bdrn7zHm2pLLcBk5WzAwkfetDFuvC1BotwWReiv2SUlPnYAA5g7XU5vdlHeddeQysnHA"

    # this step is super important to get readable captchas - normally we could take the "c" from above and already retrieve a captcha but
    # this one would be barely readable
    reloadParams = challenge.copy()
    reloadParams["k"] = rid
    reloadParams["lang"] = "de"
    reloadParams["reason"] = "i"
    reloadParams["type"] = "image"

    data = UrlMgr("http://www.google.com/recaptcha/api/reload", params=reloadParams, referer=referer, nocache=True).data
    challenge["c"] = textextract(data, "Recaptcha.finish_reload('", "',")

    print challenge
    return challenge["c"], solveCaptcha(UrlMgr("%simage" % (server), params=challenge, referer=referer))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        solveCaptcha(sys.argv[1])
    else:
        data = UrlMgr("https://www.google.com/recaptcha/demo/ajax", nocache=True).data
        rc_id = textextract(data, 'Recaptcha.create("', '",')
        challenge, solution = solveRecaptcha(rc_id)
        url = UrlMgr("https://www.google.com/recaptcha/demo/ajax", post={
            'Button1': 'Submit',
            'recaptcha_challenge_field': challenge,
            'recaptcha_response_field': solution,
        })
        if url.data.find("Richtig!") > 0:
            print "everything was fine"
        elif url.data.find("Falsch") > 0:
            print "maybe you entered the captcha wrong"
        else:
            print "unknown error"
