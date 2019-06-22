#!/usr/bin/env python
#encoding=utf-8

DCTSIZE = 8  # The basic DCT block is 8x8 coefficients
DCTSIZE2 = 64  # DCTSIZE squared; num of elements in a block
NUM_QUANT_TBLS = 4  # Quantization tables are numbered 0..3
NUM_HUFF_TBLS = 4   # Huffman tables are numbered 0..3
NUM_ARITH_TBLS = 16  # Arith-coding tables are numbered 0..15
MAX_COMPS_IN_SCAN = 4  # JPEG limit on num of components in one scan
MAX_SAMP_FACTOR = 4  # JPEG limit on sampling factors
C_MAX_BLOCKS_IN_MCU = 10  # compressor's limit on blocks per MCU
D_MAX_BLOCKS_IN_MCU = 10  # decompressor's limit on blocks per MCU
JPEG_LIB_VERSION = 90  # Compatibility version 9.0
JPOOL_IMAGE = 1

from .structs import J_COLOR_SPACE

DESCRIPTIONS_OF_J_COLOR_SAPCE = {
    J_COLOR_SPACE.JCS_UNKNOWN: 'error/unspecified',
    J_COLOR_SPACE.JCS_GRAYSCALE: 'monochrome',
    J_COLOR_SPACE.JCS_RGB: 'red/green/blue, standard RGB (sRGB)',
    J_COLOR_SPACE.JCS_YCbCr: 'Y/Cb/Cr (also known as YUV), standard YCC',
    J_COLOR_SPACE.JCS_CMYK: 'C/M/Y/K',
    J_COLOR_SPACE.JCS_YCCK: 'Y/Cb/Cr/K',
    J_COLOR_SPACE.JCS_BG_RGB: 'big gamut red/green/blue, bg-sRGB',
    J_COLOR_SPACE.JCS_BG_YCC: 'big gamut Y/Cb/Cr, bg-sYCC',
}
