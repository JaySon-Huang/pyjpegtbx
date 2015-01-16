## 目的
一个针对JPEG格式图像提取原始数据，方便图像数据操作的python库

* * *

## 开发环境
* Mac OS X
* python3.4
* gcc+llvm
* libjpeg

### 准备开发环境
`Mac OS X`:

    brew install python3
    brew install libjpeg

### Usage
`Mac OS X`:

    >>> gcc jpegparser.c -fPIC -shared -ljpeg -O2 -o libjpegtbx.so -framework Python
    >>> python3 JPEGImage.py

* * *

## Thanks
Thanks for Independent JPEG Group (ijg) providing the library for JPEG image compression. [link](http://www.ijg.org/)
