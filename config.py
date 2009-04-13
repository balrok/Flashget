# -*- coding: utf-8 -*-
import os

cache_dir = '/mnt/sda6/prog/flashget/cache'
flash_dir = '/mnt/sda6/prog/flashget/flash'
dl_instances = 2




if not os.access(cache_dir, os.W_OK):
    print "your cache-dir isn't writeable please edit config.py"
if not os.access(flash_dir, os.W_OK):
    print "your flash-dir isn't writeable please edit config.py"
