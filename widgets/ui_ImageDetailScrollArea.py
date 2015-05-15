# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/ui_ImageDetailScrollArea.ui'
#
# Created: Fri May 15 13:06:14 2015
#      by: PyQt5 UI code generator 5.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 700)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 374, 674))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lb_title = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lb_title.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_title.setObjectName("lb_title")
        self.verticalLayout_2.addWidget(self.lb_title)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lb_filename = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lb_filename.setObjectName("lb_filename")
        self.horizontalLayout.addWidget(self.lb_filename)
        self.lb_size = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lb_size.setObjectName("lb_size")
        self.horizontalLayout.addWidget(self.lb_size)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.lb_image = ImageLabel(self.scrollAreaWidgetContents)
        self.lb_image.setMinimumSize(QtCore.QSize(250, 250))
        self.lb_image.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_image.setObjectName("lb_image")
        self.verticalLayout_2.addWidget(self.lb_image)
        self.lb_components = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lb_components.setObjectName("lb_components")
        self.verticalLayout_2.addWidget(self.lb_components)
        self.treeWidget_components = AdaptiveTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_components.setUniformRowHeights(True)
        self.treeWidget_components.setObjectName("treeWidget_components")
        self.treeWidget_components.headerItem().setText(0, "1")
        self.verticalLayout_2.addWidget(self.treeWidget_components)
        self.lb_quantTbls = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lb_quantTbls.setObjectName("lb_quantTbls")
        self.verticalLayout_2.addWidget(self.lb_quantTbls)
        self.treeWidget_quantTbls = QtWidgets.QTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_quantTbls.setObjectName("treeWidget_quantTbls")
        self.treeWidget_quantTbls.headerItem().setText(0, "1")
        self.verticalLayout_2.addWidget(self.treeWidget_quantTbls)
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.treeWidget_huffTbls = QtWidgets.QTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_huffTbls.setObjectName("treeWidget_huffTbls")
        self.treeWidget_huffTbls.headerItem().setText(0, "1")
        self.verticalLayout_2.addWidget(self.treeWidget_huffTbls)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.lb_title.setText(_translate("Form", "Title"))
        self.lb_filename.setText(_translate("Form", "filename:"))
        self.lb_size.setText(_translate("Form", "size:"))
        self.lb_image.setText(_translate("Form", "ImageLabel"))
        self.lb_components.setText(_translate("Form", "lb_components"))
        self.lb_quantTbls.setText(_translate("Form", "lb_quantTbls"))
        self.label.setText(_translate("Form", "lb_huffTbls"))

from widgets.ImageLabel import ImageLabel
from widgets.AdaptiveTreeWidget import AdaptiveTreeWidget
