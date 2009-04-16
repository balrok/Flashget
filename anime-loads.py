#!/usr/bin/python
# -*- coding: utf-8 -*-

import tools.display as display
from curses import wrapper
from threading import Thread
import config


def main(stdscr):
    win_mgr = display.WindowManagement(stdscr)
    config.win_mgr = win_mgr
    win_mgr.start()
    import prog
    thread_main = Thread(prog.main())
    win_mgr.threads.append(thread_main)
    thread_main.start()

    win_mgr.quit.get(True)
    import sys
    sys.exit(0)

wrapper(main)
