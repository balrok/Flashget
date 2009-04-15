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
    Thread(prog.main()).start()


wrapper(main)
