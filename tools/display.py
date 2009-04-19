# -*- coding: utf-8 -*-

import curses
import config
import threading

class ColorLoader(object):
    def __init__(self):
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.black_white = curses.color_pair(1)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        self.yellow_blue = curses.color_pair(2)

class WindowManagement(threading.Thread):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = Screen(stdscr)
        self.main = LogWindow(self.screen, 0, 0, 20, 'main')
        self.progress = simple(self.screen, 20, 0, config.dl_instances + 2, 'progress')
        self.log = LogWindow(self.screen, 27, 0, 10, 'log')

        config.colors = ColorLoader()
        curses.curs_set(0)

        threading.Thread.__init__(self)
        self.last_key = 0
        self.active_win = self.log

    def update_title(self, txt):
        # Changes Terminal Title - copied from mucous-0.8.0 ( http://daelstorm.thegraveyard.org/mucous.php )
        import os
        if os.path.expandvars("$SHELL") in  ("/bin/bash", "/bin/sh"):
            if str(curses.termname() ) != "linux":
                os.system("echo -ne \"\033]0;%s\007\" " % txt)

    def redraw(self):
        self.log.redraw()
        self.progress.redraw()
        self.main.redraw()
        curses.doupdate()

    def key_process(self, char):
        #self.progress.add_line(str(char), 1)

        if char == 113:                     # q         exit program
            config.quit_queue.put(1)
        elif char == 12:                    # ctrl+l    redraw screen
            self.redraw()
        elif char == 338:                   # pg down   move 5 lines down
            self.active_win.cursor_move(5)
        elif char == 339:                   # pg up     move 5 lines up
            self.active_win.cursor_move(-5)
        elif char == 106:                   # j         move down
            self.active_win.cursor_move(1)
        elif char == 107:                   # k         move up
            self.active_win.cursor_move(-1)
        elif char == 103:                   # g         jump to start of log
            if self.last_key == 103:
                self.active_win.cursor_move(-10000000)
        elif char == 71:                    # GG        jump to end of log
            if self.last_key == 71:
                self.active_win.cursor_move(10000000)
        self.last_key = char

    def run(self):
        ''' Loop to catch users keys '''
        curses.cbreak(); curses.raw() # unbuffered input
        curses.noecho()     # don't echo pressed keys
        curses.flushinp()  # flushinput so that previous entered input won't be processed
        while True:
            c = self.stdscr.getch()
            self.key_process(c)


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
    def __init__(self, gui, x, y, height, title, write_lock = threading.RLock()):
        self.gui = gui
        self.width = self.gui.maxx
        self.height = height
        self.win = curses.newwin(self.height, self.width, x, y)
        self.title = title
        self.txt_mgr = TextMgr(self.win, 1, self.height - 1, 1, self.width -1, write_lock)
        self.redraw()

    def redraw(self):
        self.win.redrawwin()
        self.win.box()
        self.win.addstr(0, 4, '< ' + self.title + ' >')
        self.win.noutrefresh()

    def add_line(self, txt, line):
        self.txt_mgr.add_line(txt, line)


class TextsArray(object):
    def __init__(self):
        self.texts = []
        self.len = 0 # this is just a cache for the length of self.texts and is only used for performance (-1 so that first append makes this to 0)

    def append(self, val):
        self.texts.append(val)
        self.len += 1

    def __len__(self):
        if self.len < 0:
            return 0
        return self.len

    def __setitem__(self, key, val):
        if key >= self.len:
            self.texts.extend((key - self.len + 1) * [('', 0)])
            self.len += key - self.len + 1
        self.texts[key] = val

    def __getitem__(self, key):
        return self.texts[key]
    def __repr__(self):
        return repr(self.texts)


class TextMgr(object):
    ''' The TextMgr will manage the texts inside a curses window, it can be used to scroll through it or just update a specific line. '''
    def __init__(self, win, top, bottom, left, right, lock):
        self.win    = win
        self.height = bottom - top
        self.width  = right - left
        self.top    = top
        self.bottom = bottom
        self.left   = left
        self.right  = right

        self.write_lock = lock

        self.display_top = 0
        self.cursor = 0  # if curser is len(self.texts) it will scroll with the texts
        self.curs_pad = 1
        self.texts  = TextsArray() # The tuple (txt, len(txt)) will be the content of this array. The indices of this array are equivalent to the linenumbers

    def cursor_move(self, move):
        if len(self.texts) == 0: # We can't move our cursor, if there's no text.
            return
        self.write_lock.acquire()
        old_cursor = self.cursor # we need to temporarily store it here, to remove the highlight from old curser
        self.cursor += move
        if self.cursor > len(self.texts):
            self.cursor = len(self.texts)
        if self.cursor < 0:
            self.cursor = 0

        if self.cursor == old_cursor: # nothing changed
            self.write_lock.release()
            return

        start = self.display_top
        end = start + self.height
        if end > len(self.texts):
            end = len(self.texts)

        # config.win_mgr.progress.add_line(str(self.cursor)+':'+str(end)+':'+str(len(self.texts))+':'+str(start)+':'+str(self.height),3)
        old_display_top = self.display_top # We need to temporarily store this, to look if display_top changed, and if we need to redraw the screen
        if (self.cursor - self.curs_pad) < self.display_top:
            if self.cursor - self.curs_pad < 0:
                self.display_top = 0
            else:
                self.display_top = self.cursor - self.curs_pad

        elif (self.cursor + self.curs_pad) >= end:
            if (self.cursor + self.curs_pad) >= len(self.texts):
                self.display_top = len(self.texts) - self.height
            else:
                self.display_top = (self.cursor + self.curs_pad + 1) - self.height

        if self.display_top != old_display_top:
            # self.scroll_line(old_display_top - self.display_top)
            self.redraw(True)
        else:
            line = old_cursor - start + self.top
            if(old_cursor < len(self.texts) and line < end):
                #config.win_mgr.progress.add_line(str(self.cursor),0)
                self._draw_line(line, old_cursor)
            line = self.cursor - self.display_top + self.top
            if(self.cursor < len(self.texts) and line < end):
                #config.win_mgr.progress.add_line(str(line)+':'+str(self.cursor),2)
                self._draw_line(line, self.cursor)
            self.win.refresh() # needed to display cursorposition
        self.write_lock.release()

    def _draw_line(self, line, index):
        ''' internally used, to add decoration to some lines and to avoid code duplication '''
        if index == self.cursor:
            self.win.addstr(line, self.left, self.texts[index][0], config.colors.yellow_blue)
        else:
            self.win.addstr(line, self.left, self.texts[index][0])

    def redraw(self, partial = False):
        if len(self.texts) == 0:
            return
        self.write_lock.acquire()
        start = self.display_top
        end = start + self.height
        if end > len(self.texts):
            end = len(self.texts)
        # config.win_mgr.progress.add_line("mah"+str(end)+':'+str(start)+':'+str(len(self.texts)),2)
        for i in xrange(start, end):
            line = i - start + self.top
            if(partial and self.width > self.texts[i][1]):
                self.win.addstr(line, self.left + self.texts[i][1], (self.width - self.texts[i][1]) * ' ')
            self._draw_line(line, i)
        self.win.refresh()
        self.write_lock.release()

    def scroll_line(self, scroll):
        ''' Will be called when user manually moves cursor through text or when text is appended and cursor is one line after last line.
            The argument "scroll" indicate the change compared to last scroll-time. '''
        self.write_lock.acquire()
        start = self.display_top + scroll
        end = start + self.height
        if end > len(self.texts):
            # config.win_mgr.progress.add_line("muh"+str(end)+':'+str(len(self.texts)),2)
            end = len(self.texts) # -self.bottom ?
        for i in xrange(start, end):
            line = i - start + self.top
            if self.texts[i][1] < self.texts[i-scroll][1]:
                self.win.addstr(line, self.left + self.texts[i][1], (self.texts[i-scroll][1] - self.texts[i][1]) * ' ')
            self.win.addstr(line, self.left, self.texts[i][0])
        self.win.refresh()
        if end - start + scroll > self.height:
            self.display_top += scroll
        self.write_lock.release()

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

            if self.cursor == len(self.texts) - chunks:
                # cursor was one line behind texts_len that means user autoscrolls with the text
                self.cursor += chunks
                self.scroll_line(chunks) # display_top will be updated here
        else:
            self.texts[line] = (txt[:self.width], len(txt[:self.width]))
            self.update_line(line)


class LogWindow(object):
    def __init__(self, gui, x, y, height, title, write_lock = threading.RLock()):
        self.gui = gui
        self.width = self.gui.maxx
        self.height = height
        self.win = curses.newwin(self.height, self.width, x, y)
        self.title = title
        self.txt_mgr = TextMgr(self.win, 1, self.height - 1, 1, self.width - 1, write_lock)
        self.redraw()

    def redraw(self):
        self.win.redrawwin()
        self.win.box()
        self.win.addstr(0, 4, '< ' + self.title + ' >')
        self.win.noutrefresh()

    def add_line(self, txt):
        self.txt_mgr.add_line(txt, -1)

    def cursor_move(self, move):
        self.txt_mgr.cursor_move(move)


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
