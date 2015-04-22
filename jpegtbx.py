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
    QWidget, QScrollArea, QGraphicsWidget, QFileDialog, QTreeWidgetItem
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
    '''Main Window of Secret Photo'''

    # static strings
    strings = {
        'filename': 'filename: %s (%s)',
        'size': 'size: %d x %d',
        'component': 'Components (%d in total)',
        'quantization': 'Quantization tables (%d in total)',
        'huffman': 'Huffman tables (%d for DC, %d for AC)',
        'showedComponentsInfo': [
            'dc_tbl_no',
            'ac_tbl_no',
            'quant_tbl_no',
            'h_samp_factor',
            'v_samp_factor',
            ],
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
        self.loaded = {}

        self.mainViewSize = {'col': 3, 'row': 3}  # col, row

        girdLayout_viewLibrary = QGridLayout(
            self.ui.scrollAreaWidgetContents
        )
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
            self.btn_encryptPhoto_clicked
        )
        ui.btn_loadImage.clicked.connect(
            self.btn_loadImage_clicked
        )
        ui.btn_saveToLibrary.clicked.connect(
            self.btn_saveToLibrary_clicked
        )
        ui.treeWidget_oriComponents.header().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.setScrollMode(ui.ckbox_scrollMode.checkState())
        self.__loadOriPhoto(ui, pics[0])  # for debug

    def __loadOriPhoto(self, ui, filepath):
        '''load original photo by filepath if filepath is not NULL;
        otherwise set Label to be default value.
        '''
        if filepath:
            self.loaded['oriFilepath'] = filepath
            img = JPEGImage(filepath)
            self.loaded['oriImage'] = img
            ui.lb_oriFilename.setText(
                self.strings['filename'] % (
                    os.path.basename(filepath), 'original'
                )
            )
            ui.lb_oriSize.setText(
                self.strings['size'] % img.size
            )
            ui.lb_oriImage.setImage(filepath, 300, 300)
            for comp in img.comp_infos:
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriComponents,
                    [str(comp['component_id']), '', '']
                )
                for key in self.strings['showedComponentsInfo']:
                    QTreeWidgetItem(topItem, ['', key, str(comp[key])])
            ui.lb_oriComponents.setText(
                self.strings['component'] % len(img.comp_infos)
            )
            ui.lb_oriQuantTbls.setText(
                self.strings['quantization'] % len(img.quant_tbls)
            )
            for i, quant_tbl in enumerate(img.quant_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriQuantTbls,
                    [str(i), '', '']
                )
                for key in quant_tbl:
                    QTreeWidgetItem(topItem, ['', key, str(quant_tbl[key])])
            ui.lb_oriHuffTbls.setText(
                self.strings['huffman'] % (
                    len(img.dc_huff_tables),
                    len(img.ac_huff_tables)
                    )
            )
            for i, hufftbl in enumerate(img.dc_huff_tables):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriHuffTbls,
                    [str(i), 'type', 'DC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            for i, hufftbl in enumerate(img.ac_huff_tables):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriHuffTbls,
                    [str(i), 'type', 'AC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            # 成功载入后, 把Encrypt按钮设置为可用
            ui.btn_encrypt.setEnabled(True)
        else:
            self.loaded['oriFilepath'] = None
            self.loaded['oriImage'] = None
            ui.lb_oriFilename.setText(
                self.strings['filename'] % ('', 'NO image loaded')
            )
            ui.lb_oriSize.setText(
                self.strings['size'] % (0, 0)
            )
            ui.lb_oriImage.clear()
            ui.lb_oriComponents.setText(
                self.strings['component'] % 0
            )
            ui.lb_oriQuantTbls.setText(
                self.strings['quantization'] % 0
            )
            ui.lb_oriHuffTbls.setText(
                self.strings['huffman'] % (0, 0)
            )
            ui.btn_encrypt.setEnabled(False)

    def __loadDstPhoto(self, ui, filepath):
        if filepath:
            self.loaded['dstFilepath'] = filepath
            img = JPEGImage(filepath)
            self.loaded['dstImage'] = img
            ui.lb_dstFilename.setText(
                self.strings['filename'] % (
                    os.path.basename(filepath), 'original'
                )
            )
            ui.lb_dstSize.setText(
                self.strings['size'] % img.size
            )
            ui.lb_dstImage.setImage(filepath, 300, 300)
            for comp in img.comp_infos:
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstComponents,
                    [str(comp['component_id']), '', '']
                )
                for key in self.strings['showedComponentsInfo']:
                    QTreeWidgetItem(topItem, ['', key, str(comp[key])])
            ui.lb_dstComponents.setText(
                self.strings['component'] % len(img.comp_infos)
            )
            ui.lb_dstQuantTbls.setText(
                self.strings['quantization'] % len(img.quant_tbls)
            )
            for i, quant_tbl in enumerate(img.quant_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstQuantTbls,
                    [str(i), '', '']
                )
                for key in quant_tbl:
                    QTreeWidgetItem(topItem, ['', key, str(quant_tbl[key])])
            ui.lb_dstHuffTbls.setText(
                self.strings['huffman'] % (
                    len(img.dc_huff_tables),
                    len(img.ac_huff_tables)
                    )
            )
            for i, hufftbl in enumerate(img.dc_huff_tables):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstHuffTbls,
                    [str(i), 'type', 'DC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            for i, hufftbl in enumerate(img.ac_huff_tables):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstHuffTbls,
                    [str(i), 'type', 'AC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            # 成功载入后, 把Encrypt按钮设置为可用
            ui.btn_saveToLibrary.setEnabled(True)
        else:
            self.loaded['dstFilepath'] = None
            self.loaded['dstImage'] = None
            ui.lb_dstFilename.setText(
                self.strings['filename'] % ('', 'NO image loaded')
            )
            ui.lb_dstSize.setText(
                self.strings['size'] % (0, 0)
            )
            ui.lb_dstImage.clear()
            ui.lb_dstComponents.setText(
                self.strings['component'] % 0
            )
            ui.lb_dstQuantTbls.setText(
                self.strings['quantization'] % 0
            )
            ui.lb_dstHuffTbls.setText(
                self.strings['huffman'] % (0, 0)
            )
            ui.btn_saveToLibrary.setEnabled(False)

    def btn_loadImage_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            parent=self, caption='Open', directory='', filter='*.jpg'
        )
        if filepath:
            # set ori side
            self.__loadOriPhoto(self.ui, filepath)
            # clear dst side
            self.__loadDstPhoto(self.ui, '')

    def btn_encryptPhoto_clicked(self):
        cipher = JPEGImageCipher()
        self.loaded['dstImage'] = cipher.encrypt(self.loaded['oriImage'])
        self.loaded['dstFilepath'] = os.path.join(
            self.paths['tmp'], os.path.basename(self.loaded['oriFilepath'])
        )
        print('save encrypted image to file:', self.loaded['dstFilepath'])
        self.loaded['dstImage'].save(self.loaded['dstFilepath'])
        self.__loadDstPhoto(self.ui, self.loaded['dstFilepath'])

    def btn_saveToLibrary_clicked(self):
        libpath = os.path.join(
            self.paths['library'], os.path.basename(self.loaded['dstFilepath'])
        )
        os.rename(self.loaded['dstFilepath'], libpath)
        print('file: %s moved to %s' % (self.loaded['dstFilepath'], libpath))
        self.loaded['dstFilepath'] = libpath
        self.loaded['dstImage'].filename = libpath

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
