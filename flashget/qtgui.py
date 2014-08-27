# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qtgui.ui'
#
# Created: Wed Aug 27 19:34:42 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(640, 480)
        Dialog.setMinimumSize(QtCore.QSize(640, 480))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(9, 9, 21, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.url = QtGui.QLineEdit(Dialog)
        self.url.setGeometry(QtCore.QRect(40, 10, 110, 20))
        self.url.setObjectName(_fromUtf8("url"))
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(510, 10, 77, 26))
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(0, 60, 118, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.parallel_downloads = QtGui.QLineEdit(Dialog)
        self.parallel_downloads.setGeometry(QtCore.QRect(150, 60, 16, 16))
        self.parallel_downloads.setObjectName(_fromUtf8("parallel_downloads"))
        self.progress_1_label = QtGui.QLabel(Dialog)
        self.progress_1_label.setGeometry(QtCore.QRect(10, 140, 73, 16))
        self.progress_1_label.setObjectName(_fromUtf8("progress_1_label"))
        self.progressBar_1 = QtGui.QProgressBar(Dialog)
        self.progressBar_1.setGeometry(QtCore.QRect(89, 133, 95, 22))
        self.progressBar_1.setProperty("value", 0)
        self.progressBar_1.setObjectName(_fromUtf8("progressBar_1"))
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setGeometry(QtCore.QRect(9, 189, 22, 16))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.logBrowser = QtGui.QTextBrowser(Dialog)
        self.logBrowser.setGeometry(QtCore.QRect(9, 209, 631, 241))
        self.logBrowser.setObjectName(_fromUtf8("logBrowser"))
        self.current_downloads = QtGui.QTableView(Dialog)
        self.current_downloads.setGeometry(QtCore.QRect(250, 110, 351, 81))
        self.current_downloads.setObjectName(_fromUtf8("current_downloads"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label.setText(_translate("Dialog", "Url:", None))
        self.okButton.setText(_translate("Dialog", "OK", None))
        self.label_2.setText(_translate("Dialog", "Parallel Downloads", None))
        self.progress_1_label.setText(_translate("Dialog", "Download 1", None))
        self.label_5.setText(_translate("Dialog", "Log", None))

