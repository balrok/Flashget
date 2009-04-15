#!/usr/bin/python
# -*- coding: utf-8 -*-

import config
import tools.display as display
from curses import wrapper
import threading



def main(stdscr):
    try:
        config.d_screen = display.Screen(stdscr)
        config.d_log = display.LogWindow(config.d_screen, 0, 0, 20)
        config.d_progress = display.simple(config.d_screen, 20, 0, config.dl_instances+2)


    except:
        pass
    else:
        import prog
        threading.Thread(prog.main()).start()
        # threading.Thread(display.key_handler()).start()

wrapper(main)
