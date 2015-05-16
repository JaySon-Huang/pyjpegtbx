#!/usr/bin/env python3
#encoding=utf-8

'''
对比两张图片的Tab
'''
import os

from PyQt5.QtWidgets import QDialog, QFileDialog

from .ui_ShowResultDialog import Ui_Dialog


class ShowResultDialog(QDialog, Ui_Dialog):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        # setup widgets
        self.setupUi(self)

        self.lb_image.setImageFileSrc(filepath)
        self.image_path = filepath

        self.btn_save.clicked.connect(
            self.on_save_clicked
        )

    def on_save_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self)
        if filepath:
            os.rename(self.image_path, filepath)
            print('mv `%s` -> `%s`' % (self.image_path, filepath))
