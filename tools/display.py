# -*- coding: utf-8 -*-

import curses
import config
import threading


class WindowManagement(threading.Thread):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = Screen(stdscr)
        self.log = LogWindow(self.screen, 0, 0, 20)
        self.progress = simple(self.screen, 20, 0, config.dl_instances+2)
        config.win_mgr = self
        threading.Thread.__init__(self)

    def run(self):
        while True:
            c = self.stdscr.getch()


class Screen(object):
    def __init__(self, stdscr):
        self.__curses = curses
        self.stdscr = stdscr
        # curses.noecho()
        # curses.cbreak()
        self.stdscr.keypad(1)
        # curses.start_color()
        # self.stdscr.refresh()
        self.maxy, self.maxx = self.stdscr.getmaxyx()

    def __del__(self):
        self.__curses.nocbreak()
        self.stdscr.keypad(0)
        self.__curses.echo()
        self.__curses.endwin()


class simple(object):
    def __init__(self, gui, x, y, height=25):
        self.gui = gui
        self.width = self.gui.maxx
        self.height = height
        self.win = curses.newwin(self.height, self.width, x, y)
        self.win.box()
        self.last_len = []
        for i in xrange(0, height):
            self.last_len.append(0)
        self.win.refresh()

    def show(self, line, txt):
        lgth = len(txt)
        if lgth < self.last_len[line]:
            self.win.addstr(line, 1 + lgth, (self.last_len[line] - lgth) * ' ')
        self.last_len[line] = lgth
        self.win.addstr(line, 1, txt)
        self.win.refresh()


class LogWindow(object):
    def __init__(self, gui, x, y, height=25):
        self.gui = gui
        self.width = self.gui.maxx
        self.height = height
        self.log_cache = []
        self.win = curses.newwin(self.height, self.width, x, y)
        self.win.box()
        self.win.refresh()
        self.print_pos = 0
        self.view_pos = 0
        self.last_max = 0 # used to store the last printed position

        # self.debugwin = curses.newwin(self.height, self.width, self.height+x, y)
        # self.debugwin.box()

    def print_win(self, max):
        min = max - self.height + 2
        if min < 0:
            min = 0
        c = 0
        if max > self.height-2:
            diff = max - self.last_max
        else:
            diff = 0

        for i in xrange(min, max):
            c += 1
            if (self.width - self.log_cache[i][1]) > 0:
                self.win.addstr(c, self.log_cache[i][1], (self.width - self.log_cache[i][1]) * ' ')
            '''
            if (i + diff < len(self.log_cache) and i + diff > -1):
                # self.debugwin.addstr(c, 1, str(i)+':'+str(diff))
                # self.debugwin.addstr(c, 10, str(self.log_cache[i+diff][1])+':'+str(self.log_cache[i][1]))
                if self.log_cache[i+diff][1] < self.log_cache[i][1]:
                    # self.debugwin.addstr(c, 30, str(self.log_cache[i][1]) +':'+ str(self.log_cache[i+diff][1] - self.log_cache[i][1] +1))
                    self.win.addstr(c, self.log_cache[i+diff][1]+1, (self.log_cache[i][1] - self.log_cache[i+diff][1] + 2) * ' ')
            '''

            self.win.addstr(c, 1, self.log_cache[i][0])
            if i is max:
                break
        self.win.refresh()

        # self.debugwin.refresh()
        self.last_max = max

    def add_line(self, txt):
        length = 0
        while len(txt) > self.width-5:
            length += 1
            self.log_cache.append((txt[:self.width-5], self.width))
            txt = txt[self.width-5:]

        if str is not '':
            self.log_cache.append((txt, len(txt)))
            length +=1
        # self.debugwin.addstr(0,0,str(length))
        #self.debugwin.refresh()

        self.print_pos += length
        self.print_win(self.print_pos)


def main(stdscr):
    screen = Screen(stdscr)
    w_log = LogWindow(screen, 0, 0, 10)
    for i in xrange(0, 10):
        w_log.add_line('hello'+str(100-i))
    w_log.add_line('mal was ganz langes')
    for i in xrange(0, 109):
        w_log.add_line('hello'+str(100-i))
    print 1 + 'a'
    screen.stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)
