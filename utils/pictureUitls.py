#!/usr/bin/env python
#encoding=utf-8

from PIL import Image
from PIL import ImageEnhance

DEBUG = False


def make_highlight(image):
    enhancer = ImageEnhance.Contrast(image)
    t = enhancer.enhance(0.2)
    enhancer = ImageEnhance.Brightness(t)
    t = enhancer.enhance(1.35)
    return t


def make_difference(image, restruct_image, highlight_img):
    width, height = image.size
    difference_img = Image.new("RGB", image.size)
    d0 = image.load()
    d1 = restruct_image.load()
    cnt = 0
    for h in range(height):
        for w in range(width):
            oriVals = highlight_img.getpixel((w, h))
            if d0[w, h] != d1[w, h]:
                newVals = [255, ]
                newVals.extend(map(lambda x: x//3, oriVals[1:]))
                difference_img.putpixel((w, h), tuple(newVals))
                if DEBUG:
                    cnt += 1
                    print(
                        'diff @ (%4d, %4d): %s <-> %s'
                        % (w, h, d0[w, h], d1[w, h])
                    )
            else:
                difference_img.putpixel(
                    (w, h),
                    oriVals
                )
    if DEBUG:
        total_size = width * height
        print(
            'diff: %d, total: %d, diff precent:%f%%'
            % (cnt, total_size, cnt/total_size)
        )
    return difference_img


def compare_images(filename, compare_filename, diff_filename=None):
    image = Image.open(filename)
    restruct_image = Image.open(compare_filename)

    highlight_img = make_highlight(image)
    difference_img = make_difference(image, restruct_image, highlight_img)
    if not diff_filename:
        difference_img.show()  # 直接显示图片
        return difference_img
    else:
        difference_img.save(diff_filename, quality=90)


if __name__ == '__main__':
    compare_images('sos_ori.jpg', 'sos_emb.jpg', 'sos_diff.jpg')
