#! /usr/bin/env python3
#encoding=utf-8

'''
ImageLabel - 点击可以显示原图大小尺寸图片的QLabel子类.
DoubleClickableLabel - 监听双击事件, emit doubleClicked signal 的QLabel子类
'''

from PyQt5.QtCore import Qt, pyqtSignal, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QDialog


class DoubleClickableLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)

    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
        self.doubleClicked.emit()


class ImageLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)
        self.filepath = None

    def setImageFileSrc(self, filepath, width, height):
        pic = QPixmap(filepath)
        self.pixmap = pic
        pic = pic.scaled(
            width, height, Qt.KeepAspectRatio
        )
        self.setPixmap(pic)
        # 修改鼠标样式
        self.setCursor(Qt.PointingHandCursor)

    def setImageMemSrc(self, img, width, height):
        pic = QPixmap()
        pic.loadFromData(img.save2Bytes())
        self.pixmap = pic
        pic = pic.scaled(
            width, height, Qt.KeepAspectRatio
        )
        self.setPixmap(pic)
        self.setCursor(Qt.PointingHandCursor)

    def clear(self):
        self.pixmap = None
        super().clear()

    def mousePressEvent(self, ev):
        if self.pixmap:
            self.w = QDialog(parent=self)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.w.setLayout(layout)

            # 弹出窗口的内容
            # view = QLabel()
            view = DoubleClickableLabel()
            pic = QPixmap(self.pixmap)
            view.setPixmap(pic)
            view.doubleClicked.connect(
                self.w.close
            )
            layout.addWidget(view)

            self.w.show()
        super().mousePressEvent(ev)
