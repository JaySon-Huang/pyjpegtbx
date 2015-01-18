#/usr/bin/env python3

import ctypes
_lib = ctypes.CDLL("./libjpegtbx.so")

_lib.parse.restype = ctypes.py_object
_lib.parse.argtypes = [ctypes.c_char_p, ctypes.c_int]

_lib.save_from_rgb.restype = ctypes.c_int
_lib.save_from_rgb.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]

J_COLOR_SPACE = {
    0:('UNKNOWN'  , None),      # error/unspecified
    1:('GRAYSCALE', ('Grey',)       ),       # monochrome
    2:('RGB'      , ('R','G','B')   ),       # red/green/blue, standard RGB (sRGB)
    3:('YCbCr'    , ('Y','Cb','Cr') ),       # Y/Cb/Cr (also known as YUV), standard YCC
    4:('CMYK'     , ('C','M','Y','K')   ),   # C/M/Y/K
    5:('YCCK'     , ('Y','Cb','Cr','K') ),   # Y/Cb/Cr/K
    6:('BG_RGB'   , None),      # big gamut red/green/blue,) bg-sRGB
    7:('BG_YCC'   , None),      # big gamut Y/Cb/Cr, bg-sYCC
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
        ret = _lib.parse(filename.encode(encoding='utf-8'), get_rawdct)
        img.size = ret['size']
        img._color_space = ret['color_space']
        img.data = ret['data']
        img.isdct = get_rawdct
        return img

    def setdata(self, data):
        self.data = data

    def save(self, filename, quality=75):
        if self.isdct:
            raise NotImplementedError()
        else :
            import array
            rgb_data = b''
            for rgb in self.data:
                rgb_data += array.array('B', rgb)
            ok = _lib.save_from_rgb(
                    filename.encode(encoding='utf-8'),
                    self.size[0], self.size[1], quality,
                    rgb_data
                )

if __name__ == "__main__":
    filename = "lfs.jpg"
    img = JPEGImage.open(filename)

    # # 利用PIL对比得到的数据是否有误
    # from PIL import Image
    # img2 = Image.open(filename)
    # l = list(img2.getdata())
    # for x in range(len(l)):
    #     assert img.data[x] == l[x], "Err"

    # 修改后重新存储rgb数据
    newdata = []
    for rgb in img.data:
        newdata.append((rgb[0],rgb[1],0))
    img.setdata(newdata)
    img.save('oo.jpg')

