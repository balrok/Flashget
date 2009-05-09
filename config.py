# -*- coding: utf-8 -*-
import os

cache_dir = '/mnt/sda6/prog/python/flashget/cache'
cache_dir_for_flv = '/mnt/sda6/prog/python/flashget/cache2'
flash_dir = '/mnt/sda6/prog/python/flashget/flash'
dl_instances = 1

win_mgr = None

megavideo_wait = 0



if not os.access(cache_dir, os.W_OK):
    print "your cache-dir isn't writeable please edit config.py"
if not os.access(flash_dir, os.W_OK):
    print "your flash-dir isn't writeable please edit config.py"
