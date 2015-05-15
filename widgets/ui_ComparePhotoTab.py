# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/ui_ComparePhotoTab.ui'
#
# Created: Sat May 16 02:24:29 2015
#      by: PyQt5 UI code generator 5.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Tab(object):
    def setupUi(self, Tab):
        Tab.setObjectName("Tab")
        Tab.resize(636, 384)
        self.vLayout = QtWidgets.QVBoxLayout(Tab)
        self.vLayout.setObjectName("vLayout")
        self.hLayout = QtWidgets.QHBoxLayout()
        self.hLayout.setObjectName("hLayout")
        self.btn_loadOriImage = QtWidgets.QPushButton(Tab)
        self.btn_loadOriImage.setObjectName("btn_loadOriImage")
        self.hLayout.addWidget(self.btn_loadOriImage)
        self.btn_loadCmpImage = QtWidgets.QPushButton(Tab)
        self.btn_loadCmpImage.setObjectName("btn_loadCmpImage")
        self.hLayout.addWidget(self.btn_loadCmpImage)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hLayout.addItem(spacerItem)
        self.btn_compareImage = QtWidgets.QPushButton(Tab)
        self.btn_compareImage.setObjectName("btn_compareImage")
        self.hLayout.addWidget(self.btn_compareImage)
        self.btn_saveCmpResult = QtWidgets.QPushButton(Tab)
        self.btn_saveCmpResult.setObjectName("btn_saveCmpResult")
        self.hLayout.addWidget(self.btn_saveCmpResult)
        self.vLayout.addLayout(self.hLayout)
        self.hLayout_2 = QtWidgets.QHBoxLayout()
        self.hLayout_2.setObjectName("hLayout_2")
        self.lb_oriImage = ImageLabel(Tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_oriImage.sizePolicy().hasHeightForWidth())
        self.lb_oriImage.setSizePolicy(sizePolicy)
        self.lb_oriImage.setMinimumSize(QtCore.QSize(300, 300))
        self.lb_oriImage.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_oriImage.setObjectName("lb_oriImage")
        self.hLayout_2.addWidget(self.lb_oriImage)
        self.lb_cmpImage = ImageLabel(Tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_cmpImage.sizePolicy().hasHeightForWidth())
        self.lb_cmpImage.setSizePolicy(sizePolicy)
        self.lb_cmpImage.setMinimumSize(QtCore.QSize(300, 300))
        self.lb_cmpImage.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_cmpImage.setObjectName("lb_cmpImage")
        self.hLayout_2.addWidget(self.lb_cmpImage)
        self.vLayout.addLayout(self.hLayout_2)

        self.retranslateUi(Tab)
        QtCore.QMetaObject.connectSlotsByName(Tab)

    def retranslateUi(self, Tab):
        _translate = QtCore.QCoreApplication.translate
        Tab.setWindowTitle(_translate("Tab", "Form"))
        self.btn_loadOriImage.setText(_translate("Tab", "Load Original \n"
"Image"))
        self.btn_loadCmpImage.setText(_translate("Tab", "Load Compared \n"
"Image"))
        self.btn_compareImage.setText(_translate("Tab", "Compare"))
        self.btn_saveCmpResult.setText(_translate("Tab", "Save Compare"))
        self.lb_oriImage.setText(_translate("Tab", "Original Image Label"))
        self.lb_cmpImage.setText(_translate("Tab", "Compared Image Label"))

from widgets.ImageLabel import ImageLabel
