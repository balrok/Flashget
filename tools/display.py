# -*- coding: utf-8 -*-

import curses
import config
import threading

class ColorLoader(object):
    paircount = 9 # paircount gets incremented first, so the first key will be 10
    def __init__(self):
        COLORS = "BLUE GREEN CYAN RED MAGENTA YELLOW WHITE BLACK" # not used, but a good reference
        self.esc = '^[['
        self.esc_len = len(self.esc)
        self.esc_end = self.esc + '00'
        # i make those esc-ids from 10 to 99 so we always have a static length, then it's easier to remove them
        self.esc_key_len = 2 # len(10) - len(99) is always 2

    def __getattr__(self, key):
        if key.startswith('esc'):   # format was esc_COLOR_COLOR # returns for example ^[[13
            pair = getattr(self, key[4:])
            setattr(self, key, self.esc + str(pair))
        else:                       # key should look like this: COLOR_COLOR where the first one will be foreground and 2nd one background
            colors = key.split('_')
            ColorLoader.paircount += 1
            fg = getattr(curses, 'COLOR_%s' % colors[0])
            bg = getattr(curses, 'COLOR_%s' % colors[1])
            curses.init_pair(ColorLoader.paircount, fg, bg)
            setattr(self, key, ColorLoader.paircount)
        return getattr(self, key)

class WindowManagement(object):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = Screen(stdscr)
        # menu_width = 20
        menu_width = 0
        self.main = LogWindow(0, menu_width, 20, self.screen.maxx - menu_width, 'main')
        # self.menu = LogWindow(0, 0, self.screen.maxy, menu_width, 'menu')
        self.progress = simple(20, menu_width, config.dl_instances + 2, self.screen.maxx - menu_width, 'progress')
        self.progress.txt_mgr.cursor = -1
        self.log = LogWindow(27, menu_width, 10, self.screen.maxx - menu_width, 'log')

        curses.curs_set(0)
        config.colors = ColorLoader()

        self.last_key = 0 # last pressed key (cause some keys depend on it (for example gg)
        self.active_win = self.log # window where we currently scroll

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
        #self.menu.redraw()
        curses.doupdate()


class Screen(object):
    def __init__(self, stdscr):
        self.__curses = curses
        self.stdscr = stdscr
        # curses.noecho()
        self.stdscr.keypad(1)
        # curses.start_color()
        curses.cbreak(); curses.raw() # unbuffered input (means no enter-key must be pressed to get a key-event)
        curses.noecho()     # don't echo pressed keys
        curses.flushinp()   # flushinput so that previous entered input won't be processed
        self.maxy, self.maxx = self.stdscr.getmaxyx()

    def __del__(self):
        self.__curses.nocbreak()
        self.stdscr.keypad(0)
        self.__curses.echo()
        self.__curses.endwin()


class simple(object):
    def __init__(self, x, y, height, width, title, write_lock = threading.RLock()):
        self.width = width
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
        self.len = 0 # this is just a cache for the length of self.texts and is only used for performance (it behaves the same as len() )

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

        self.line_cache = self.height * [0]
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
                if self.display_top < 0:
                    self.display_top = 0
            else:
                self.display_top = (self.cursor + self.curs_pad + 1) - self.height

        if self.display_top != old_display_top:
            self.redraw()
        else:
            line = old_cursor - start + self.top
            if(old_cursor < len(self.texts) and line < end + 1):
                #config.win_mgr.progress.add_line(str(self.cursor),0)
                self._draw_line(line, old_cursor)
            line = self.cursor - self.display_top + self.top
            if(self.cursor < len(self.texts) and line < end + 1):
                #config.win_mgr.progress.add_line(str(line)+':'+str(self.cursor),2)
                self._draw_line(line, self.cursor)
            self.win.refresh() # needed to display cursorposition
        self.write_lock.release()

    def _draw_line(self, line, index):
        ''' used to add lines to the windows, will also split the text  prev_line will be used to clear the text under this line'''
        le = self.texts[index][1] # length
        swi = self.width
        sle = self.left

        i = 0
        end = 0
        co_sl = []
        if index == self.cursor:
            co_sl.append((end, le, config.colors.YELLOW_BLUE))
        else:
            for x in self.texts[index][2]: # structure is (start, end, key)
                if x[0] > end: # print normal until start
                    co_sl.append((end, x[0], 0))
                co_sl.append((x[0], x[1], x[2]))
                end = x[1]
            if end < le:
                co_sl.append((end, le, 0))

        cosl_i = 0
        start = 0
        end = 0
        if line + (le / swi) - self.top < self.height:
            last_len = self.line_cache[line + (le / swi) - self.top] # we only need to look at the last one, all other will be splitted with len swi
        while start < le:
            if i + line > self.height:
                return i
            end   += swi
            if end > le:
                end = le
            self.line_cache[line + i - self.top] = end - start
            s = start
            e = co_sl[cosl_i][1]
            if e > end:
                e = end
            while True:
                self.win.addstr(line + i, self.left + (s - start), self.texts[index][0][s:e].encode('utf-8'), curses.color_pair(co_sl[cosl_i][2]))
                if e == end:
                    break
                cosl_i += 1
                s = co_sl[cosl_i][0]
                e = co_sl[cosl_i][1]
                if e > end:
                    e = end
            i     += 1
            start += swi

        i -= 1
        if self.line_cache[line + i - self.top] < swi:
            if last_len > self.line_cache[line + i - self.top]:
                self.win.addstr(line + i, self.line_cache[line + i - self.top] + self.left, (last_len - self.line_cache[line + i - self.top]) * ' ')
        return i + 1

    def redraw(self):
        if len(self.texts) == 0:
            return
        self.write_lock.acquire()
        start = self.display_top
        end = start + self.height
        if end > len(self.texts):
            end = len(self.texts)
        line = self.top
        i = 0
        while line < self.height + 1:
            line += self._draw_line(line, start + i)
            i += 1
            if i == end:
                break
        self.win.refresh()
        self.write_lock.release()

    def update_line(self, pos):
        # maybe we can directly call draw_line instead of this
        if(pos < self.display_top or pos > self.display_top + self.height):
            return # lineupdate isn't visible
        line = pos - self.display_top + self.top
        self._draw_line(line, pos)
        self.win.refresh()
        return

    def add_line(self, txt, line):
        '''Adds a text at the specified line-position and will update the window in case the user will see new stuff.
           Also this function process the txt-line: it will create the colorlist and slice strings for the scrolling window.'''
        def get_esc(txt):
            ''' returns array with (start, end, key) values, where start and end means the position where colors.key is applied
                also it removes then all key_sequences from txt
                return is txt, array'''
            end     = 0 # current position, from where we need to find things (will be changed inside the loop)
            ret_arr = []
            found   = 0
            # make variablenames shorter
            esc_len = config.colors.esc_len
            esc_key_len = config.colors.esc_key_len
            esc = config.colors.esc
            found_keys = []
            while True:
                start = txt.find(esc, end)
                if start == -1:
                    break
                key = txt[(start + esc_len):(start + esc_len + esc_key_len)]
                found_keys.append(key)
                end = txt.find(esc, start + esc_len + esc_key_len) # we only search for esc, cause we forbidd nested colors
                if end < 0:         # if no end found, set the end to the end of text
                    end = len(txt)  # start won't automaticly find anything at next loop and stop then
                found += 2
                ret_arr.append((start - (esc_len * (found - 2)), # we must remove here the esc-sequences, cause they will be removed later
                               1 + end - (esc_len * found),
                               int(key)))
                end += esc_len + esc_key_len # we will search the next start from this position

            if found_keys != []: # now we remove all esc-sequences:
                for i in set(found_keys): # walks through all unique keys
                    txt = txt.replace(esc + str(i), '')
                txt = txt.replace(config.colors.esc_end, '')
            return txt, ret_arr

        txt, color_list = get_esc(txt)
        if line == -1:
            self.texts.append((txt, len(txt), color_list))
            if self.cursor == len(self.texts) - 1: # cursor was one line behind texts_len that means user autoscrolls with the text
                self.cursor = len(self.texts)
                self.display_top = len(self.texts) - self.height
                if self.display_top < 0:
                    self.display_top = 0
                self.redraw()
            elif len(self.texts) < self.height: # at the beginning we also need to redraw this, cause the log will be empty
                self.redraw()
        else:
            self.texts[line] = (txt, len(txt), color_list)
            self.update_line(line)


class LogWindow(object):
    def __init__(self, x, y, height, width, title, write_lock = threading.RLock()):
        self.width = width
        self.height = height
        self.win = curses.newwin(self.height, self.width, x, y)
        self.title = title
        self.txt_mgr = TextMgr(self.win, 1, self.height - 1, 1, self.width - 1, write_lock)
        self.redraw()

    def redraw(self):
        self.win.redrawwin()
        self.win.box()
        self.win.addstr(0, 1, '< ' + self.title + ' >')
        self.win.noutrefresh()

    def add_line(self, txt):
        self.txt_mgr.add_line(txt, -1)

    def cursor_move(self, move):
        self.txt_mgr.cursor_move(move)


def main(stdscr):
    import time
    win_mgr = WindowManagement(stdscr)
    win_mgr.log.add_line('test')
    w_log = win_mgr.log
    for i in xrange(0, 10):
        time.sleep(1)
        w_log.add_line(10*i*'hello'+str(100-i))
        w_log.redraw()
    w_log.add_line(3*'mal was ganz langes')
    for i in xrange(0, 109):
        time.sleep(1)

        w_log.add_line('hello'+str(100-i))

    time.sleep(1)


if __name__ == '__main__':
    class config(object):
        def __init__(self):
            self.bla=0
            self.dl_instances = 4
    config = config()
    curses.wrapper(main)
