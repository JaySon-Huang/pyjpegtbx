#! /usr/bin/env python3
#encoding=utf-8

import os
import sys
import json

from pyjpegtbx import JPEGImage
from JPEGImageCipher import JPEGImageCipher

from PyQt5.QtCore import (
    QDir, Qt, QVariant
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QItemDelegate, QLabel, QHeaderView, QGridLayout,
    QWidget, QScrollArea, QGraphicsWidget
)
from PyQt5.QtGui import (
    QPixmap, QStandardItemModel, QStandardItem
)

from ui_GirdWidget import Ui_GirdWidget
from ui_MainWindow import Ui_MainWindow


pics = ['lfs.jpg', 'tmp0.jpg', 'tmp1.jpg']


class GirdWidget(QWidget):
    def __init__(self, filename, size, parent=None):
        super().__init__(parent)

        self.ui = Ui_GirdWidget()
        self.ui.setupUi(self)

        if filename:
            pic = QPixmap(filename)
            pic = pic.scaled(
                size[0], size[1],
                Qt.KeepAspectRatio
            )
            self.ui.lb_preview.setPixmap(pic)
            self.ui.lb_filename.setText(filename)
        else:
            pass




class MainWindow(QMainWindow):

    # static strings
    strings = {
        'filename': 'filename: %s (%s)',
        'size': 'size: %d x %d',
        'component': 'Components (%d in total)',
        'quantization': 'Quantization tables (%d in total)',
        'huffman': 'Huffman tables (%d for DC, %d for AC)',
    }
    # static paths
    paths = {
        'root': '',
        'library': '',
        'tmp': '',
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 初始化paths, 并确保一些文件夹的存在性
        self.setPaths()

        self.mainViewSize = {'col': 3, 'row': 3}  # col, row

        girdLayout_viewLibrary = QGridLayout(self.ui.scrollAreaWidgetContents)
        for i, pic in enumerate(pics):
            col = i % self.mainViewSize['col']
            row = i / self.mainViewSize['col']
            girdLayout_viewLibrary.addWidget(
                GirdWidget(pic, (250, 250)),
                row, col
            )
        while i < 11:
            i += 1
            col = i % self.mainViewSize['col']
            row = i / self.mainViewSize['col']
            girdLayout_viewLibrary.addWidget(
                GirdWidget('', (0, 0)),
                row, col
            )
        self.setUpTabAddPhoto(self.ui)

    def setUpTabAddPhoto(self, ui):
        # 绑定同步CheckBox状态改变信号和动作槽
        ui.ckbox_scrollMode.stateChanged['int'].connect(
            self.setScrollMode
        )
        ui.btn_encrypt.clicked.connect(
            self.encryptPhoto
        )
        self.setScrollMode(ui.ckbox_scrollMode.checkState())
        self.loadFilename = pics[0]  # for debug
        self.loadOriPhoto(ui, self.loadFilename)

    def loadOriPhoto(self, ui, filename):
        self.loadImage = JPEGImage(self.loadFilename)
        ui.lb_oriFilename.setText(
            self.strings['filename'] % (
                os.path.basename(self.loadFilename), 'original'
            )
        )
        ui.lb_oriSize.setText(
            self.strings['size'] % self.loadImage.size
        )
        ui.lb_oriImage.setImage(self.loadFilename, 300, 300)
        ui.lb_oriComponents.setText(
            self.strings['component'] % len(self.loadImage.comp_infos)
        )
        ui.txedt_oriComponents.setText(
            str(self.loadImage.comp_infos)
        )
        ui.lb_oriQuantTbls.setText(
            self.strings['quantization'] % len(self.loadImage.quant_tbls)
        )
        ui.txedt_oriQuantTbls.setText(
            str(self.loadImage.quant_tbls)
        )
        ui.lb_oriHuffTbls.setText(
            self.strings['huffman'] % (
                len(self.loadImage.dc_huff_tables),
                len(self.loadImage.ac_huff_tables)
                )
        )
        ui.txedt_oriHuffTbls.setText(
            str(self.loadImage.dc_huff_tables) +
            str(self.loadImage.ac_huff_tables)
        )

        # 成功载入后, 把Encrypt按钮设置为可用
        self.ui.btn_encrypt.setEnabled(True)

    def loadDstPhoto(self, ui, filename):
        self.loadImage = JPEGImage(self.loadFilename)
        ui.lb_dstFilename.setText(
            self.strings['filename'] % (
                os.path.basename(self.encryptedFilename), 'encrypted'
            )
        )
        ui.lb_dstSize.setText(
            self.strings['size'] % self.loadImage.size
        )
        ui.lb_dstImage.setImage(self.encryptedFilename, 300, 300)
        ui.lb_dstComponents.setText(
            self.strings['component'] % len(self.loadImage.comp_infos)
        )
        ui.txedt_dstComponents.setText(
            str(self.loadImage.comp_infos)
        )
        ui.lb_dstQuantTbls.setText(
            self.strings['quantization'] % len(self.loadImage.quant_tbls)
        )
        ui.txedt_dstQuantTbls.setText(
            str(self.loadImage.quant_tbls)
        )
        ui.lb_dstHuffTbls.setText(
            self.strings['huffman'] % (
                len(self.loadImage.dc_huff_tables),
                len(self.loadImage.ac_huff_tables)
                )
        )
        ui.txedt_dstHuffTbls.setText(
            str(self.loadImage.dc_huff_tables) +
            str(self.loadImage.ac_huff_tables)
        )

        # 成功载入后, 把Encrypt按钮设置为可用
        ui.btn_saveToLibrary.setEnabled(True)

    def encryptPhoto(self):
        cipher = JPEGImageCipher()
        cipher.encrypt(self.loadImage)
        self.encryptedFilename = os.path.join(
            self.paths['tmp'], os.path.basename(self.loadFilename)
        )
        print('save encrypted image to file:', self.encryptedFilename)
        self.loadImage.save(self.encryptedFilename)
        self.loadDstPhoto(self.ui, self.encryptedFilename)

    def setScrollMode(self, state):
        if state == Qt.Unchecked:
            self.ui.scrollArea_rightPhoto.verticalScrollBar().valueChanged['int'].disconnect(
                self.ui.scrollArea_leftPhoto.verticalScrollBar().setValue
            )
            self.ui.scrollArea_leftPhoto.verticalScrollBar().valueChanged['int'].disconnect(
                self.ui.scrollArea_rightPhoto.verticalScrollBar().setValue
            )
        elif state == Qt.Checked:
            self.ui.scrollArea_rightPhoto.verticalScrollBar().valueChanged['int'].connect(
                self.ui.scrollArea_leftPhoto.verticalScrollBar().setValue
            )
            self.ui.scrollArea_leftPhoto.verticalScrollBar().valueChanged['int'].connect(
                self.ui.scrollArea_rightPhoto.verticalScrollBar().setValue
            )

    def setPaths(self):
        path = sys.path[0]
        # 判断文件是编译后的文件还是脚本文件
        if os.path.isdir(path):  # 脚本文件目录
            exec_path = path
        else:  # 编译后的文件, 返回它的上一级目录
            exec_path = os.path.dirname(path)
        self.paths['root'] = exec_path
        self.paths['library'] = os.path.join(exec_path, 'library')
        self.paths['tmp'] = os.path.join(exec_path, 'tmp')
        self.ensurePathsExist()

    def ensurePathsExist(self):
        for _, path in self.paths.items():
            if not os.path.exists(path):
                os.makedirs(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
