#/usr/bin/env python3

import ctypes
_lib = ctypes.CDLL("./libjpegtbx.so")

_lib.parse.restype = ctypes.py_object
_lib.parse.argtypes = [ctypes.c_char_p, ctypes.c_int]


J_COLOR_SPACE = {
    0:'UNKNOWN',    # error/unspecified
    1:'GRAYSCALE',  # monochrome
    2:'RGB',        # red/green/blue, standard RGB (sRGB)
    3:'YCbCr',      # Y/Cb/Cr (also known as YUV), standard YCC
    4:'CMYK',       # C/M/Y/K
    5:'YCCK',       # Y/Cb/Cr/K
    6:'BG_RGB',     # big gamut red/green/blue, bg-sRGB
    7:'BG_YCC',     # big gamut Y/Cb/Cr, bg-sYCC
}

class JPEGImage:
    # size => (width, height)
    # color_space 
    # quant_tbl => a list of quant table
    # huff_tbl_ptrs => {'dc':[[][]], 'ac':[[][]]}
    def __init__(self, filename):
        self.filename = filename
        self.data = None
        self.dctdata = None

    @classmethod
    def open(cls, filename, get_rawdct=False):
        img = cls(filename)
        # cfilename = ctypes.create_string_buffer(filename.encode(encoding="utf-8"))
        ret = _lib.parse(filename.encode(encoding="utf-8"), get_rawdct)
        img.size = ret['size']
        img._color_space = ret['color_space']
        img.data = ret['data']
        if get_rawdct:
            pass
        else:
            pass
        return img

    def save(self, filename):
        raise NotImplementedError()

if __name__ == "__main__":
    filename = "lfs.jpg"
    img = JPEGImage.open(filename)

    from PIL import Image
    img2 = Image.open(filename)
    l = list(img2.getdata())

    for x in range(len(l)):
        if img.data[x] != l[x]:
            print("Err")

