#!/usr/bin/python
# -*- coding: utf-8 -*-

import tools.display as display
from curses import wrapper
import thread
import config
import Queue

import locale

locale.setlocale(locale.LC_ALL,"")


def key_process(char):
    win_mgr = config.win_mgr
    #config.win_mgr.progress.add_line(str(char),0)
    if char == 113:                     # q         exit program
        import sys
        sys.exit(0)
    elif char == 12:                    # ctrl+l    redraw screen
        win_mgr.redraw()
    elif char == 338:                   # pg down   move 5 lines down
        win_mgr.active_win.cursor_move(5)
    elif char == 339:                   # pg up     move 5 lines up
        win_mgr.active_win.cursor_move(-5)
    elif char == 106:                   # j         move down
        win_mgr.active_win.cursor_move(1)
    elif char == 107:                   # k         move up
        win_mgr.active_win.cursor_move(-1)
    elif char == 103:                   # g         jump to start of log
        if win_mgr.last_key == 103:
            win_mgr.active_win.cursor_move(-10000000)
    elif char == 71:                    # GG        jump to end of log
        if win_mgr.last_key == 71:
            win_mgr.active_win.cursor_move(10000000)
    elif char == 265:                   # F1
        win_mgr.active_win = win_mgr.progress
    elif char == 266:                   # F2
        win_mgr.active_win = win_mgr.main
    elif char == 267:                   # F3
        win_mgr.active_win = win_mgr.log
    win_mgr.last_key = char
    win_mgr.last_key = char


def main(stdscr):
    win_mgr = display.WindowManagement(stdscr)
    win_mgr.update_title('Flash-Downloader')
    config.win_mgr = win_mgr
    win_mgr.redraw() # display new created screen
    import prog
    thread.start_new(prog.main, ())

    while True:
        c = win_mgr.stdscr.getch()
        key_process(c)

wrapper(main)
