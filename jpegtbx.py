#! /usr/bin/env python3
#encoding=utf-8

import os
import sys
import json
import hashlib

from pyjpegtbx import JPEGImage
# from JPEGImageCipher import JPEGImageCipher0 as JPEGImageCipher
from cipher.JPEGImageCipher import JPEGImageCipher1 as JPEGImageCipher

from PyQt5.QtCore import (
    QDir, Qt, QVariant
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QItemDelegate, QLabel, QHeaderView, QGridLayout,
    QWidget, QScrollArea, QGraphicsWidget, QFileDialog, QTreeWidgetItem,
    QSizePolicy, QInputDialog, QLineEdit
)
from PyQt5.QtGui import (
    QPixmap, QStandardItemModel, QStandardItem
)

from widgets.GridWidget import GridWidget
from widgets.ui_MainWindow import Ui_MainWindow

pics = ['lfs.jpg', 'tmp0.jpg', 'tmp1.jpg']


class MainWindow(QMainWindow):
    '''Main Window of Secret Photo'''

    # property
    properties = {
        'columnSize': 3
    }
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
        self.seed = None

        self.setUpTabLibrary(self.ui)
        self.setUpTabAddPhoto(self.ui)

    def setUpTabLibrary(self, ui):
        ui.btn_enterPassword.clicked.connect(
            self.btn_enterPassword_clicked
        )
        libfiles = [
            os.path.join(self.paths['library'], _)
            for _ in os.listdir(self.paths['library'])
        ]
        print('files', libfiles)
        self.ui.libraryWidgets = []

        sp = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sp.setHorizontalStretch(0)
        sp.setVerticalStretch(0)

        for i, filepath in enumerate(libfiles):
            col = i % self.properties['columnSize']
            row = i // self.properties['columnSize']
            widget = GridWidget(ui.scrollAreaWidgetContents)
            sp.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
            widget.setSizePolicy(sp)
            widget.setContent(filepath, (250, 250))
            ui.gridLayout.addWidget(
                widget, row, col, Qt.AlignHCenter | Qt.AlignVCenter
            )
            self.ui.libraryWidgets.append(widget)
        while i < 11:
            i += 1
            col = i % self.properties['columnSize']
            row = i // self.properties['columnSize']
            widget = GridWidget(ui.scrollAreaWidgetContents)
            sp.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
            widget.setSizePolicy(sp)
            widget.setContent('', None)
            ui.gridLayout.addWidget(
                widget, row, col, Qt.AlignHCenter | Qt.AlignVCenter
            )
            self.ui.libraryWidgets.append(widget)

    def setUpTabAddPhoto(self, ui):
        # 绑定同步CheckBox状态改变信号和动作槽
        ui.ckbox_scrollMode.stateChanged['int'].connect(
            self.setScrollMode
        )
        ui.btn_encrypt.clicked.connect(
            self.btn_encryptPhoto_clicked
        )
        ui.btn_decrypt.clicked.connect(
            self.btn_decryptPhoto_clicked
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
            img = JPEGImage.open(filepath)
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
                    len(img.dc_huff_tbls),
                    len(img.ac_huff_tbls)
                    )
            )
            for i, hufftbl in enumerate(img.dc_huff_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriHuffTbls,
                    [str(i), 'type', 'DC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            for i, hufftbl in enumerate(img.ac_huff_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_oriHuffTbls,
                    [str(i), 'type', 'AC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            # 成功载入后, 把 Encrypt/Decrypt 按钮设置为可用
            ui.btn_encrypt.setEnabled(True)
            ui.btn_decrypt.setEnabled(True)
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
            ui.treeWidget_oriComponents.clear()
            ui.lb_oriQuantTbls.setText(
                self.strings['quantization'] % 0
            )
            ui.treeWidget_oriQuantTbls.clear()
            ui.lb_oriHuffTbls.setText(
                self.strings['huffman'] % (0, 0)
            )
            ui.treeWidget_oriHuffTbls.clear()
            ui.btn_encrypt.setEnabled(False)
            ui.btn_decrypt.setEnabled(False)

    def __loadDstPhoto(self, ui, filepath):
        if filepath:
            self.loaded['dstFilepath'] = filepath
            img = JPEGImage.open(filepath)
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
                    len(img.dc_huff_tbls),
                    len(img.ac_huff_tbls)
                    )
            )
            for i, hufftbl in enumerate(img.dc_huff_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstHuffTbls,
                    [str(i), 'type', 'DC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            for i, hufftbl in enumerate(img.ac_huff_tbls):
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
            ui.treeWidget_dstComponents.clear()
            ui.lb_dstQuantTbls.setText(
                self.strings['quantization'] % 0
            )
            ui.treeWidget_dstQuantTbls.clear()
            ui.lb_dstHuffTbls.setText(
                self.strings['huffman'] % (0, 0)
            )
            ui.treeWidget_dstHuffTbls.clear()
            ui.btn_saveToLibrary.setEnabled(False)

    def btn_enterPassword_clicked(self):
        password, isOK = QInputDialog.getText(
            self, 'Enter your password', 'Password:',
            QLineEdit.Password
        )
        if isOK:
            print(password)
            h = hashlib.md5(password.encode('utf-8')).digest()
            front, back = 0, 0
            for i, num in enumerate(h):
                if i < 8:
                    front <<= 8
                    front += num
                    front &= 0xFFFFFFFF
                else:
                    back <<= 8
                    back += num
                    back &= 0xFFFFFFFF
            front *= 1.0
            back *= 1.0
            self.seed = front/back if front < back else back/front

    def btn_loadImage_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            parent=self, caption='Open', directory='', filter='*.jpg'
        )
        if filepath:
            # clear ori side
            self.__loadOriPhoto(self.ui, '')
            # set ori side
            self.__loadOriPhoto(self.ui, filepath)
            # clear dst side
            self.__loadDstPhoto(self.ui, '')

    def __loadDstPhotoFromImage(self, ui, img):
        if img:
            self.loaded['dstImage'] = img
            ui.lb_dstFilename.setText(
                self.strings['filename'] % (
                    '(in memory)', 'original'
                )
            )
            ui.lb_dstSize.setText(
                self.strings['size'] % img.size
            )
            ui.lb_dstImage.setImageMemSrc(img, 300, 300)
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
                    len(img.dc_huff_tbls),
                    len(img.ac_huff_tbls)
                    )
            )
            for i, hufftbl in enumerate(img.dc_huff_tbls):
                topItem = QTreeWidgetItem(
                    ui.treeWidget_dstHuffTbls,
                    [str(i), 'type', 'DC']
                )
                for key in hufftbl:
                    QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
            for i, hufftbl in enumerate(img.ac_huff_tbls):
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
            ui.treeWidget_dstComponents.clear()
            ui.lb_dstQuantTbls.setText(
                self.strings['quantization'] % 0
            )
            ui.treeWidget_dstQuantTbls.clear()
            ui.lb_dstHuffTbls.setText(
                self.strings['huffman'] % (0, 0)
            )
            ui.treeWidget_dstHuffTbls.clear()
            ui.btn_saveToLibrary.setEnabled(False)

    def btn_encryptPhoto_clicked(self):
        if not self.seed:
            self.btn_enterPassword_clicked()
        cipher = JPEGImageCipher(self.seed)
        self.loaded['dstImage'] = cipher.encrypt(self.loaded['oriImage'])
        ## 先保存临时文件, 再载入临时文件显示图片 ##
        # filename = os.path.basename(self.loaded['oriFilepath'])
        # self.__saveToTempFile(filename)
        # self.__loadDstPhoto(self.ui, self.loaded['dstFilepath'])
        ## 直接通过JPEGImage对象的接口中载入图像数据 ##
        self.__loadDstPhotoFromImage(self.ui, self.loaded['dstImage'])

    def btn_decryptPhoto_clicked(self):
        if not self.seed:
            self.btn_enterPassword_clicked()
        cipher = JPEGImageCipher(self.seed)
        self.loaded['dstImage'] = cipher.decrypt(self.loaded['oriImage'])
        ## 先保存临时文件, 再载入临时文件显示图片 ##
        # filename = os.path.basename(self.loaded['oriFilepath'])
        # self.__saveToTempFile(filename)
        # self.__loadDstPhoto(self.ui, self.loaded['dstFilepath'])
        ## 直接通过JPEGImage对象的接口中载入图像数据 ##
        self.__loadDstPhotoFromImage(self.ui, self.loaded['dstImage'])

    def __saveToTempFile(self, filename):
        '''保存self.loaded['dstImage']对象中存储的图像到`paths.tmp`文件夹下,
        并把路径名存储到`self.loaded['dstFilepath']`中'''
        self.loaded['dstFilepath'] = os.path.join(
            self.paths['tmp'], filename
        )
        print(
            'save encrypted/decrypted image to temp file:',
            self.loaded['dstFilepath']
        )
        self.loaded['dstImage'].save(self.loaded['dstFilepath'])

    def btn_saveToLibrary_clicked(self):
        ## 使用临时文件存储的方式, 直接移动文件 ##
        # libpath = os.path.join(
        #     self.paths['library'], os.path.basename(self.loaded['dstFilepath'])
        # )
        # os.rename(self.loaded['dstFilepath'], libpath)
        # print('file: %s moved to %s' % (self.loaded['dstFilepath'], libpath))
        # self.loaded['dstFilepath'] = libpath
        # self.loaded['dstImage'].filename = libpath
        ## 把self.loaded['dstImage']保存到`paths.library`中 ##
        filepath = os.path.join(
            self.paths['library'], os.path.basename(self.loaded['oriFilepath'])
        )
        self.loaded['dstFilepath'] = filepath
        self.loaded['dstImage'].save(filepath)

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
