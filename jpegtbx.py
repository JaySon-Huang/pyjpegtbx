import os
import sys
from PyQt5.QtCore import (
    QDir, Qt
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QItemDelegate, QLabel
)
from PyQt5.QtGui import (
    QPixmap, QStandardItemModel, QStandardItem
)

import ui_jpegtbx


class ImageDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        '''
        returns the widget used to change data from the model
        and can be reimplemented to customize editing behavior.
        '''
        label = QLabel(parent)
        # pic = QPixmap(filename)
        # label.setPixmap(pic)
        return label

    def setEditorData(self, editor, index):
        '''
        provides the widget with data to manipulate.
        '''
        imgItem = index.model().item(index.row(), index.column())
        pic = QPixmap(imgItem.filename)
        # picScaled = pic.scaled(imgItem.size[0], imgItem.size[1], Qt.KeepAspectRatio)
        # editor.setPixmap(QPixmap.fromImage(picScaled))
        editor.setPixmap(pic)

    def setModelData(self, editor, model, index):
        '''
        returns updated data to the model.
        '''
        super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        '''
        ensures that the editor is displayed correctly with respect to the item view.
        '''
        editor.setGeometry(option.rect)


class ImageItem(QStandardItem):
    def __init__(self, filename, size):
        super().__init__()
        self.filename = filename
        self.size = size

pics = ['lfs.jpg', 'tmp0.jpg', 'tmp1.jpg']


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = ui_jpegtbx.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setCurFilePath()

        self.mainViewSize = {'col': 4, 'row': 3}  # col, row
        self.mainViewModel = QStandardItemModel()
        self.mainViewModel.setColumnCount(self.mainViewSize['col'])
        self.mainViewModel.setRowCount(self.mainViewSize['row'])
        # 绑定model
        self.ui.mainView.setModel(self.mainViewModel)
        # 加载Delegate类
        delegate = ImageDelegate()
        self.ui.mainView.setItemDelegate(delegate)
        for i, pic in enumerate(pics):
            col, row = i % self.mainViewSize['col'], i / self.mainViewSize['col']
            item = ImageItem(pic, (250, 250))
            self.mainViewModel.setItem(row, col, item)

    def setCurFilePath(self, filepath=None):
        if not filepath:
            path = sys.path[0]
            # 判断文件是编译后的文件还是脚本文件
            if os.path.isdir(path):  # 脚本文件目录
                dirpath = path
            else:  # 编译后的文件, 返回它的上一级目录
                dirpath = os.path.dirname(path)
        else:
            pass
        self.ui.le_curFilepath.setText(dirpath)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
