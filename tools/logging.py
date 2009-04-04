class LogHandler(object):
    def __init__(self, type):
        self.type = type
    def info(self, str):
        print str
    def error(self, str):
        print str
