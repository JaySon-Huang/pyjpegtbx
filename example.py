#! /usr/bin/env python3
#encoding=utf-8

from __future__ import print_function

from pyjpegtbx import JPEGImage

# 第二个参数为 JPEGImage.MODE_RGB, 表示读取RGB数据
img = JPEGImage.open('test/pics/lfs.jpg', JPEGImage.MODE_RGB)
newdata = []
# img.data中存储着RGB数据
# for rgb in img.data:
#     newdata.append((0, rgb[1], rgb[2]))
# img.data = newdata
# img.save('tmp0.jpg')

# 第二个参数默认为True, 表示读取DCT数据
img = JPEGImage.open('test/pics/lfs.jpg', JPEGImage.MODE_DCT)
# 查看颜色分量信息
print('component infos:', img.comp_infos)
# 量化表
print('quantitative tables:', img.quant_tbls)
# 哈夫曼表
print('huffman tables:')
print(img.ac_huff_tbls)
print(img.dc_huff_tbls)
# 文件名
print('filename:', img.filename)
# (width, height)
print('size:', img.size)
# DCT数据信息
# print(img.data)
# 把高频DCT系数设置为0
for comp in img.data:
    for coef in comp:
        for i in range(32, 64):
            coef[i] = 0
img.save('tmp1.jpg')

# 获取exif信息
# exif_infos = img.get_exif()
# print(exif_infos)
