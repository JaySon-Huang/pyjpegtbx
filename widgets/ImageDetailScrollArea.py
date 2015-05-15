from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtWidgets import (
    QScrollArea, QLabel, QWidget, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout,
)

from .ImageLabel import ImageLabel
from .AdaptiveTreeWidget import AdaptiveTreeWidget


class ImageDetailScrollArea(QScrollArea):

    # signal
    imageLoaded = pyqtSignal()

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

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 380, 680))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        # title
        self.lb_title = QLabel(self.scrollAreaWidgetContents)
        self.lb_title.setAlignment(Qt.AlignCenter)
        self.lb_title.setObjectName("lb_title")
        self.verticalLayout.addWidget(self.lb_title)
        # filename && size
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lb_filename = QLabel(self.scrollAreaWidgetContents)
        self.lb_filename.setObjectName("lb_filename")
        self.horizontalLayout.addWidget(self.lb_filename)
        self.lb_size = QLabel(self.scrollAreaWidgetContents)
        self.lb_size.setObjectName("lb_size")
        self.horizontalLayout.addWidget(self.lb_size)
        self.verticalLayout.addLayout(self.horizontalLayout)
        # image preview
        self.lb_image = ImageLabel(self.scrollAreaWidgetContents)
        self.lb_image.setMinimumSize(QSize(250, 250))
        self.lb_image.setAlignment(Qt.AlignCenter)
        self.lb_image.setObjectName("lb_image")
        self.verticalLayout.addWidget(self.lb_image)
        # components
        self.lb_components = QLabel(self.scrollAreaWidgetContents)
        self.lb_components.setObjectName("lb_components")
        self.verticalLayout.addWidget(self.lb_components)
        self.treeWidget_components = AdaptiveTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_components.setUniformRowHeights(True)
        self.treeWidget_components.setObjectName("treeWidget_components")
        self.treeWidget_components.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget_components)
        # quant tables
        self.lb_quantTbls = QLabel(self.scrollAreaWidgetContents)
        self.lb_quantTbls.setObjectName("lb_quantTbls")
        self.verticalLayout.addWidget(self.lb_quantTbls)
        self.treeWidget_quantTbls = AdaptiveTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_quantTbls.setObjectName("treeWidget_quantTbls")
        self.treeWidget_quantTbls.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget_quantTbls)
        # huffman tables
        self.lb_huffTbls = QLabel(self.scrollAreaWidgetContents)
        self.lb_huffTbls.setObjectName("lb_huffTbls")
        self.verticalLayout.addWidget(self.lb_huffTbls)
        self.treeWidget_huffTbls = AdaptiveTreeWidget(self.scrollAreaWidgetContents)
        self.treeWidget_huffTbls.setObjectName("treeWidget_huffTbls")
        self.treeWidget_huffTbls.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget_huffTbls)

        # set the widgets into scrollArea
        self.setWidget(self.scrollAreaWidgetContents)
        self.clear()

    def clear(self):
        self.image = None
        self.lb_filename.setText(
            self.strings['filename'] % ('', 'NO image loaded')
        )
        self.lb_size.setText(
            self.strings['size'] % (0, 0)
        )
        self.lb_image.clear()
        self.lb_components.setText(
            self.strings['component'] % 0
        )
        self.treeWidget_components.clear()
        self.lb_quantTbls.setText(
            self.strings['quantization'] % 0
        )
        self.treeWidget_quantTbls.clear()
        self.lb_huffTbls.setText(
            self.strings['huffman'] % (0, 0)
        )
        self.treeWidget_huffTbls.clear()

    def setImage(self, image):
        self.image = image
        self.lb_filename.setText(
            self.strings['filename'] % (image.filename, 'original')
        )
        self.lb_size.setText(
            self.strings['size'] % image.size
        )
        self.lb_image.setImage(image.filepath, 300, 300)
        # components
        for comp in image.comp_infos:
            topItem = QTreeWidgetItem(
                self.treeWidget_components,
                [str(comp['component_id']), '', '']
            )
            for key in self.strings['showedComponentsInfo']:
                QTreeWidgetItem(topItem, ['', key, str(comp[key])])
        self.lb_components.setText(
            self.strings['component'] % len(image.comp_infos)
        )
        # quantization tables
        self.lb_quantTbls.setText(
            self.strings['quantization'] % len(image.quant_tbls)
        )
        for i, quant_tbl in enumerate(image.quant_tbls):
            topItem = QTreeWidgetItem(
                self.treeWidget_quantTbls,
                [str(i), '', '']
            )
            for key in quant_tbl:
                QTreeWidgetItem(topItem, ['', key, str(quant_tbl[key])])
        # huffman tables
        self.lb_huffTbls.setText(
            self.strings['huffman'] % (
                len(image.dc_huff_tbls),
                len(image.ac_huff_tbls)
                )
        )
        for i, hufftbl in enumerate(image.dc_huff_tbls):
            topItem = QTreeWidgetItem(
                self.treeWidget_huffTbls,
                [str(i), 'type', 'DC']
            )
            for key in hufftbl:
                QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
        for i, hufftbl in enumerate(image.ac_huff_tbls):
            topItem = QTreeWidgetItem(
                self.treeWidget_huffTbls,
                [str(i), 'type', 'AC']
            )
            for key in hufftbl:
                QTreeWidgetItem(topItem, ['', key, str(hufftbl[key])])
