#!/usr/bin/env python3
#encoding=utf-8

'''
对比两张图片的Tab
'''

from PyQt5.QtWidgets import QWidget

from .ui_ComparePhotoTab import Ui_Tab


class ComparePhotoTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
