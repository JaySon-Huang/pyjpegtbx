#! /usr/bin/env python3
#encoding=utf-8

import os
import sys
import json
import hashlib
from functools import partial

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
from utils.fileUtils import (
    paths, setupPaths, getTmpFilepath, getLibFilepath, moveToLibrary
)

pics = ['lfs.jpg', 'tmp0.jpg', 'tmp1.jpg']


class MainWindow(QMainWindow):
    '''Main Window of Secret Photo'''

    # property
    properties = {
        'columnSize': 3
    }
    # static strings
    strings = {
        'format': {
            'extract': 'Message extract:\n%s',
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.loaded = {}
        self.seed = None

        self.setUpTabLibrary(self.ui)
        self.setUpTabAddPhoto(self.ui)

    def setUpTabLibrary(self, ui):
        ui.btn_enterPassword.clicked.connect(
            self.btn_enterPassword_clicked
        )
        libfiles = []
        for filename in os.listdir(paths['library']):
            if filename.endswith('jpeg') or filename.endswith('.jpg'):
                libfiles.append(os.path.join(paths['library'], filename))
        print('files in library:', libfiles)
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
            partial(self.btn_encryptPhoto_clicked, toEmbMessage=False)
        )
        ui.btn_decrypt.clicked.connect(
            partial(self.btn_decryptPhoto_clicked, toExtractMessage=False)
        )
        ui.btn_loadImage.clicked.connect(
            self.btn_loadImage_clicked
        )

        ui.btn_saveToLibrary.clicked.connect(
            self.btn_saveToLibrary_clicked
        )

        ui.saContents_ori.imageLoaded.connect(
            partial(self.__setBtnEnable, enable=True)
        )
        ui.saContents_ori.imageCleared.connect(
            partial(self.__setBtnEnable, enable=False)
        )

        ui.btn_encryptEmb.clicked.connect(
            partial(self.btn_encryptPhoto_clicked, toEmbMessage=True)
        )
        ui.btn_decryptExtract.clicked.connect(
            partial(self.btn_decryptPhoto_clicked, toExtractMessage=True)
        )

        ui.saContents_ori.setTitle('Original')
        ui.saContents_dst.setTitle('Destination')
        ui.lb_msg.setText('')
        # 更新当前是否同步滚动
        self.setScrollMode(ui.ckbox_scrollMode.checkState())
        # self.__loadOriPhoto(ui, pics[0])  # for debug

    def __setBtnEnable(self, enable):
        # 成功载入后, 把 Encrypt/Decrypt 按钮设置为可用
        self.ui.btn_encrypt.setEnabled(enable)
        self.ui.btn_decrypt.setEnabled(enable)
        self.ui.btn_encryptEmb.setEnabled(enable)
        self.ui.btn_decryptExtract.setEnabled(enable)

    def __loadOriPhoto(self, ui, filepath):
        '''load original photo by filepath if filepath is not NULL;
        otherwise set Label to be default value.
        '''
        if filepath:
            self.loaded['oriFilepath'] = filepath
            img = JPEGImage.open(filepath)
            self.loaded['oriImage'] = img
            ui.saContents_ori.setImage(img)
        else:
            self.loaded['oriFilepath'] = None
            self.loaded['oriImage'] = None
            ui.saContents_ori.clear()

    def __loadDstPhoto(self, ui, filepath):
        if filepath:
            self.loaded['dstFilepath'] = filepath
            img = JPEGImage.open(filepath)
            self.loaded['dstImage'] = img
            ui.saContents_dst.setImage(img)
            # 成功载入后, 把Encrypt按钮设置为可用
            ui.btn_saveToLibrary.setEnabled(True)
        else:
            self.loaded['dstFilepath'] = None
            self.loaded['dstImage'] = None
            ui.saContents_dst.clear()
            ui.btn_saveToLibrary.setEnabled(False)

    def __loadDstPhotoFromImage(self, ui, img):
        if img:
            self.loaded['dstFilepath'] = None
            self.loaded['dstImage'] = img
            ui.saContents_dst.setImage(img)
            # 成功载入后, 把Encrypt按钮设置为可用
            ui.btn_saveToLibrary.setEnabled(True)
        else:
            self.loaded['dstFilepath'] = None
            self.loaded['dstImage'] = None
            ui.saContents_dst.clear()
            ui.btn_saveToLibrary.setEnabled(False)

    def btn_enterPassword_clicked(self):
        password, isOK = QInputDialog.getText(
            self, 'Enter your password', 'Password:',
            QLineEdit.Password
        )
        if isOK:
            print('Password is:', password)
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
        return isOK

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

    def btn_encryptPhoto_clicked(self, toEmbMessage):
        if not self.seed:
            if not self.btn_enterPassword_clicked():
                # 取消输入密码
                return
        self.__loadDstPhotoFromImage(self.ui, None)
        cipher = JPEGImageCipher(self.seed)
        if toEmbMessage:
            msg, isOK = QInputDialog.getMultiLineText(
                self, 'Enter the message you want to emb',
                'Message:'
            )
            bdata = msg.encode('utf-8')
            print('get `%s`<=>`%s` from input dialog' % (msg, bdata))
            img = cipher.encrtptAndEmbData(self.loaded['oriImage'], bdata)
        else:
            img = cipher.encrypt(self.loaded['oriImage'])
        ## 先保存临时文件, 再载入临时文件显示图片 ##
        # tmpFilepath = self.__saveToTempFile(img, img.filename)
        # self.__loadDstPhoto(self.ui, tmpFilepath)
        ## 直接通过JPEGImage对象的接口中载入图像数据 ##
        self.__loadDstPhotoFromImage(self.ui, img)

    def btn_decryptPhoto_clicked(self, toExtractMessage):
        if not self.seed:
            if not self.btn_enterPassword_clicked():
                # 取消输入密码
                return
        cipher = JPEGImageCipher(self.seed)
        if toExtractMessage:
            img, bdata = cipher.decryptAndExtractData(self.loaded['oriImage'])
            msg = bdata.decode('utf-8')
            print('The message extract is:`%s`<=>`%s`' % (bdata, msg))
            self.ui.lb_msg.setText(
                self.strings['format']['extract'] % msg
            )
        else:
            img = cipher.decrypt(self.loaded['oriImage'])
        ## 先保存临时文件, 再载入临时文件显示图片 ##
        # tmpFilepath = self.__saveToTempFile(img, img.filename)
        # self.__loadDstPhoto(self.ui, tmpFilepath)
        ## 直接通过JPEGImage对象的接口中载入图像数据 ##
        self.__loadDstPhotoFromImage(self.ui, img)

    def __saveToTempFile(self, img, filename):
        '''保存self.loaded['dstImage']对象中存储的图像到`tmp`文件夹下,
        并把路径名存储到`self.loaded['dstFilepath']`中'''
        self.loaded['dstFilepath'] = getTmpFilepath(filename)
        print(
            'save encrypted/decrypted image to temp file:',
            self.loaded['dstFilepath']
        )
        img.save(self.loaded['dstFilepath'])
        return self.loaded['dstFilepath']

    def btn_saveToLibrary_clicked(self):
        ## 使用临时文件存储的方式, 直接移动文件 ##
        # libpath = moveToLibrary(self.loaded['dstFilepath'])
        # print('file: %s moved to %s' % (self.loaded['dstFilepath'], libpath))
        # self.loaded['dstFilepath'] = libpath
        # self.loaded['dstImage'].filename = libpath
        ## 把self.loaded['dstImage']保存到`paths.library`中 ##
        filepath = getLibFilepath(self.loaded['oriFilepath'])
        self.loaded['dstFilepath'] = filepath
        self.loaded['dstImage'].save(filepath)

    def setScrollMode(self, state):
        if state == Qt.Unchecked:
            self.ui.scrollArea_ori.verticalScrollBar().valueChanged['int'].disconnect(
                self.ui.scrollArea_dst.verticalScrollBar().setValue
            )
            self.ui.scrollArea_dst.verticalScrollBar().valueChanged['int'].disconnect(
                self.ui.scrollArea_ori.verticalScrollBar().setValue
            )
        elif state == Qt.Checked:
            self.ui.scrollArea_ori.verticalScrollBar().valueChanged['int'].connect(
                self.ui.scrollArea_dst.verticalScrollBar().setValue
            )
            self.ui.scrollArea_dst.verticalScrollBar().valueChanged['int'].connect(
                self.ui.scrollArea_ori.verticalScrollBar().setValue
            )


def main():
    setupPaths()

    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
