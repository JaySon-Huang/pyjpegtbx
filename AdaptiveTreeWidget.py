#! /usr/bin/env python3
#encoding=utf-8

'''
AdaptiveTreeWidget - 展开/收缩过程中自适应高度的QTreeWidget
'''

from functools import partial

from PyQt5.QtWidgets import QTreeWidget


class AdaptiveTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set the minimum height
        self.MIN_HEIGHT = self.minimumSizeHint().height()
        self._height = self.MIN_HEIGHT
        self.setFixedHeight(self._height)

        self.expanded['QModelIndex'].connect(
            partial(self.onItemStatusChanged, isExpand=True)
        )
        self.collapsed['QModelIndex'].connect(
            partial(self.onItemStatusChanged, isExpand=False)
        )
        self.expandAll()

    def onItemStatusChanged(self, index, isExpand):
        '''onItemStatusChanged(self, index, isExpand)
        fit the height when item Expanded/Collapsed
        increase the height when isExpand = True; otherwise decrease the height
        '''
        childCnt = 0
        while True:
            ind = index.child(childCnt, 0)
            if not ind.isValid():
                break
            childCnt += 1
        if isExpand:
            self._height += self.rowHeight(index) * childCnt
        else:
            self._height -= self.rowHeight(index) * childCnt
        # not less than minimum height
        if self._height < self.MIN_HEIGHT:
            self._height = self.MIN_HEIGHT
        self.setFixedHeight(self._height)
