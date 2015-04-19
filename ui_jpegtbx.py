# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'jpegtbx.ui'
#
# Created: Mon Apr 20 03:06:04 2015
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1036, 712)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.le_curFilepath = QtWidgets.QLineEdit(self.centralwidget)
        self.le_curFilepath.setObjectName("le_curFilepath")
        self.horizontalLayout_2.addWidget(self.le_curFilepath)
        self.btn_changeToFilepath = QtWidgets.QPushButton(self.centralwidget)
        self.btn_changeToFilepath.setObjectName("btn_changeToFilepath")
        self.horizontalLayout_2.addWidget(self.btn_changeToFilepath)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mainView = QtWidgets.QTableView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainView.sizePolicy().hasHeightForWidth())
        self.mainView.setSizePolicy(sizePolicy)
        self.mainView.setMinimumSize(QtCore.QSize(600, 600))
        self.mainView.setObjectName("mainView")
        self.horizontalLayout.addWidget(self.mainView)
        self.verticalLayout.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1036, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuAbout = QtWidgets.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        self.le_curFilepath.returnPressed.connect(self.btn_changeToFilepath.click)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SecretPhotos"))
        self.btn_changeToFilepath.setText(_translate("MainWindow", "Go"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuAbout.setTitle(_translate("MainWindow", "About"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionExit.setStatusTip(_translate("MainWindow", "Quit SecretPhotos"))
        self.actionExit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionOpen.setStatusTip(_translate("MainWindow", "Open file..."))
        self.actionOpen.setShortcut(_translate("MainWindow", "Ctrl+F"))

