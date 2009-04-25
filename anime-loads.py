#!/usr/bin/python
# -*- coding: utf-8 -*-

import tools.display as display
from curses import wrapper
import thread
import config
import Queue

import locale

locale.setlocale(locale.LC_ALL,"")



def main(stdscr):
    config.quit_queue = Queue.Queue()
    win_mgr = display.WindowManagement(stdscr)
    win_mgr.update_title('anime-loads downloader')
    config.win_mgr = win_mgr
    win_mgr.start()
    win_mgr.redraw() # display new created screen
    import prog
    thread.start_new(prog.main, ())
    while True:
        try:
            config.quit_queue.get(True, 1)
        except:
            pass
        else:
            import sys
            sys.exit(0)

wrapper(main)
