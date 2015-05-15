#!/usr/bin/env python
#encoding=utf-8

import os
import ctypes
from copy import deepcopy

from .constants import (
    JPEG_LIB_VERSION, JPOOL_IMAGE, DCTSIZE2,
    DESCRIPTIONS_OF_J_COLOR_SAPCE,
)
from .structs import (
    ERROR_EXIT_FUNC,
    JSAMPLE, JSAMPARRAY, JBLOCK, J_COLOR_SPACE,
    jpeg_error_mgr,
    j_common_ptr, jpeg_decompress_struct, jpeg_compress_struct,
    jpeg_component_info, jvirt_barray_ptr
)
from .functions import jfuncs, cfopen, cfclose, jround_up

__all__ = [
    'JPEGImage',
]


def py_error_exit(cinfo):
    print('in calling error_exit')
error_exit = ERROR_EXIT_FUNC(py_error_exit)


class JPEGImage(object):

    MODE_DCT = 1
    MODE_RGB = 2

    @classmethod
    def open(cls, filepath, mode=MODE_DCT):
        f = open(filepath, 'rb')
        contents = f.read()
        cinfo = jpeg_decompress_struct()
        jerr = jpeg_error_mgr()
        cinfo.err = jfuncs['jStdError'](ctypes.byref(jerr))
        jerr.error_exit = error_exit
        jfuncs['jCreaDecompress'](
            ctypes.byref(cinfo),
            JPEG_LIB_VERSION, ctypes.sizeof(jpeg_decompress_struct)
        )
        ## use `jMemSrc` instead
        # infile = cfopen(b'lfs.jpg', b'rb')
        # jfuncs['jStdSrc'](ctypes.byref(cinfo), infile)
        jfuncs['jMemSrc'](ctypes.byref(cinfo), contents, len(contents))
        jfuncs['jReadHeader'](ctypes.byref(cinfo), True)

        obj = cls()
        obj.filename = os.path.basename(filepath)
        obj.filepath = os.path.abspath(filepath)

        obj.size = (cinfo.image_width, cinfo.image_height)
        obj._color_space = cinfo.jpeg_color_space
        obj.progressive_mode = bool(cinfo.progressive_mode)
        obj.optimize_coding = False

        # 颜色分量信息
        # 把指针转化为指向cinfo.num_components个jpeg_component_info结构体的指针
        obj.comp_infos = []
        ComponentInfoArrayType = ctypes.POINTER(
            cinfo.num_components * jpeg_component_info
        )
        comps = ctypes.cast(cinfo.comp_info, ComponentInfoArrayType)
        for comp in comps.contents:
            comp_info = {}
            for fieldname in jpeg_component_info.fields_needed:
                comp_info[fieldname] = comp.__getattribute__(fieldname)
            obj.comp_infos.append(comp_info)

        # 量化表
        obj.quant_tbls = []
        for quant_tbl_ptr in cinfo.quant_tbl_ptrs:
            tbl = {}
            try:
                tbl['quantval'] = [_ for _ in quant_tbl_ptr.contents.quantval]
            except ValueError:
                pass
            else:
                obj.quant_tbls.append(tbl)

        # 哈夫曼表
        obj.dc_huff_tbl = []
        for huff_tbl_ptr in cinfo.dc_huff_tbl_ptrs:
            tbl = {}
            try:
                tbl['bits'] = [_ for _ in huff_tbl_ptr.contents.bits]
                tbl['huffval'] = [_ for _ in huff_tbl_ptr.contents.huffval]
            except ValueError:
                pass
            else:
                obj.dc_huff_tbl.append(tbl)
        obj.ac_huff_tbl = []
        for huff_tbl_ptr in cinfo.ac_huff_tbl_ptrs:
            tbl = {}
            try:
                tbl['bits'] = [_ for _ in huff_tbl_ptr.contents.bits]
                tbl['huffval'] = [_ for _ in huff_tbl_ptr.contents.huffval]
            except ValueError:
                pass
            else:
                obj.ac_huff_tbl.append(tbl)

        # DCT/RGB data
        obj.mode = mode
        if mode == JPEGImage.MODE_DCT:
            obj.data = []
            coef_arrays = jfuncs['jReadCoefs'](ctypes.byref(cinfo))
            CoefArraysType = ctypes.POINTER(
                jvirt_barray_ptr * cinfo.num_components
            )
            coef_arrays = ctypes.cast(coef_arrays, CoefArraysType)
            for i, coef_array in enumerate(coef_arrays.contents):
                comp = obj.comp_infos[i]
                component_blocks = []
                for nrow in range(comp['height_in_blocks']):
                    block_row = cinfo.mem.contents.access_virt_barray(
                        ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                        coef_array, nrow, 1, int(False)
                    )
                    block_row = ctypes.cast(
                        block_row.contents, ctypes.POINTER(
                            JBLOCK * comp['width_in_blocks']
                        )
                    )
                    for block in block_row.contents:
                        component_blocks.append(list(block))
                obj.data.append(component_blocks)
        elif mode == JPEGImage.MODE_RGB:
            obj.data = []
            jfuncs['jStrtDecompress'](ctypes.byref(cinfo))
            row_stride = cinfo.output_width * cinfo.output_components
            buf = cinfo.mem.contents.alloc_sarray(
                ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                JPOOL_IMAGE, row_stride, 1
            )
            while cinfo.output_scanline < cinfo.output_height:
                jfuncs['jReadScanlines'](
                    ctypes.byref(cinfo), buf, 1
                )
                tbuf = ctypes.cast(
                    buf.contents,
                    ctypes.POINTER(JSAMPLE*row_stride)
                )
                for ncol in range(0, row_stride, 3):
                    rgb = [_ for _ in tbuf.contents[ncol:ncol+3]]
                    obj.data.append(rgb)

        jfuncs['jFinDecompress'](ctypes.byref(cinfo))
        jfuncs['jDestDecompress'](ctypes.byref(cinfo))
        return obj

    def copy(self):
        return deepcopy(self)

    def __setcinfo(self, cinfo):
        cinfo.image_width, cinfo.image_height = self.size
        if self.mode == JPEGImage.MODE_RGB:
            cinfo.input_components = 3  # 3 for R,G,B
            cinfo.in_color_space = J_COLOR_SPACE.JCS_RGB
            jfuncs['jSetDefaults'](ctypes.byref(cinfo))
            jfuncs['jSetQuality'](ctypes.byref(cinfo), quality, int(True))

            jfuncs['jStrtCompress'](ctypes.byref(cinfo), int(True))

            bdata = b''.join(
                bytes(rgb) for rgb in self.data
            )
            row_stride = cinfo.image_width * 3
            rowcnt = 0
            while rowcnt < cinfo.image_height:
                row = ctypes.create_string_buffer(
                    bdata[rowcnt*row_stride:(rowcnt+1)*row_stride]
                )
                row_ptr = ctypes.cast(
                    ctypes.pointer(ctypes.pointer(row)),
                    JSAMPARRAY
                )
                jfuncs['jWrtScanlines'](ctypes.byref(cinfo), row_ptr, 1)
                rowcnt += 1

        elif self.mode == JPEGImage.MODE_DCT:
            cinfo.input_components = 3  # 3 for Y,Cr,Cb
            cinfo.jpeg_color_space = self._color_space

            cinfo.in_color_space = J_COLOR_SPACE.JCS_YCbCr
            cinfo.optimize_coding = int(self.optimize_coding)

            jfuncs['jSetDefaults'](ctypes.byref(cinfo))

            cinfo.in_color_space = 3
            cinfo.num_components = 3
            cinfo.jpeg_width, cinfo.jpeg_height = self.size

            if self.progressive_mode:
                jfuncs['jSimProgress'](ctypes.byref(cinfo))

            min_h, min_v = 16, 16
            ComponentInfoArrayType = ctypes.POINTER(
                cinfo.num_components * jpeg_component_info
            )
            comp_infos = ctypes.cast(cinfo.comp_info, ComponentInfoArrayType)

            # set params to alloc coef arrays
            coef_arrays = ctypes.cast(
                cinfo.mem.contents.alloc_small(
                    ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                    JPOOL_IMAGE,
                    ctypes.sizeof(jvirt_barray_ptr) * cinfo.num_components
                ),
                ctypes.POINTER(jvirt_barray_ptr * cinfo.num_components)
            )

            # `min_DCT_h(v)_scaled_size` must be filled
            for i, comp_info in enumerate(comp_infos.contents):
                ori = self.comp_infos[i]
                comp_info.component_index = ori['component_index']
                comp_info.component_id = ori['component_id']
                comp_info.quant_tbl_no = ori['quant_tbl_no']
                comp_info.ac_tbl_no = ori['ac_tbl_no']
                comp_info.dc_tbl_no = ori['dc_tbl_no']

                comp_info.DCT_h_scaled_size = ori['DCT_h_scaled_size']
                comp_info.DCT_v_scaled_size = ori['DCT_v_scaled_size']
                comp_info.h_samp_factor = ori['h_samp_factor']
                comp_info.v_samp_factor = ori['v_samp_factor']
                comp_info.width_in_blocks = ori['width_in_blocks']
                comp_info.height_in_blocks = ori['height_in_blocks']

                # allocate the space of coef arrays
                coef_array = cinfo.mem.contents.request_virt_barray(
                    ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                    JPOOL_IMAGE, int(True),
                    jround_up(comp_info.width_in_blocks, comp_info.h_samp_factor),
                    jround_up(comp_info.height_in_blocks, comp_info.v_samp_factor),
                    comp_info.v_samp_factor
                )
                coef_arrays.contents.__setitem__(i, coef_array)
                min_h = min(min_h, ori['DCT_h_scaled_size'])
                min_v = min(min_v, ori['DCT_v_scaled_size'])
            cinfo.min_DCT_h_scaled_size = min_h
            cinfo.min_DCT_v_scaled_size = min_v

            # realize virtual block arrays
            jfuncs['jWrtCoefs'](
                ctypes.byref(cinfo),
                ctypes.cast(coef_arrays, ctypes.POINTER(jvirt_barray_ptr))
            )

            # populate the array with the DCT coefficients
            for i, (comp_info, coef_array) in enumerate(
                zip(self.comp_infos, coef_arrays.contents)
            ):

                for nrow in range(comp_info['height_in_blocks']):

                    block_row = cinfo.mem.contents.access_virt_barray(
                        ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                        coef_array, nrow, 1, int(True)
                    )
                    block_row = ctypes.cast(
                        block_row.contents, ctypes.POINTER(
                            JBLOCK * comp_info['width_in_blocks']
                        )
                    )
                    for ncol in range(comp_info['width_in_blocks']):
                        block = JBLOCK()
                        for j in range(DCTSIZE2):
                            block[j] = \
                                self.data[i][nrow*comp_info['width_in_blocks']+ncol][j]
                        block_row.contents.__setitem__(
                            ncol, block
                        )

            # get the quantization tables
            for i, quant_table in enumerate(self.quant_tbls):
                # type of quant_table is c_ushort_Array_64
                for j in range(DCTSIZE2):
                    cinfo.quant_tbl_ptrs[i].contents.quantval[j] = \
                        self.quant_tbls[i]['quantval'][j]

    def save(self, filepath, quality=75):
        cinfo = jpeg_compress_struct()
        jerr = jpeg_error_mgr()
        cinfo.err = jfuncs['jStdError'](ctypes.byref(jerr))
        jerr.error_exit = error_exit
        jfuncs['jCreaCompress'](
            ctypes.byref(cinfo),
            JPEG_LIB_VERSION, ctypes.sizeof(jpeg_compress_struct)
        )
        fp = cfopen(filepath.encode(), b'wb')
        jfuncs['jStdDest'](ctypes.byref(cinfo), fp)
        self.__setcinfo(cinfo)
        # release resources
        jfuncs['jFinCompress'](ctypes.byref(cinfo))
        jfuncs['jDestCompress'](ctypes.byref(cinfo))
        cfclose(fp)

    def save2Bytes(self, quality=75):
        cinfo = jpeg_compress_struct()
        jerr = jpeg_error_mgr()
        cinfo.err = jfuncs['jStdError'](ctypes.byref(jerr))
        jerr.error_exit = error_exit
        jfuncs['jCreaCompress'](
            ctypes.byref(cinfo),
            JPEG_LIB_VERSION, ctypes.sizeof(jpeg_compress_struct)
        )
        outbuffer = ctypes.POINTER(ctypes.c_char)()
        outsize = ctypes.c_long()
        jfuncs['jMemDest'](
            ctypes.byref(cinfo),
            ctypes.byref(outbuffer),
            ctypes.byref(outsize)
        )
        self.__setcinfo(cinfo)
        # release resources
        jfuncs['jFinCompress'](ctypes.byref(cinfo))
        jfuncs['jDestCompress'](ctypes.byref(cinfo))

        outbuffer = ctypes.cast(
            outbuffer,
            ctypes.POINTER(ctypes.c_char * outsize.value)
        )
        buf = b''.join(outbuffer.contents)
        return buf

    def color_space_description(self):
        return DESCRIPTIONS_OF_J_COLOR_SAPCE[self._color_space]
