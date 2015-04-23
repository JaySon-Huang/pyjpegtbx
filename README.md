## 目的
一个针对JPEG格式图像提取原始数据，方便图像数据操作的python库

* * *

## My Develop environment
* Mac OS X
* python3 (3.4.2)
* gcc (4.9.2) + llvm (3.5.0)
* libjpeg (8d)
* qt5 (5.4.0)
* PyQt5 (5.3.2)

### Prepare for develop environment
`in Mac OS X`:

    brew install python3
    brew install libjpeg

    brew install qt5
    brew install pyqt5


### Install

    >>> python3 setup.py install

### Usage (English Version)
    
    >>> from pyjpegtbx import JPEGImage
    >>> 
    >>> # False for reading RGB data
    >>> img = JPEGImage('lfs.jpg', False)
    >>> newdata = []
    >>> # RGB data now is in img.data
    >>> for rgb in img.data:
    >>>     newdata.append((0, rgb[1], rgb[2]))
    >>> img.data = newdata
    >>> img.save('tmp0.jpg')
    >>> 
    >>> # True(default) for reading DCT data
    >>> img = JPEGImage('lfs.jpg')
    >>> # components' info
    >>> print img.comp_infos
    >>> # quality tables
    >>> print img.quant_tbls
    >>> # huffman tables
    >>> print img.ac_huff_tables
    >>> print img.dc_huff_tables
    >>> print img.filename
    >>> print img.size # (width, height)
    >>> # DCT data now is in img.data
    >>> # print img.data
    >>> # set some of DCT data to zero
    >>> for key, val in img.data.items():
    >>>     for coef in val:
    >>>         for i in range(32, 64):
    >>>             coef[i] = 0
    >>> img.save('tmp1.jpg')

### Usage (中文版)
    
    >>> from pyjpegtbx import JPEGImage
    >>> 
    >>> # 第二个参数为False, 表示读取RGB数据
    >>> img = JPEGImage('lfs.jpg', False)
    >>> newdata = []
    >>> # img.data中存储着RGB数据
    >>> for rgb in img.data:
    >>>     newdata.append((0, rgb[1], rgb[2]))
    >>> img.data = newdata
    >>> img.save('tmp0.jpg')
    >>> 
    >>> # 第二个参数默认为True, 表示读取DCT数据
    >>> img = JPEGImage('lfs.jpg')
    >>> # 查看颜色分量信息
    >>> print img.comp_infos
    >>> # 量化表
    >>> print img.quant_tbls
    >>> # 哈夫曼表
    >>> print img.ac_huff_tables
    >>> print img.dc_huff_tables
    >>> # 文件名
    >>> print img.filename
    >>> # (width, height)
    >>> print img.size
    >>> # DCT数据信息
    >>> # print img.data
    >>> # 把高频DCT系数设置为0
    >>> for key, val in img.data.items():
    >>>     for coef in val:
    >>>         for i in range(32, 64):
    >>>             coef[i] = 0
    >>> img.save('tmp1.jpg')

### Gui Version
    
    >>> python3 jpegtbx.py

* * *

## Thanks
* Thanks for Independent JPEG Group (ijg) providing the library for JPEG image compression. [link](http://www.ijg.org/)
* Thanks for these article [使用C语言扩展Python(一)~(五)](http://www.cnblogs.com/phinecos/archive/2010/05/17/1737033.html)
