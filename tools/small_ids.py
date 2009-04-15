class SmallId(object):
    def __init__(self, log, start):
        self.ids = [0]
        self.log = log
        self.start = start

    def free(self, id):
        self.ids[id - self.start] = 0
        self.log.info('freeing id '+str(id))

    def new(self):
        i = 0
        for i in xrange(0,len(self.ids)):
            if self.ids[i] == 0:
                break
        else:
            i += 1
            self.ids.append(1)
        self.ids[i] = 1
        self.log.info('using id ' + str(i + self.start))
        return i + self.start


