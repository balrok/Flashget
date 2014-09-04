#!/usr/bin/python

import Tkinter as tki
from Tkinter import Label, Button
import Pmw
import time
import logging
import threading
import Queue

import flashget
from flashget.main import main as flashget_main
from flashget.config import updateConfig, loadConfig

fields = []

def sleep_handler(self, timeout):
    end = time.time() + timeout
    app.sleepName = self.ename
    while True:
        percent = (1 - (end - time.time()) / timeout) * 100
        app.sleepProgress.put("%.2f" % percent)
        if percent >= 100:
            return True
        time.sleep(0.1)

def progress_handler(self, uid, event, data):
    log_string = ' [%s%%] %s/%s at %s ETA %s  %s %d' % (data["percent"], data["downloaded"], data["size"], data["speed"], data["eta"], data["basename"], uid)
    app.downloads.put((uid, event, data, log_string))

class App(object):
    def __init__(self):
        self.fields = []
        self.queue = Queue.Queue()

        self.sleepProgress = Queue.Queue()
        self.sleepName = ""

        self.downloads = Queue.Queue()
        self.printedDownloads = 0
        self.downloadLines = []

        self.root = tki.Tk()
        self.root.wm_title(flashget.__name__ + " - " + flashget.__version__)
        self.root.columnconfigure(0, weight=1)


        notebook = Pmw.NoteBook(self.root)
        notebook.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        page = notebook.add('Start & Overview')
        notebook.tab('Start & Overview').focus_set()

        # Create the "Toolbar" contents of the page.
        group = Pmw.Group(page, tag_text = 'Start')
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        # Create the "Startup" contents of the page.
        tkWebsite = Pmw.EntryField(group.interior(), labelpos = 'w',
            label_text = 'Website:')
        tkWebsite.insert(0,"http://de.ddl.me/ein-seltsames-paar-deutsch-stream-download_0_5707.html")
        tkWebsite.grid(row=0, column=0, columnspan=2, sticky="ns")
        tkWebsite.columnconfigure(0, weight=1)
        self.fields.append((tkWebsite, "website"))
        Button(group.interior(), text='Run', command=self.startFlashget).grid(row=1, column=0, sticky="nsew", pady=4)

        group = Pmw.Group(page, tag_text = 'Downloads')
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)
        self.drawProgressSleep(group.interior())
        self.drawProgressDownloads(group.interior())

        group = Pmw.Group(page, tag_text = 'Log')
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)
        self.drawLogWindow(group.interior())
        #home.pack(fill = 'x', padx = 20, pady = 10)

        page = notebook.add('Settings')


        notebook.setnaturalsize()

        #self.drawInputs(page)
        #self.drawProgressSleep()
        #self.drawProgressDownloads()
        #self.drawLogWindow()

    def drawProgressSleep(self, parent):
        l = Label(parent, text="Sleeping")
        l.grid(row=0)
        self.tkSleepName = Label(parent, text="name")
        self.tkSleepName.grid(row=1, column=1)
        self.tkSleepPercent = Label(parent, text="per")
        self.tkSleepPercent.grid(row=1, column=2)
        self.process_sleep()

    def drawProgressDownloads(self, parent):
        # I tried to implement a scrollbar here , but it doesn't work so well
        # so TODO: improve the scrollbar here
        vscrollbar = tki.Scrollbar(parent, orient=tki.VERTICAL)
        vscrollbar.grid(row=1, column=4, rowspan=100)

        canvas = tki.Canvas(parent, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
        canvas.grid(row=1, columnspan=3, sticky="nsew")

        vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.dl_frm = dl_frm = interior = tki.Frame(canvas)
        dl_frm.grid(row=0)
        interior_id = canvas.create_window(0, 0, window=interior,anchor=tki.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

        self.process_downloads()


    def drawLogWindow(self, parent):
        # TODO find a way to autofit in the width and height
        # create a Text widget
        self.txt = Pmw.ScrolledText(parent,
                text_wrap = 'word',
                #vscrollmode = "none",
                usehullsize = 1,
                hull_width = 900,
                hull_height = 190,
                #text_width = 60,
                #text_height = 10,
                #historycommand = self.statechange,
        )
        self.txt.grid(row=0)

    def startFlashget(self):
        values = {}
        for field,name in self.fields:
            values[name] = field.get()
        self.flashget_thread = FlashgetThread(self, values)

    def run(self):
        self.process_queue()
        self.root.mainloop()

    def process_queue(self):
        try:
            while True:
                record = self.queue.get(False)
                self.txt.appendtext(record+u"\n")
        except Queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def process_sleep(self):
        try:
            while True:
                record = self.sleepProgress.get(False)
                self.tkSleepName.config(text=self.sleepName)
                self.tkSleepPercent.config(text=record)
        except Queue.Empty:
            pass
        self.root.after(100, self.process_sleep)

    def _init_downloadLine(self):
        self.printedDownloads += 1
        line = self.printedDownloads
        c = 0
        label = Label(self.dl_frm, text="%d"%line)
        label.grid(row=line, column=c)
        self.downloadLines.append(label)

    def process_downloads(self):
        try:
            while True:
                uid, event, data, t = self.downloads.get(False)
                if uid >= self.printedDownloads:
                    for i in range(0, 1 + uid - self.printedDownloads):
                        self._init_downloadLine()
                label = self.downloadLines[uid]
                label.config(text=" "*200) # clear line
                if event == "new" or event == "update":
                    label.config(text=t)
        except Queue.Empty:
            pass
        self.root.after(100, self.process_downloads)

class FlashgetThread(threading.Thread):
    def __init__(self, app, values):
        self.app = app
        self.values = values
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        config = loadConfig()
        config = updateConfig({"links": [self.values["website"]],
            "progress_handler": progress_handler,
            "sleep_handler": sleep_handler,
            "captcha_selfsolve": True})
        flashget_main(config)



class TkHandler(logging.Handler):
    def __init__(self, app):
        logging.Handler.__init__(self)
        self.app = app
    def emit(self, record):
        record = self.format(record)
        if record:
            self.app.queue.put(record)



app = App()


logger = logging.getLogger()
handler = TkHandler(app)
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)5s] %(name)17s:%(lineno)03d: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

app.run()
