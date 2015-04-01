#/usr/bin/env python3

import ctypes
_lib = ctypes.CDLL("./libjpegtbx.so")

_lib.parse.restype = ctypes.py_object
_lib.parse.argtypes = [ctypes.c_char_p, ctypes.c_int]

_lib.save_from_rgb.restype = ctypes.c_int
_lib.save_from_rgb.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]

_lib.save_from_dct.restype = ctypes.c_int
_lib.save_from_dct.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, # filename
    ctypes.py_object, # self.data, 
    ctypes.c_int, ctypes.c_int, ctypes.c_int, # self.size, self._color_space
    ctypes.c_int, ctypes.c_int, # self.progressive_mode, self.optimize_coding
    ctypes.py_object, # self.comp_infos
    ctypes.py_object, # self.quant_tbls
    ctypes.py_object, # self.ac_huff_tables
    ctypes.py_object, # self.dc_huff_tables
]

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
    # huff_tbl_ptrs => {'dc':[[],...,[],[]], 'ac':[[],...,[],[]]}
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    @classmethod
    def open(cls, filename, get_rawdct=False):
        img = cls(filename)
        ret = _lib.parse(filename.encode(encoding='utf-8'), get_rawdct)

        # for debug
        for key, val in ret.items():
            #if key not in  ('data', 'ac_huff_tables', 'dc_huff_tables', 'quant_tbls') :
            #    print(key,val)
            if key == "data":
                print(key, len(val))

        img.isdct = get_rawdct

        img.size = ret['size']
        img._color_space = ret['color_space']
        img.progressive_mode = ret['progressive_mode']

        img.data = ret['data']
        img.comp_infos = ret['comp_infos']
        img.quant_tbls = ret['quant_tbls']
        img.ac_huff_tables = ret['ac_huff_tables']
        img.dc_huff_tables = ret['dc_huff_tables']

        img.optimize_coding = False
        return img

    def setdata(self, data):
        self.data = data

    def save(self, filename, quality=75):
        if self.isdct:
            _lib.save_from_dct(
                filename.encode(encoding='utf-8'),
                self.filename.encode(encoding='utf-8'),
                self.data, 
                self.size[0], self.size[1], self._color_space,
                self.progressive_mode, self.optimize_coding,
                self.comp_infos,
                self.quant_tbls,
                self.ac_huff_tables,
                self.dc_huff_tables
            )
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
    # img = JPEGImage.open(filename)

    # # 利用PIL对比得到的数据是否有误
    # from PIL import Image
    # img2 = Image.open(filename)
    # l = list(img2.getdata())
    # for x in range(len(l)):
    #     assert img.data[x] == l[x], "Err"

    # # 修改后重新存储rgb数据
    # newdata = []
    # for rgb in img.data:
    #     newdata.append((rgb[0],rgb[1],0))
    # img.setdata(newdata)
    # img.save('oo.jpg')

    # 修改后重新存储dct数据
    # img = JPEGImage.open(filename, get_rawdct=True)
    # for key,val in img.data.items():
    #     print(key,len(val))
    #     for coef in val:
    #         for i in range(48,64):
    #             coef[i] = 0
    # img.save('oo.jpg')

    files = [ "zhou.jpg", "zhou_cut.jpg", "lfs.jpg", "tic.jpg",]
    files = ["tic.jpg",] # Bad Case
    for filename in files:
        img = JPEGImage.open(filename, get_rawdct=True)
        for key,val in img.data.items():
            print(key, val[0])
            for coef in val:
                for i in range(48, 64):
                    coef[i] = 0
        img.save(filename.split(".")[0]+"_saved.jpg")
