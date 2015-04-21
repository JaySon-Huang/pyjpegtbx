from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout


class ImageLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)
        self.filepath = None

    def setImage(self, filepath, width, height):
        self.filepath = filepath
        pic = QPixmap(filepath)
        pic = pic.scaled(
            width, height, Qt.KeepAspectRatio
        )
        self.setPixmap(pic)

    def mousePressEvent(self, ev):
        if self.filepath:
            self.w = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.w.setLayout(layout)
            view = QLabel()
            pic = QPixmap(self.filepath)
            view.setPixmap(pic)
            layout.addWidget(view)
            self.w.show()
        super().mousePressEvent(ev)
