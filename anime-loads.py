#!/usr/bin/python
# -*- coding: utf-8 -*-

import config
import tools.display as display
from curses import wrapper



def main(stdscr):
    try:
        config.d_screen = display.Screen(stdscr)
        config.d_log = display.LogWindow(config.d_screen, 0, 0, 20)
        config.d_progress = display.simple(config.d_screen, 20, 0, 4)


    except:
        pass
    else:
        config.d_log.add_line('test')
        import prog
        prog.main()

wrapper(main)
