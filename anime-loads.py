#!/usr/bin/python
# -*- coding: utf-8 -*-

import tools.display as display
from curses import wrapper
from threading import Thread


def main(stdscr):
    win_mgr = display.WindowManagement(stdscr)
    win_mgr.start()
    import prog
    Thread(prog.main()).start()


wrapper(main)
