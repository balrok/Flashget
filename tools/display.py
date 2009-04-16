# -*- coding: utf-8 -*-

import curses
import config
import threading

class WindowManagement(threading.Thread):
    def __init__(self, stdscr):
        import Queue
        self.quit = Queue.Queue()
        self.stdscr = stdscr
        self.screen = Screen(stdscr)
        # self.stdscr.nodelay(1) # nonblocking getch - this isn't that good, cause i only need to react if realy input came in
        self.log = LogWindow(self.screen, 0, 0, 20)
        self.progress = simple(self.screen, 20, 0, config.dl_instances+2)
        self.threads = [] # this array will be extended from external calls and is used to join all threads
        threading.Thread.__init__(self)

    def key_process(self, char):
        # self.progress.add_line(char, 1)
        # self.log.add_line(char)
        if char == 'q':
            self.quit.put(1)
            return

    def run(self):
        ''' Loop to catch users keys '''
        import tools.getch as getch
        import time

        getch = getch._Getch()
        curses.nocbreak()
        curses.noecho()
        time.sleep(1)
        while True:
            c = getch()
            self.key_process(c)
            time.sleep(0.1) # i don't realy understand why this doesn't work without this sleep


class Screen(object):
    def __init__(self, stdscr):
        self.__curses = curses
        self.stdscr = stdscr
        # curses.noecho()
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
        self.win.refresh()

        self.txt_mgr = TextMgr(self.win, 1, self.height - 1, 1, self.width -1)

    def add_line(self, txt, line):
        self.txt_mgr.add_line(txt, line)


class TextsArray(object):
    def __init__(self):
        self.texts = []
        self.len = -1 # this is just a cache for the length of self.texts and is only used for performance (-1 so that first append makes this to 0)

    def append(self, val):
        self.texts.append(val)
        self.len += 1

    def __len__(self):
        return self.len

    def __setitem__(self, key, val):
        if key > self.len:
            self.texts.extend((key - self.len) * ['', 0])
            self.len += key - self.len
        self.texts[key] = val

    def __getitem__(self, key):
        return self.texts[key]


class TextMgr(object):
    ''' The TextMgr will manage the texts inside a curses window, it can be used to scroll through it or just update a specific line. '''
    def __init__(self, win, top, bottom, left, right):
        self.win    = win
        self.height = bottom - top
        self.width  = right  - left
        self.top    = top
        self.bottom = bottom
        self.left   = left
        self.right  = right

        self.display_top = 0
        self.cursor = 1  # if curser is 1 + len(self.texts) it will scroll with the texts
        self.texts  = TextsArray() # The tuple (txt, len(txt)) will be the content of this array. The indices of this array are equivalent to the linenumbers

    def redraw(self):
        start = display_top
        end = start + self.height
        if end > len(self.texts):
            end = len(self.texts) - self.bottom
        for i in xrange(start, end):
            line = i - start + self.top
            if self.width > self.texts[i][1]:
                self.win.addstr(i, self.left + self.texts[i][1], (self.width - self.texts[i][1]) * ' ')
            self.win.addstr(line, self.left, self.texts[i][0])
        self.win.refresh()

    def scroll_line(self, scroll):
        ''' Will be called when user manually moves cursor through text or when text is appended and cursor is one line after last line.
            The argument "scroll" indicate the change compared to last scroll-time. '''
        start = self.display_top + scroll - 1
        end = start + self.height
        if end > len(self.texts):
            # config.win_mgr.progress.add_line("muh"+str(end)+':'+str(len(self.texts)),2)
            end = len(self.texts) # -self.bottom ?
        end += 1
        for i in xrange(start, end):
            line = i - start + self.top
            if self.texts[i][1] < self.texts[i-scroll][1]:
                self.win.addstr(line, self.left + self.texts[i][1], (self.texts[i-scroll][1] - self.texts[i][1]) * ' ')
            self.win.addstr(line, self.left, self.texts[i][0])
        self.win.refresh()
        if end - start + scroll > self.height:
            self.display_top += scroll

    def update_line(self, pos):
        if(pos < self.display_top or pos > self.display_top + self.height):
            return # lineupdate isn't visible
        line = pos - self.display_top + self.top
        if self.width > self.texts[pos][1]:
            self.win.addstr(line, self.left + self.texts[pos][1], (self.width - self.texts[pos][1]) * ' ')
        self.win.addstr(line, self.left, self.texts[pos][0])
        self.win.refresh()

    def add_line(self, txt, line):
        '''Adds a text at the specified line-position and will update the window in case the user will see new stuff.'''
        if line == -1:
            chunks = len(txt) / self.width + 1 # i need a ceil here
            while len(txt) > self.width:
                self.texts.append((txt[:self.width], self.width))
                txt = txt[self.width:]
            if txt != '':
                self.texts.append((txt, len(txt)))

            if self.cursor - 1 == len(self.texts) - chunks:
                # cursor was one line behind texts_len that means user autoscrolls with the text
                self.cursor += chunks
                self.scroll_line(chunks) # display_top will be updated here
        else:
            self.texts[line] = (txt[:self.width], len(txt[:self.width]))
            self.update_line(line)


class LogWindow(object):
    def __init__(self, gui, x, y, height=25):
        self.gui = gui
        self.width = self.gui.maxx
        self.height = height
        self.win = curses.newwin(self.height, self.width, x, y)
        self.win.box()
        self.win.refresh()

        self.txt_mgr = TextMgr(self.win, 1, self.height - 1, 1, self.width - 1)

    def add_line(self, txt):
        self.txt_mgr.add_line(txt, -1)

def main(stdscr):
    screen = Screen(stdscr)
    w_log = simple(screen, 0, 0, 10)
    for i in xrange(0, 10):
        w_log.add_line('hello'+str(100-i),1)
    w_log.add_line('mal was ganz langes',2)
    for i in xrange(0, 109):
        w_log.add_line('hello'+str(100-i),3)
    screen.stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)
