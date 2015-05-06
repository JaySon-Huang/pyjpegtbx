# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_GirdWidget.ui'
#
# Created: Thu Apr 23 12:32:32 2015
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GirdWidget(object):
    def setupUi(self, GirdWidget):
        GirdWidget.setObjectName("GirdWidget")
        GirdWidget.resize(300, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(GirdWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lb_preview = ImageLabel(GirdWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_preview.sizePolicy().hasHeightForWidth())
        self.lb_preview.setSizePolicy(sizePolicy)
        self.lb_preview.setMinimumSize(QtCore.QSize(250, 250))
        self.lb_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_preview.setObjectName("lb_preview")
        self.verticalLayout.addWidget(self.lb_preview)
        self.lb_filename = QtWidgets.QLabel(GirdWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_filename.sizePolicy().hasHeightForWidth())
        self.lb_filename.setSizePolicy(sizePolicy)
        self.lb_filename.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_filename.setWordWrap(True)
        self.lb_filename.setObjectName("lb_filename")
        self.verticalLayout.addWidget(self.lb_filename)

        self.retranslateUi(GirdWidget)
        QtCore.QMetaObject.connectSlotsByName(GirdWidget)

    def retranslateUi(self, GirdWidget):
        _translate = QtCore.QCoreApplication.translate
        GirdWidget.setWindowTitle(_translate("GirdWidget", "Form"))
        self.lb_preview.setText(_translate("GirdWidget", "PictureLabel"))
        self.lb_filename.setText(_translate("GirdWidget", "Filename"))

from .ImageLabel import ImageLabel
