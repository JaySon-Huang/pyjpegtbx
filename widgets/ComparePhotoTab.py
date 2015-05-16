#!/usr/bin/env python3
#encoding=utf-8

'''
对比两张图片的Tab
'''

from PyQt5.QtWidgets import QWidget, QFileDialog

from .ui_ComparePhotoTab import Ui_Tab
from .ShowResultDialog import ShowResultDialog
from utils.pictureUtils import compare_images
from utils.fileUtils import getTmpFilepath, getLibFilepath


class ComparePhotoTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        # setup widgets
        self.setupUi(self)

        self.imagesPath = {
            'ori': None,
            'cmp': None,
            'res': None,
        }

        # connect signal-slot
        self.btn_loadOriImage.clicked.connect(
            self.on_loadOriImage_clicked
        )
        self.btn_loadCmpImage.clicked.connect(
            self.on_loadCmpImage_clicked
        )
        self.btn_compareImage.clicked.connect(
            self.on_compareImage_clicked
        )

    def on_loadOriImage_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            parent=self, caption='Open', directory='', filter='*.jpg'
        )
        if filepath:
            self.imagesPath['ori'] = filepath
            self.lb_oriImage.setImageFileSrc(filepath)

    def on_loadCmpImage_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            parent=self, caption='Open', directory='', filter='*.jpg'
        )
        if filepath:
            self.imagesPath['cmp'] = filepath
            self.lb_cmpImage.setImageFileSrc(filepath)

    def on_compareImage_clicked(self):
        if not self.imagesPath['ori'] and not self.imagesPath['cmp']:
            return
        img = compare_images(
            self.imagesPath['ori'], self.imagesPath['cmp']
        )
        filepath = getTmpFilepath(self.imagesPath['ori'])
        print('result of compare image save to:', filepath)
        img.save(filepath, quality=90)
        self.dialog = ShowResultDialog(filepath)
        self.dialog.exec_()
