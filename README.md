## 开发环境
* Mac OS X
* python3.4
* gcc+llvm

### Usage
    >>> gcc jpegparser.c -fPIC -shared -ljpeg -O2 -o libjpegtbx.so -framework Python
    >>> python3 JPEGImage.py
