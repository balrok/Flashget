import os

class config(object):
    cache_dir = '/mnt/sda6/prog/flashget/cache'
    flash_dir = '/mnt/sda6/prog/flashget/flash'
    dl_instances = 2



    def __getattr__(self, name):
        if name == 'dl_instances':
            value = 1
        self.name = value
        return value



    if not os.access(cache_dir, os.W_OK):
        print "your cache-dir isn't writeable please edit config.py"
    if not os.access(flash_dir, os.W_OK):
        print "your flash-dir isn't writeable please edit config.py"
