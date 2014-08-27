# -*- coding: utf-8 -*-
import flashget
from flashget.qtgui import Ui_Dialog
from flashget.main import main as flashget_main
from flashget.config import updateConfig, loadConfig
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QVariant, Qt, QAbstractTableModel, QThread
import sys


class FlashgetDialog(QtGui.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # Set up the user interface from Designer.
        self.setupUi(parent)

        self.okButton.clicked.connect(self.accept)

        self.config = loadConfig()

        self.setFields()
        self.started = False

    def setFields(self):
        self.parallel_downloads.setText(self.config["dl_instances"])
        self.url.setText("http://de.ddl.me/ein-seltsames-paar-deutsch-stream-download_0_5707.html")

        XStream.stdout().messageWritten.connect( self.logBrowser.insertPlainText)
        XStream.stderr().messageWritten.connect( self.logBrowser.insertPlainText )

        self.tableModel = DownloadsModel([["","","","",""]], self)
        self.current_downloads.setModel(self.tableModel)

    def accept(self):
        if self.started:
            return
        url = self.url.text()
        url = unicode(url).strip()
        self.config = updateConfig({"links": [url],
            "progress_handler": progress_handler,
            "sleep_handler": sleep_handler,
            "captcha_selfsolve": True})
        self.thread = FlashgetThread(self.config, self)
        self.thread.start()
        self.started = True


class FlashgetThread(QThread):
    def __init__(self, config, parent=None):
        QThread.__init__(self, parent)

        self.config = config

    def run(self):
        flashget_main(self.config)

def progress_handler(self, uid, event, data):
    emptyRow = ["", "", "", "", ""]
    arraydata = main.centralWidget().tableModel.arraydata
    if event == "new" or event == "update":
        while len(arraydata) <= uid:
            arraydata.append(emptyRow)
        arraydata[uid] = [data["basename"], data["downloaded"] + " / " + data["size"], data["percent"], data["eta"], data["speed"]]
        #self.logProgress(' [%s%%] %s/%s at %s ETA %s  %s' % (data["percent"], data["downloaded"], data["size"], data["speed"], data["eta"], data["basename"]))
    elif event == "delete":
        if len(arraydata) <= uid:
            arraydata[uid] = emptyRow
        # cleanup
        while True:
            if arraydata[len(arraydata)-1] == emptyRow:
                del arraydata[len(arraydata)-1]
        # we need at least one row
        if len(arraydata) == 0:
            arraydata = [emptyRow]
        # self.logProgress(' ') # clear our old line
    main.centralWidget().tableModel.layoutChanged.emit()

def sleep_handler(self, timeout):
    import time
    start = time.time()
    print("sleeping for %d" % timeout)
    main.centralWidget().progress_1_label.setText(self.ename)
    while True:
        diff = time.time() - start
        if diff > timeout:
            break
        # TODO this one is crashing the application - especially when I add a "print" before
        # I guess signals are required for it so it doesn't run in a separate thread
        # val = int((diff*10/(timeout*10))*100)
        # main.centralWidget().progressBar_1.setValue(val)
        time.sleep(0.1)
    main.centralWidget().progressBar_1._active = False
    return True


class DownloadsModel(QAbstractTableModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.setWindowTitle(flashget.__name__ + " - " + flashget.__version__)
        self.resize(433, 318)

        w = FlashgetDialog(self)
        self.setCentralWidget(w)




import logging

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
        # originally: XStream.stdout().write("{}\n".format(record))

logger = logging.getLogger()
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(unicode(msg))
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr





app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())
