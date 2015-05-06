#! /usr/bin/env python3
#encoding=utf-8

'''
AdaptiveTreeWidget - 展开/收缩过程中自适应高度的QTreeWidget
'''
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPalette, QColor
from .ui_GirdWidget import Ui_GirdWidget


class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GirdWidget()
        self.ui.setupUi(self)

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(QPalette.Window, QColor(0xff, 0xff, 0xff))
        self.setPalette(p)

    def setContent(self, filename, size):
        if filename:
            self.ui.lb_preview.setImage(filename, size[0], size[1])
            # pic = QPixmap(filename)
            # pic = pic.scaled(
            #     size[0], size[1],
            #     Qt.KeepAspectRatio
            # )
            # self.ui.lb_preview.setPixmap(pic)
            self.ui.lb_filename.setText(os.path.basename(filename))
        else:
            self.ui.lb_preview.clear()
            self.ui.lb_filename.clear()
