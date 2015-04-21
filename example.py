#! /usr/bin/env python3
#encoding=utf-8

from pyjpegtbx import JPEGImage

# 第二个参数为False, 表示读取RGB数据
img = JPEGImage('lfs.jpg', False)
newdata = []
# img.data中存储着RGB数据
for rgb in img.data:
    newdata.append((0, rgb[1], rgb[2]))
img.data = newdata
img.save('tmp0.jpg')

# 第二个参数默认为True, 表示读取DCT数据
img = JPEGImage('lfs.jpg')
# 查看颜色分量信息
print(img.comp_infos)
# 量化表
print(img.quant_tbls)
# 哈夫曼表
print(img.ac_huff_tables)
print(img.dc_huff_tables)
# 文件名
print(img.filename)
# (width, height)
print(img.size)
# DCT数据信息
# print(img.data)
# 把高频DCT系数设置为0
for key, val in img.data.items():
    for coef in val:
        for i in range(32, 64):
            coef[i] = 0
img.save('tmp1.jpg')
