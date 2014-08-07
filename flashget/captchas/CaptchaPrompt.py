import subprocess

class CaptchaPrompt(object):
    def newCaptchaTask(self, task):
        if not task.isTextual():
            return False
        return self.processCaptcha(task)
    def processCaptcha(self, task):
        imageviewer = 'xv' # 'xdg-open'
        subprocess.Popen([imageviewer, task.tmpfile.name])
        # print "gwenview %s" % task.tmpfile.name
        while True:
            solvedCaptcha = raw_input("Write the captcha code or '?': ")
            if solvedCaptcha == "?":
                print "typing nothing will use another service (if configured)"
            else:
                break
        task.setResult(solvedCaptcha)
        return solvedCaptcha

