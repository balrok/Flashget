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


class WindowManagement(threading.Thread):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen = Screen(stdscr)
        self.main = LogWindow(self.screen, 0, 0, 20, 'main')
        self.progress = simple(self.screen, 20, 0, config.dl_instances + 2, 'progress')
        self.log = LogWindow(self.screen, 27, 0, 10, 'log')

        config.colors = ColorLoader()
        curses.curs_set(0)

        self.last_key = 0 # last pressed key (cause some keys depend on it (for example gg)
        self.active_win = self.log # window where we currently scroll
        threading.Thread.__init__(self)

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
        curses.cbreak(); curses.raw() # unbuffered input (means no enter-key must be pressed to get a key-event)
        curses.noecho()     # don't echo pressed keys
        curses.flushinp()   # flushinput so that previous entered input won't be processed
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
        ''' internally used, to add decoration to some lines '''
        if index == self.cursor:
            self.win.addstr(line, self.left, self.texts[index][0], curses.color_pair(config.colors.YELLOW_BLUE))
        else:
            end = 0
            if len(self.texts[index][2]) > 0: # we have some defined colors inside
                for i in self.texts[index][2]: # structure is (start, end, key)
                    if i[0] > end: # print normal until start
                        self.win.addstr(line, self.left + end, self.texts[index][0][end:i[0]])
                    self.win.addstr(line, self.left + i[0], self.texts[index][0][i[0]:i[1]], curses.color_pair(i[2]))
                    end   = i[1]

            if end < self.texts[index][1]:
                self.win.addstr(line, self.left + end, self.texts[index][0][end:])

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
            self._draw_line(line, i)
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
            # if text should scroll, we will cut it, if the width is to small
            chunks = len(txt) / self.width + 1 # i need a ceil here, this is the amount of parts a text will be splitted (1-N)
            color_start = 0                     # the index in color_list from where we start
            color_len   = len(color_list)       # just as a cache
            txt_start   = 0                     # index of txt, where we start (only needed for text which needs to be splitted, but normal
                                                # text also uses this index
            txt_end     = 0                     # can be calculated through txt_start
            for x in xrange(0, chunks - 1):         # don't cycle to last chunk, cause this chunk mostly is shorter then previous ones
                txt_start = x * self.width
                txt_end   = txt_start + self.width
                if color_start < color_len:
                    c_index         = color_start
                    old_color_start = color_start
                    while c_index < color_len: # get te index from colorlist, where start is in range of the text which gets printed
                        if color_list[c_index][0] > txt_end: # if colorstart is after the end of text, we will stop
                            break
                        c_index += 1
                    color_start = c_index
                    if color_list[c_index - 1][1] > txt_end:    # if the end of our current color will be in the next line
                        color_start -= 1                        # we decrement the color_start so it will be used then later
                    color_slice = []
                    for j in xrange(old_color_start, c_index):  # cause the text is now splitted, the (start, end) positions may be to high
                        color_slice.append((color_list[j][0] - txt_start, color_list[j][1] - txt_start, color_list[j][2]))
                    self.texts.append((txt[txt_start:txt_end], self.width, color_slice))
                else:
                    self.texts.append((txt[txt_start:txt_end], self.width, []))

            txt_start = txt_end
            if txt_start < len(txt): # this section will also often be called after the text was already splitted
                self.texts.append((txt[txt_start:], len(txt[txt_start:]), color_list[color_start:]))

            if self.cursor == len(self.texts) - chunks: # cursor was one line behind texts_len that means user autoscrolls with the text
                self.cursor += chunks
                self.scroll_line(chunks)
        else:
            # if text should go on one line, we don't cut it here
            start = 0
            self.texts[line] = (txt[:self.width], len(txt[:self.width]), color_list)
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
