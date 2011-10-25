#!/usr/bin/python
# -*- coding: utf-8 -*-

import tools.display as display
from curses import wrapper
import thread
import config
import Queue
import sys

import locale
import tools.commandline as commandline

locale.setlocale(locale.LC_ALL,"")


def key_process(char):
    win_mgr = config.win_mgr
    #config.win_mgr.progress.add_line(str(char),0)
    if char == 12:                      # ctrl+l    redraw screen
        win_mgr.redraw()
    elif char == 17:                    # ctrl+q    exit program
        import sys
        sys.exit(0)
    elif char == 338:                   # pg down   move 5 lines down
        win_mgr.active_win.cursor_move(5)
    elif char == 339:                   # pg up     move 5 lines up
        win_mgr.active_win.cursor_move(-5)

    elif char >= 265 and char <= 275:    # F1, F2, .. , F10
        win = char - 265
        if win < len(win_mgr.win_list):
            win_mgr.active_win = win_mgr.win_list[win]

    if win_mgr.active_win.input_mode:
        if char >= 32 and char <= 126: # 32-126 are printable ascii-characters
            win_mgr.active_win.add_char(chr(char), 0)
            return
        if char == 10: # newline = return
            win_mgr.active_win.send_input(0)

    elif char == 113:                   # q         exit program
        import sys
        sys.exit(0)
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
    win_mgr.last_key = char


def main(stdscr):
    win_mgr = display.WindowManagement(stdscr)
    win_mgr.update_title('Flash-Downloader')
    config.win_mgr = win_mgr
    from tools.log import WinHandler
    import logging
    for i in config.logTypes:
        winHandler = WinHandler(win_mgr.log)
        winHandler.setLevel(logging.DEBUG)
        config.logger[i].addHandler(winHandler)

    win_mgr.redraw() # display new created screen
    import prog
    thread.start_new(prog.main, ())

    while True:
        c = win_mgr.stdscr.getch()
        key_process(c)

commandline.parse()
open('.flashget_log', 'a').write(' '.join(sys.argv) + '\n')
wrapper(main)
